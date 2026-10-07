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
  - alie_noisy: ALIE where each colluder adds its own Gaussian noise, the
    size of the honest spread, to the shared vector. The colluders then no
    longer send identical updates, which separates a defence that finds
    duplicates (FoolsGold) from one that finds a shifted cluster.
  - adaptive: an attacker who knows the defence (Fang et al., 2020;
    Shejwalkar and Houmansadr, NDSS 2021). The attackers train like
    targeted_flip, then all send mean(honest) + gamma * d, with
    d = mean(attackers) - mean(honest) the direction of their poison. Each
    round they search for the largest gamma at which the aggregation rule
    still accepts their updates, by running an exact copy of the rule (same
    settings, same random state) on the round's updates. gamma = 1 sends the
    attackers' mean poisoned update, 0 sends the honest mean (no poison),
    larger values push harder. Rules that reject no client accept any gamma,
    so they get the maximum. This is the strongest attacker we simulate: it
    knows the honest updates, the rule and its randomness.

"""
from __future__ import annotations

import copy
import math
import random
from statistics import NormalDist

import torch

from grama.federated.client import ATTACKS, ClientUpdate, label_map_for

__all__ = ["ATTACKS", "adaptive_attack", "alie_attack", "alie_z", "label_flip", "label_map_for",
           "magnitude_poison", "select_compromised_clients", "shift_updates"]


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


def alie_attack(updates: list[ClientUpdate], malicious_idx: list[int], noise: float = 0.0,
                generator: torch.Generator | None = None) -> list[ClientUpdate]:
    """Replace the colluding clients' updates with mean - z * std of all honest updates this round.

    With noise > 0 each colluder adds N(0, (noise * std)^2) of its own, so no two send the same vector.
    """
    if not malicious_idx:
        return updates
    z = alie_z(len(updates), len(malicious_idx))
    names = list(updates[0].delta_w)
    crafted, spread = {}, {}
    for name in names:
        stack = torch.stack([u.delta_w[name].float() for u in updates])
        spread[name] = stack.std(dim=0, unbiased=False)
        crafted[name] = stack.mean(dim=0) - z * spread[name]
    out = list(updates)
    for i in malicious_idx:
        u = updates[i]
        if noise > 0.0:
            delta = {k: v + noise * spread[k] * torch.randn(v.shape, generator=generator) for k, v in crafted.items()}
        else:
            delta = {k: v.clone() for k, v in crafted.items()}
        out[i] = ClientUpdate(u.client_id, delta, u.num_samples, u.local_loss, malicious=True)
    return out


def shift_updates(updates: list[ClientUpdate], malicious_idx: list[int], scale: float) -> list[ClientUpdate]:
    """Every attacker sends mean(honest) + scale * (mean(attackers) - mean(honest))."""
    bad = set(malicious_idx)
    honest = [u for i, u in enumerate(updates) if i not in bad]
    names = list(updates[0].delta_w)

    def mean(group, name):
        return torch.stack([u.delta_w[name].float() for u in group]).mean(dim=0)

    crafted = {}
    for n in names:
        h = mean(honest, n)
        crafted[n] = h + scale * (mean([updates[i] for i in malicious_idx], n) - h)
    out = list(updates)
    for i in malicious_idx:
        u = updates[i]
        out[i] = ClientUpdate(u.client_id, {n: v.clone() for n, v in crafted.items()},
                              u.num_samples, u.local_loss, malicious=True)
    return out


def adaptive_attack(updates: list[ClientUpdate], malicious_idx: list[int], aggregator, param_shapes: dict,
                    max_scale: float = 10.0, steps: int = 7) -> tuple[list[ClientUpdate], float | None]:
    """The largest poison scale the aggregator still accepts, found by bisection on a copy of it.

    Tries max_scale, then 1 (the plain poison), then bisects between the
    largest accepted and smallest rejected scale, starting from 0 (the honest
    mean). Returns the updates to send and the scale used, or None when there
    is nothing to do (no attackers, or no honest update to measure against).
    """
    if not malicious_idx or len(malicious_idx) == len(updates):
        return updates, None
    if not getattr(aggregator, "detects_clients", False):
        return shift_updates(updates, malicious_idx, max_scale), max_scale

    def accepted(scale):
        candidate = shift_updates(updates, malicious_idx, scale)
        # Same random state as the real aggregation, which runs next.
        with torch.random.fork_rng(devices=[]):
            result = copy.deepcopy(aggregator).aggregate(candidate, param_shapes)
        ok = all(result.trust_weights.get(updates[i].client_id, 0.0) > 0.0 for i in malicious_idx)
        return ok, candidate

    ok, candidate = accepted(max_scale)
    if ok:
        return candidate, max_scale
    ok, candidate = accepted(1.0)
    lo, hi = (1.0, max_scale) if ok else (0.0, 1.0)
    best = (1.0, candidate) if ok else None
    for _ in range(steps):
        mid = (lo + hi) / 2
        ok, candidate = accepted(mid)
        if ok:
            lo, best = mid, (mid, candidate)
        else:
            hi = mid
    if best is None:   # not even a small step gets through: send the honest mean this round
        return shift_updates(updates, malicious_idx, 0.0), 0.0
    return best[1], best[0]
