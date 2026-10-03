"""Baseline aggregation rules to compare the latent density defence against.

  fedavg        sample-weighted mean (McMahan et al., 2017), no defence
  median        coordinate-wise median (Yin et al., 2018)
  trimmed_mean  coordinate-wise mean after dropping the largest and smallest
                values of each coordinate (Yin et al., 2018)
  krum          Multi-Krum (Blanchard et al., 2017): keep the updates closest
                to their neighbours, average those

All of them return the same AggregationResult as LatentDensityAggregator,
so the server and the experiments treat every rule the same way.
"""
from __future__ import annotations

import torch

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


AGGREGATORS = ("fedavg", "median", "trimmed_mean", "krum", "hdbscan")


def make_aggregator(name: str, fed_cfg: dict, device: str = "cpu") -> Aggregator:
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
    if name == "hdbscan":
        return LatentDensityAggregator(
            latent_dim=agg_cfg["latent_dim"],
            autoencoder_hidden=agg_cfg["autoencoder_hidden"],
            autoencoder_epochs=agg_cfg["autoencoder_epochs"],
            autoencoder_lr=agg_cfg.get("autoencoder_lr", 1e-3),
            normalize=agg_cfg.get("normalize_updates", True),
            phi_input=agg_cfg.get("phi_input", "all"),
            device=device,
            **agg_cfg["hdbscan"],
        )
    raise ValueError(f"Unknown aggregator {name!r}; expected one of {AGGREGATORS}")
