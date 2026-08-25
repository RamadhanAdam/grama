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
    return torch.cat([v.flatten() for v in delta_w.values()])


@dataclass
class AggregationResult:
    global_delta: dict[str, torch.Tensor]     # sum_k alpha_k * Δw_k, ready to add to w_global
    trust_weights: dict[int, float]              # client_id -> alpha_k
    cluster_labels: dict[int, int]                # client_id -> HDBSCAN label (-1 = noise/adversarial)
    benign_cluster_id: int | None


class LatentDensityAggregator:
    def __init__(
        self,
        latent_dim: int = 2,
        autoencoder_hidden: int = 32,
        autoencoder_epochs: int = 10,
        min_cluster_size: int = 3,
        min_samples: int = 1,
        cluster_selection_epsilon: float = 0.0,
        device: str = "cpu",
    ):
        self.latent_dim = latent_dim
        self.autoencoder_hidden = autoencoder_hidden
        self.autoencoder_epochs = autoencoder_epochs
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.cluster_selection_epsilon = cluster_selection_epsilon
        self.device = device

    def _train_autoencoder(self, flat_deltas: torch.Tensor) -> DeltaAutoencoder:
        input_dim = flat_deltas.shape[1]
        ae = DeltaAutoencoder(input_dim, self.autoencoder_hidden, self.latent_dim).to(self.device)
        optimizer = torch.optim.Adam(ae.parameters(), lr=1e-3)
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
        flat = torch.stack([flatten_delta(u.delta_w) for u in updates]).to(self.device)  # (K, P)

        # eq. 11: project to latent space.
        ae = self._train_autoencoder(flat)
        with torch.no_grad():
            latent, _ = ae(flat)
        latent_np = latent.cpu().numpy()

        # eq. 12-13: HDBSCAN uses mutual-reachability distance internally to
        # find the most persistent dense cluster(s); sklearn's HDBSCAN
        # implements this directly (Campello et al. 2013).
        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            cluster_selection_epsilon=self.cluster_selection_epsilon,
        )
        labels = clusterer.fit_predict(latent_np)
        probabilities = getattr(clusterer, "probabilities_", np.ones_like(labels, dtype=float))

        cluster_labels = dict(zip(client_ids, labels.tolist()))

        # The benign cluster C_benign = the largest non-noise cluster (most
        # persistent honest-vehicle cluster per eq. 13's stability argument).
        non_noise = labels[labels != -1]
        if len(non_noise) == 0:
            logger.warning("HDBSCAN found no clusters (all noise) — treating all updates as untrusted this round.")
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
            logger.info("Aggregator rejected %d/%d client update(s) as adversarial/noise: %s",
                        len(rejected), len(client_ids), rejected)

        # eq. 15: w_global^(t+1) = w_global^(t) + sum_k alpha_k * Δw_k
        global_delta: dict[str, torch.Tensor] = {name: torch.zeros(shape) for name, shape in param_shapes.items()}
        for u in updates:
            alpha_k = trust_weights[u.client_id]
            if alpha_k == 0.0:
                continue
            for name, tensor in u.delta_w.items():
                global_delta[name] += alpha_k * tensor

        return AggregationResult(
            global_delta=global_delta,
            trust_weights=trust_weights,
            cluster_labels=cluster_labels,
            benign_cluster_id=benign_cluster_id,
        )

    @staticmethod
    def apply(global_state_dict: dict, result: AggregationResult) -> dict:
        return apply_state_dict_delta(global_state_dict, result.global_delta, scale=1.0)
