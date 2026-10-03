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
  - alie ("A Little Is Enough", Baruch et al., NeurIPS 2019): the attackers
    collude and all send mean - z * std of the round's honest updates, per
    coordinate. The update sits inside the honest spread, so distance and
    density based defences find it hard to tell apart, yet it pulls every
    coordinate the same way. We give the attackers full knowledge of the
    round's honest updates, the strong setting of Fang et al. (2020).

The functions below are the same attacks as stand-alone helpers, plus the
choice of which clients are compromised.
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist

import torch

from grama.federated.client import ATTACKS, ClientUpdate, label_map_for

__all__ = ["ATTACKS", "alie_attack", "alie_z", "label_flip", "label_map_for", "magnitude_poison",
           "select_compromised_clients"]


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


def alie_z(num_clients: int, num_malicious: int) -> float:
    """z_max of Baruch et al.: s = floor(n/2 + 1) - f, z = Phi^-1((n - s) / n)."""
    n, f = num_clients, num_malicious
    s = math.floor(n / 2 + 1) - f
    p = min(max((n - s) / n, 0.5), 0.999)
    return max(NormalDist().inv_cdf(p), 0.0)


def alie_attack(updates: list[ClientUpdate], malicious_idx: list[int]) -> list[ClientUpdate]:
    """Replace the colluding clients' updates with mean - z * std of all honest updates this round."""
    if not malicious_idx:
        return updates
    z = alie_z(len(updates), len(malicious_idx))
    names = list(updates[0].delta_w)
    crafted = {}
    for name in names:
        stack = torch.stack([u.delta_w[name].float() for u in updates])
        crafted[name] = stack.mean(dim=0) - z * stack.std(dim=0, unbiased=False)
    out = list(updates)
    for i in malicious_idx:
        u = updates[i]
        out[i] = ClientUpdate(u.client_id, {k: v.clone() for k, v in crafted.items()},
                              u.num_samples, u.local_loss, malicious=True)
    return out
