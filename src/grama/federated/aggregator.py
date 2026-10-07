"""Server-side latent density defense & aggregation (Sec 5.3, eq. 11-15).

Replaces the baseline's heuristic AWI/threshold defense with:
  1. A small autoencoder projecting each client's Δw_k into a low-dim
     latent space u_k = phi(Δw_k)                                (eq. 11)
  2. HDBSCAN clustering over the latent updates, using mutual reachability
     distance to separate dense benign clusters from sparse adversarial
     outliers                                                       (eq. 12-13)
  3. Cluster-membership-probability-weighted trust scores alpha_k, zeroing
     out anything HDBSCAN calls noise                              (eq. 14)
  4. Weighted aggregation into the new global model                (eq. 15)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
from sklearn.cluster import HDBSCAN

from grama.federated.client import ClientUpdate, apply_state_dict_delta
from grama.utils.logging import get_logger

logger = get_logger(__name__)


LATENT_METHODS = ("autoencoder", "pca", "raw")


class DeltaAutoencoder(nn.Module):
    """phi: flattened Δw -> latent u_k ∈ R^d (eq. 11). Trained per-round on the
    incoming batch of client updates (unsupervised, reconstruction loss) so it
    adapts to whatever parameter scale/shape the current model has.
    """

    def __init__(self, input_dim: int, hidden_dim: int, latent_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        u = self.encoder(x)
        recon = self.decoder(u)
        return u, recon


def flatten_delta(delta_w: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.cat([v.flatten().float() for v in delta_w.values()])


def unflatten_delta(flat: torch.Tensor, param_shapes: dict[str, torch.Size]) -> dict[str, torch.Tensor]:
    out, i = {}, 0
    for name, shape in param_shapes.items():
        n = int(torch.Size(shape).numel())
        out[name] = flat[i: i + n].reshape(shape).cpu()
        i += n
    return out


@dataclass
class AggregationResult:
    global_delta: dict[str, torch.Tensor]     # sum_k alpha_k * Δw_k, ready to add to w_global
    trust_weights: dict[int, float]              # client_id -> alpha_k
    cluster_labels: dict[int, int]                # client_id -> HDBSCAN label (-1 = noise/adversarial)
    benign_cluster_id: int | None


class Aggregator:
    """Common interface: aggregate(updates, param_shapes) -> AggregationResult.

    detects_clients says whether the rule names clients it rejects (a zero
    trust weight). Median and trimmed mean work per coordinate and reject
    nobody as a whole, so detection rates are not defined for them.
    """

    name = "base"
    detects_clients = False

    def aggregate(self, updates: list[ClientUpdate], param_shapes: dict[str, torch.Size]) -> "AggregationResult":
        raise NotImplementedError

    @staticmethod
    def apply(global_state_dict: dict, result: "AggregationResult") -> dict:
        return apply_state_dict_delta(global_state_dict, result.global_delta, scale=1.0)


class LatentDensityAggregator(Aggregator):
    name = "hdbscan"
    detects_clients = True

    def __init__(
        self,
        latent_dim: int = 2,
        autoencoder_hidden: int = 32,
        autoencoder_epochs: int = 10,
        min_cluster_size: int = 3,
        min_samples: int = 1,
        cluster_selection_epsilon: float = 2.0,
        autoencoder_lr: float = 1e-3,
        normalize: bool = True,
        allow_single_cluster: bool = True,
        standardize_latent: bool = True,
        phi_input: str = "all",
        latent_method: str = "autoencoder",
        device: str = "cpu",
    ):
        if phi_input not in ("all", "last_layer"):
            raise ValueError(f"phi_input must be 'all' or 'last_layer', got {phi_input!r}")
        if latent_method not in LATENT_METHODS:
            raise ValueError(f"latent_method must be one of {LATENT_METHODS}, got {latent_method!r}")
        self.latent_dim = latent_dim
        self.autoencoder_hidden = autoencoder_hidden
        self.autoencoder_epochs = autoencoder_epochs
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.cluster_selection_epsilon = cluster_selection_epsilon
        self.autoencoder_lr = autoencoder_lr
        self.normalize = normalize
        self.allow_single_cluster = allow_single_cluster
        self.standardize_latent = standardize_latent
        self.phi_input = phi_input
        self.latent_method = latent_method
        self.device = device

    def _latent(self, flat: torch.Tensor) -> np.ndarray:
        """The points HDBSCAN clusters: phi(updates), their PCA projection, or the updates as they are."""
        if self.latent_method == "raw":
            return flat.cpu().numpy()
        if self.latent_method == "pca":
            centred = flat - flat.mean(dim=0, keepdim=True)
            u, s, _ = torch.linalg.svd(centred, full_matrices=False)
            k = max(1, min(self.latent_dim, s.shape[0]))
            return (u[:, :k] * s[:k]).cpu().numpy()
        ae = self._train_autoencoder(flat)
        with torch.no_grad():
            latent, _ = ae(flat)
        return latent.cpu().numpy()

    def _train_autoencoder(self, flat_deltas: torch.Tensor) -> DeltaAutoencoder:
        input_dim = flat_deltas.shape[1]
        ae = DeltaAutoencoder(input_dim, self.autoencoder_hidden, self.latent_dim).to(self.device)
        optimizer = torch.optim.Adam(ae.parameters(), lr=self.autoencoder_lr)
        criterion = nn.MSELoss()

        for _ in range(self.autoencoder_epochs):
            optimizer.zero_grad()
            u, recon = ae(flat_deltas)
            loss = criterion(recon, flat_deltas)
            loss.backward()
            optimizer.step()
        return ae

    def aggregate(self, updates: list[ClientUpdate], param_shapes: dict[str, torch.Size]) -> AggregationResult:
        if not updates:
            raise ValueError("aggregate() called with no client updates")

        client_ids = [u.client_id for u in updates]
        if self.phi_input == "last_layer":
            # Only the final layer's weight and bias (Tolpegin et al., 2020,
            # found label flipping easiest to see there).
            names = list(updates[0].delta_w)[-2:]
            flat = torch.stack([torch.cat([u.delta_w[n].flatten().float() for n in names]) for u in updates])
        else:
            flat = torch.stack([flatten_delta(u.delta_w) for u in updates])  # (K, P)
        flat = flat.to(self.device)
        if self.normalize:
            # Raw Δw entries are ~1e-3 to 1e-5, far too small for phi to learn
            # from in a few steps (it ends up a random projection). Centre the
            # updates across clients, then scale so the median update has norm
            # sqrt(P), i.e. entries of order 1. One scalar for the whole round,
            # so relative sizes are kept and an oversized update still stands out.
            flat = flat - flat.mean(dim=0, keepdim=True)
            median_norm = flat.norm(dim=1).median().clamp(min=1e-12)
            flat = flat * (flat.shape[1] ** 0.5) / median_norm

        # eq. 11: project to latent space. The ablation can swap the autoencoder for PCA or skip the
        # projection and cluster the updates themselves (latent_method).
        latent_np = self._latent(flat)
        if self.standardize_latent:
            # Express the latent points in units of their typical spread (median
            # distance to the median point). phi is refitted every round, so its
            # raw scale means nothing; after this, cluster_selection_epsilon reads
            # as "within that many typical spreads".
            centre = np.median(latent_np, axis=0)
            spread = np.median(np.linalg.norm(latent_np - centre, axis=1))
            latent_np = (latent_np - centre) / max(float(spread), 1e-12)

        # eq. 12-13: HDBSCAN uses mutual-reachability distance internally to
        # find the most persistent dense cluster(s); sklearn's HDBSCAN
        # implements this directly (Campello et al. 2013).
        clusterer = HDBSCAN(
            min_cluster_size=max(2, min(self.min_cluster_size, len(updates))),
            min_samples=self.min_samples,
            cluster_selection_epsilon=self.cluster_selection_epsilon,
            # With no attackers, the honest updates form ONE cluster. sklearn's
            # default refuses a single cluster and calls every point noise,
            # which would reject every update and freeze the global model.
            allow_single_cluster=self.allow_single_cluster,
        )
        labels = clusterer.fit_predict(latent_np)
        probabilities = getattr(clusterer, "probabilities_", np.ones_like(labels, dtype=float))

        cluster_labels = dict(zip(client_ids, labels.tolist()))

        # The benign cluster C_benign = the largest non-noise cluster (most
        # persistent honest-vehicle cluster per eq. 13's stability argument).
        non_noise = labels[labels != -1]
        if len(non_noise) == 0:
            logger.debug("HDBSCAN found no clusters (all noise); the global model is kept as is this round.")
            benign_cluster_id = None
        else:
            values, counts = np.unique(non_noise, return_counts=True)
            benign_cluster_id = int(values[np.argmax(counts)])

        # eq. 14: alpha_k = P_k / sum(P_j in C_benign) if in benign cluster, else 0.
        trust_weights: dict[int, float] = {}
        if benign_cluster_id is not None:
            benign_mask = labels == benign_cluster_id
            benign_prob_sum = probabilities[benign_mask].sum() or 1.0
            for cid, lbl, prob in zip(client_ids, labels, probabilities):
                trust_weights[cid] = float(prob / benign_prob_sum) if lbl == benign_cluster_id else 0.0
        else:
            trust_weights = {cid: 0.0 for cid in client_ids}

        rejected = [cid for cid, w in trust_weights.items() if w == 0.0]
        if rejected:
            logger.debug("Aggregator rejected %d/%d client update(s) as adversarial/noise: %s",
                        len(rejected), len(client_ids), rejected)

        # eq. 15: w_global^(t+1) = w_global^(t) + sum_k alpha_k * Δw_k
        global_delta: dict[str, torch.Tensor] = {name: torch.zeros(shape) for name, shape in param_shapes.items()}
        for u in updates:
            alpha_k = trust_weights[u.client_id]
            if alpha_k == 0.0:
                continue
            for name, tensor in u.delta_w.items():
                global_delta[name] += alpha_k * tensor.float().cpu()

        return AggregationResult(
            global_delta=global_delta,
            trust_weights=trust_weights,
            cluster_labels=cluster_labels,
            benign_cluster_id=benign_cluster_id,
        )
