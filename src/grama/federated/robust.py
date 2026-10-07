"""Baseline aggregation rules to compare the latent density defence against.

  fedavg        sample-weighted mean (McMahan et al., 2017), no defence
  median        coordinate-wise median (Yin et al., 2018)
  trimmed_mean  coordinate-wise mean after dropping the largest and smallest
                values of each coordinate (Yin et al., 2018)
  krum          Multi-Krum (Blanchard et al., 2017): keep the updates closest
                to their neighbours, average those
  norm_clip     clip every update to the round's median update norm, then
                average (norm bounding, as in Sun et al., 2019, with an
                adaptive bound)
  flame         FLAME (Nguyen et al., USENIX Security 2022): HDBSCAN on the
                pairwise cosine distances of the updates keeps the majority
                cluster, those updates are clipped to the median norm and
                averaged, and Gaussian noise of scale lambda * median norm is
                added. The closest prior defence to the latent density one.

  foolsgold     FoolsGold (Fung et al., RAID 2020): clients whose summed updates point
                the same way as another client's get less weight (sybil resistance)
  deepsight     DeepSight (Rieger et al., NDSS 2022), simplified: update clusters
                are accepted or dropped by how many output neurons carry the update's
                energy (threshold exceedings), then clipped. Omits the DDifs measure,
                which needs forward passes on random inputs
  freqfed       FreqFed (Fereidooni et al., NDSS 2024): the low-frequency part of the
                discrete cosine transform of each update is clustered with HDBSCAN,
                the majority cluster is kept, clipped and averaged

All of them return the same AggregationResult as LatentDensityAggregator,
so the server and the experiments treat every rule the same way.
"""
from __future__ import annotations

import numpy as np
import torch
from sklearn.cluster import HDBSCAN

from grama.federated.aggregator import (
    AggregationResult,
    Aggregator,
    LatentDensityAggregator,
    flatten_delta,
    unflatten_delta,
)
from grama.federated.client import ClientUpdate


def _stack(updates: list[ClientUpdate]) -> torch.Tensor:
    return torch.stack([flatten_delta(u.delta_w) for u in updates])  # (K, P)


class FedAvgAggregator(Aggregator):
    name = "fedavg"

    def aggregate(self, updates, param_shapes):
        n = torch.tensor([u.num_samples for u in updates], dtype=torch.float32)
        w = n / n.sum()
        delta = (w.unsqueeze(1) * _stack(updates)).sum(0)
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: float(wi) for u, wi in zip(updates, w)},
            cluster_labels={}, benign_cluster_id=None,
        )


class MedianAggregator(Aggregator):
    name = "median"

    def aggregate(self, updates, param_shapes):
        delta = _stack(updates).median(dim=0).values
        k = len(updates)
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: 1.0 / k for u in updates},
            cluster_labels={}, benign_cluster_id=None,
        )


class TrimmedMeanAggregator(Aggregator):
    name = "trimmed_mean"

    def __init__(self, trim_ratio: float = 0.2):
        self.trim_ratio = trim_ratio

    def aggregate(self, updates, param_shapes):
        flat = _stack(updates)
        k = len(updates)
        b = min(int(self.trim_ratio * k), (k - 1) // 2)
        sorted_vals = flat.sort(dim=0).values
        delta = sorted_vals[b: k - b].mean(dim=0)
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: 1.0 / k for u in updates},
            cluster_labels={}, benign_cluster_id=None,
        )


class KrumAggregator(Aggregator):
    """Multi-Krum. f = number of attackers it is built to tolerate (needs K >= 2f + 3)."""

    name = "krum"
    detects_clients = True

    def __init__(self, assumed_fraction: float = 0.4, multi: bool = True):
        self.assumed_fraction = assumed_fraction
        self.multi = multi

    def aggregate(self, updates, param_shapes):
        flat = _stack(updates)
        k = len(updates)
        f = max(0, min(int(self.assumed_fraction * k), (k - 3) // 2))
        dist = torch.cdist(flat, flat).pow(2)
        nearest = max(1, k - f - 2)
        # Score: summed squared distance to the nearest k - f - 2 others (excluding itself).
        scores = dist.sort(dim=1).values[:, 1: nearest + 1].sum(dim=1)
        m = k - f if self.multi else 1
        chosen = set(scores.argsort()[:m].tolist())
        delta = flat[sorted(chosen)].mean(dim=0)
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: (1.0 / m if i in chosen else 0.0) for i, u in enumerate(updates)},
            cluster_labels={}, benign_cluster_id=None,
        )


