"""Attack simulations for adversarial poisoning evaluation (Sec 6.2.3).

The attacks run inside the compromised clients (see federated/client.py,
LocalClient(attack=...)), the way a compromised vehicle would poison its own
update before sending it:
  - label_flip: trains on wrong labels, so the resulting Δw is poisoned
    "honestly" (the vehicle genuinely learns the wrong mapping).
  - targeted_flip: trains with every attack labelled benign, so the global
    model learns to let attacks through.
  - magnitude_poison: scales an honest Δw up, an oversized update that tries
    to dominate aggregation.

The functions below are the same attacks as stand-alone helpers, plus the
choice of which clients are compromised.
"""
from __future__ import annotations

import random

import torch

from grama.federated.client import ATTACKS, ClientUpdate, label_map_for

__all__ = ["ATTACKS", "label_flip", "label_map_for", "magnitude_poison", "select_compromised_clients"]


def label_flip(labels: torch.Tensor, num_classes: int, seed: int | None = None) -> torch.Tensor:
    """Move every label to a different class, chosen at random per sample (seeded)."""
    g = torch.Generator().manual_seed(seed if seed is not None else random.randrange(2**31))
    shift = torch.randint(1, num_classes, labels.shape, generator=g)
    return (labels + shift) % num_classes


def magnitude_poison(update: ClientUpdate, scale: float) -> ClientUpdate:
    """Scale a client's Δw by `scale`, simulating an oversized malicious update."""
    return ClientUpdate(
        client_id=update.client_id,
        delta_w={k: v * scale for k, v in update.delta_w.items()},
        num_samples=update.num_samples,
        local_loss=update.local_loss,
        malicious=True,
    )


def select_compromised_clients(client_ids: list[int], fraction: float, seed: int = 42) -> set[int]:
    rng = random.Random(seed)
    k = round(len(client_ids) * fraction)
    return set(rng.sample(list(client_ids), k))
