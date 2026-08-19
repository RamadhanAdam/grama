"""Attack simulations for adversarial poisoning evaluation (Sec 6.2.3).

Two attack types, applied to a fraction of clients per round:
  - label_flip: mislabels local training data before local training runs,
    so the resulting Δw is poisoned "honestly" (a compromised vehicle
    genuinely learns the wrong mapping).
  - magnitude_poison: directly scales up a client's already-computed Δw,
    simulating a compromised node injecting an oversized gradient update
    to try to dominate aggregation.
"""
from __future__ import annotations

import random

import torch

from grama.federated.client import ClientUpdate


def label_flip(labels: torch.Tensor, num_classes: int, seed: int | None = None) -> torch.Tensor:
    """Shift every label to a different, deterministic-per-call random class (not identity)."""
    rng = random.Random(seed)
    flipped = labels.clone()
    for i in range(len(labels)):
        orig = int(labels[i].item())
        choices = [c for c in range(num_classes) if c != orig]
        flipped[i] = rng.choice(choices)
    return flipped


def magnitude_poison(update: ClientUpdate, scale: float) -> ClientUpdate:
    """Scale a client's Δw by `scale`, simulating an oversized malicious gradient."""
    poisoned_delta = {k: v * scale for k, v in update.delta_w.items()}
    return ClientUpdate(
        client_id=update.client_id,
        delta_w=poisoned_delta,
        num_samples=update.num_samples,
        local_loss=update.local_loss,
    )


def select_compromised_clients(client_ids: list[int], fraction: float, seed: int = 42) -> set[int]:
    rng = random.Random(seed)
    k = round(len(client_ids) * fraction)
    return set(rng.sample(client_ids, k))