def _clip_to_median(flat: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Scale each row down to at most the median row norm. Returns (clipped, median norm)."""
    norms = flat.norm(dim=1)
    bound = norms.median()
    scale = torch.clamp(bound / norms.clamp(min=1e-12), max=1.0)
    return flat * scale.unsqueeze(1), bound


class NormClipAggregator(Aggregator):
    name = "norm_clip"

    def aggregate(self, updates, param_shapes):
        clipped, _ = _clip_to_median(_stack(updates))
        k = len(updates)
        return AggregationResult(
            global_delta=unflatten_delta(clipped.mean(dim=0), param_shapes),
            trust_weights={u.client_id: 1.0 / k for u in updates},
            cluster_labels={}, benign_cluster_id=None,
        )


class FlameAggregator(Aggregator):
    """FLAME: cosine-distance HDBSCAN filtering, median-norm clipping, adaptive noise."""

    name = "flame"
    detects_clients = True

    def __init__(self, noise_lambda: float = 0.001, seed: int = 0):
        self.noise_lambda = noise_lambda
        self.generator = torch.Generator().manual_seed(seed)

    def aggregate(self, updates, param_shapes):
        flat = _stack(updates)
        k = len(updates)
        unit = flat / flat.norm(dim=1, keepdim=True).clamp(min=1e-12)
        dist = (1.0 - unit @ unit.T).clamp(min=0.0).double().numpy()
        np.fill_diagonal(dist, 0.0)
        labels = HDBSCAN(
            metric="precomputed", min_cluster_size=k // 2 + 1, min_samples=1, allow_single_cluster=True,
        ).fit_predict(dist)
        non_noise = labels[labels != -1]
        if len(non_noise):
            values, counts = np.unique(non_noise, return_counts=True)
            keep = labels == values[np.argmax(counts)]
        else:
            keep = np.ones(k, dtype=bool)  # no majority found: FLAME falls back to everyone
        clipped, bound = _clip_to_median(flat)
        kept = torch.from_numpy(keep)
        delta = clipped[kept].mean(dim=0)
        delta = delta + torch.randn(delta.shape, generator=self.generator) * (self.noise_lambda * float(bound))
        m = int(keep.sum())
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: (1.0 / m if keep[i] else 0.0) for i, u in enumerate(updates)},
            cluster_labels={u.client_id: int(labels[i]) for i, u in enumerate(updates)},
            benign_cluster_id=None,
        )


class FoolsGoldAggregator(Aggregator):
    """FoolsGold. Keeps each client's summed update over the rounds it took part in; the more a client's
    history points the same way as another's, the less weight it gets. Colluders with identical
    updates get weight 0."""

    name = "foolsgold"
    detects_clients = True

    def __init__(self, confidence: float = 1.0):
        self.confidence = confidence
        self.history: dict[int, torch.Tensor] = {}

    def aggregate(self, updates, param_shapes):
        flat = _stack(updates)
        k = len(updates)
        for i, u in enumerate(updates):
            self.history[u.client_id] = self.history.get(u.client_id, torch.zeros_like(flat[i])) + flat[i]
        hist = torch.stack([self.history[u.client_id] for u in updates])
        unit = hist / hist.norm(dim=1, keepdim=True).clamp(min=1e-12)
        cs = unit @ unit.T - torch.eye(k)
        max_cs = cs.max(dim=1).values
        # Pardoning: a client that is less similar than its neighbour keeps its weight.
        for i in range(k):
            for j in range(k):
                if i != j and max_cs[j] > max_cs[i]:
                    cs[i, j] = cs[i, j] * max_cs[i] / max_cs[j]
        wv = (1.0 - cs.max(dim=1).values).clamp(0.0, 1.0)
        if wv.max() > 0:
            wv = wv / wv.max()
        wv = torch.where(wv >= 1.0, torch.full_like(wv, 0.99), wv)
        wv = self.confidence * (torch.log(wv / (1.0 - wv)) + 0.5)    # -inf where wv is 0, cleaned below
        wv = torch.nan_to_num(wv, nan=0.0, neginf=0.0, posinf=1.0).clamp(0.0, 1.0)
        total = float(wv.sum())
        if total <= 0.0:
            weights = torch.zeros(k)
            delta = torch.zeros(flat.shape[1])
        else:
            weights = wv / total
            delta = (weights.unsqueeze(1) * flat).sum(0)
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: float(w) for u, w in zip(updates, weights)},
            cluster_labels={}, benign_cluster_id=None,
        )


class DeepSightAggregator(Aggregator):
    """DeepSight without DDifs. Per update: the share of its energy on each output neuron (NEUPs) and
    the number of neurons above a threshold (threshold exceedings, TE). Few exceedings mean the update
    was trained on one label, which is how poisoned updates look. Updates are clustered on cosine
    distance and NEUP distance; a cluster is dropped when a third or more of it looks suspicious."""

    name = "deepsight"
    detects_clients = True

    def __init__(self, suspicious_share: float = 1.0 / 3.0, noise_lambda: float = 0.0, seed: int = 0):
        self.suspicious_share = suspicious_share
        self.noise_lambda = noise_lambda
        self.generator = torch.Generator().manual_seed(seed)

    def aggregate(self, updates, param_shapes):
        flat = _stack(updates)
        k = len(updates)
        names = list(updates[0].delta_w)[-2:]          # output layer: weights and bias
        neups = []
        for u in updates:
            w, b = u.delta_w[names[0]].float(), u.delta_w[names[1]].float()
            energy = w.reshape(w.shape[0], -1).pow(2).sum(1) + b.reshape(-1).pow(2)
            neups.append(energy / energy.sum().clamp(min=1e-12))
        neup = torch.stack(neups)                       # (K, classes)
        threshold = (neup.max(dim=1, keepdim=True).values / 2).clamp(min=0.01)
        te = (neup > threshold).sum(dim=1).float()
        suspicious = (te <= te.median() / 2).numpy()

        unit = flat / flat.norm(dim=1, keepdim=True).clamp(min=1e-12)
        d_cos = (1.0 - unit @ unit.T).clamp(min=0.0)
        d_neup = torch.cdist(neup, neup)
        dist = (d_cos / d_cos.max().clamp(min=1e-12) + d_neup / d_neup.max().clamp(min=1e-12)) / 2
        dist = dist.double().numpy()
        np.fill_diagonal(dist, 0.0)
        labels = HDBSCAN(metric="precomputed", min_cluster_size=2, min_samples=1,
                         allow_single_cluster=False).fit_predict(dist)
        keep = np.zeros(k, dtype=bool)
        for lbl in set(labels.tolist()):
            members = labels == lbl
            if lbl == -1:                               # noise points are judged one by one
                keep |= members & ~suspicious
            elif suspicious[members].mean() < self.suspicious_share:
                keep |= members
        if not keep.any():
            keep = ~suspicious if (~suspicious).any() else np.ones(k, dtype=bool)
        clipped, bound = _clip_to_median(flat)
        delta = clipped[torch.from_numpy(keep)].mean(dim=0)
        if self.noise_lambda:
            delta = delta + torch.randn(delta.shape, generator=self.generator) * (self.noise_lambda * float(bound))
        m = int(keep.sum())
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: (1.0 / m if keep[i] else 0.0) for i, u in enumerate(updates)},
            cluster_labels={u.client_id: int(labels[i]) for i, u in enumerate(updates)},
            benign_cluster_id=None,
        )


class FreqFedAggregator(Aggregator):
    """FreqFed: HDBSCAN on the low-frequency discrete cosine transform of each update."""

    name = "freqfed"
    detects_clients = True

    def __init__(self, low_fraction: float = 0.05, noise_lambda: float = 0.0, seed: int = 0):
        self.low_fraction = low_fraction
        self.noise_lambda = noise_lambda
        self.generator = torch.Generator().manual_seed(seed)

    def aggregate(self, updates, param_shapes):
        from scipy.fft import dct

        flat = _stack(updates)
        k = len(updates)
        spectrum = dct(flat.double().numpy(), norm="ortho", axis=1)
        low = torch.from_numpy(spectrum[:, : max(2, int(self.low_fraction * spectrum.shape[1]))]).float()
        unit = low / low.norm(dim=1, keepdim=True).clamp(min=1e-12)
        dist = (1.0 - unit @ unit.T).clamp(min=0.0).double().numpy()
        np.fill_diagonal(dist, 0.0)
        labels = HDBSCAN(metric="precomputed", min_cluster_size=k // 2 + 1, min_samples=1,
                         allow_single_cluster=True).fit_predict(dist)
        non_noise = labels[labels != -1]
        if len(non_noise):
            values, counts = np.unique(non_noise, return_counts=True)
            keep = labels == values[np.argmax(counts)]
        else:
            keep = np.ones(k, dtype=bool)
        clipped, bound = _clip_to_median(flat)
        delta = clipped[torch.from_numpy(keep)].mean(dim=0)
        if self.noise_lambda:
            delta = delta + torch.randn(delta.shape, generator=self.generator) * (self.noise_lambda * float(bound))
        m = int(keep.sum())
        return AggregationResult(
            global_delta=unflatten_delta(delta, param_shapes),
            trust_weights={u.client_id: (1.0 / m if keep[i] else 0.0) for i, u in enumerate(updates)},
            cluster_labels={u.client_id: int(labels[i]) for i, u in enumerate(updates)},
            benign_cluster_id=None,
        )


# Variants of the latent density defence, for the ablation and the sensitivity grid
# (config names are hdbscan_<suffix>). Each entry overrides one or two settings.
HDBSCAN_VARIANTS = {
    "hdbscan_pca": {"latent_method": "pca"},
    "hdbscan_raw": {"latent_method": "raw"},
    "hdbscan_no_rescale": {"normalize": False, "standardize_latent": False},
    "hdbscan_no_normalize": {"normalize": False},
    "hdbscan_no_standardize": {"standardize_latent": False},
    "hdbscan_last_layer": {"phi_input": "last_layer"},
    "hdbscan_eps1": {"cluster_selection_epsilon": 1.0},
    "hdbscan_eps4": {"cluster_selection_epsilon": 4.0},
    "hdbscan_eps8": {"cluster_selection_epsilon": 8.0},
    "hdbscan_mcs2": {"min_cluster_size": 2},
    "hdbscan_mcs5": {"min_cluster_size": 5},
}


AGGREGATORS = ("fedavg", "median", "trimmed_mean", "krum", "norm_clip", "flame", "foolsgold", "deepsight",
               "freqfed", "hdbscan") + tuple(HDBSCAN_VARIANTS)


def make_aggregator(name: str, fed_cfg: dict, device: str = "cpu", seed: int = 0) -> Aggregator:
    """Build an aggregator by name from config/federated.yaml's 'aggregator' section."""
    agg_cfg = fed_cfg.get("aggregator", {})
    if name == "fedavg":
        return FedAvgAggregator()
    if name == "median":
        return MedianAggregator()
    if name == "trimmed_mean":
        return TrimmedMeanAggregator(agg_cfg.get("trim_ratio", 0.2))
    if name == "krum":
        return KrumAggregator(agg_cfg.get("krum_assumed_fraction", 0.4))
    if name == "norm_clip":
        return NormClipAggregator()
    if name == "flame":
        return FlameAggregator(agg_cfg.get("flame_noise_lambda", 0.001), seed=seed)
    if name == "foolsgold":
        return FoolsGoldAggregator(agg_cfg.get("foolsgold_confidence", 1.0))
    if name == "deepsight":
        return DeepSightAggregator(noise_lambda=agg_cfg.get("deepsight_noise_lambda", 0.0), seed=seed)
    if name == "freqfed":
        return FreqFedAggregator(agg_cfg.get("freqfed_low_fraction", 0.05), agg_cfg.get("freqfed_noise_lambda", 0.0), seed=seed)
    if name == "hdbscan" or name in HDBSCAN_VARIANTS:
        params = dict(
            latent_dim=agg_cfg["latent_dim"],
            autoencoder_hidden=agg_cfg["autoencoder_hidden"],
            autoencoder_epochs=agg_cfg["autoencoder_epochs"],
            autoencoder_lr=agg_cfg.get("autoencoder_lr", 1e-3),
            normalize=agg_cfg.get("normalize_updates", True),
            phi_input=agg_cfg.get("phi_input", "all"),
            **agg_cfg["hdbscan"],
        )
        params.update(HDBSCAN_VARIANTS.get(name, {}))
        return LatentDensityAggregator(device=device, **params)
    raise ValueError(f"Unknown aggregator {name!r}; expected one of {AGGREGATORS}")
