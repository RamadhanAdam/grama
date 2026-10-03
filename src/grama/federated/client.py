"""Local client training loop (Sec 4.1, Phase 4).

Each simulated vehicle holds a shard of window sequences (from
federated_split.dirichlet_partition), trains locally for a few epochs
starting from the current global weights, and returns Δw_k = w_k - w_global.

A client can be compromised (Sec 6.2.3). Then it poisons its own update:
  label_flip       trains on labels mapped to a wrong class (fixed per client)
  targeted_flip    trains with every attack labelled benign, to hide attacks
  magnitude_poison trains honestly, then scales Δw by poison_scale
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, Subset

ATTACKS = ("label_flip", "targeted_flip", "magnitude_poison")


@dataclass
class ClientUpdate:
    client_id: int
    delta_w: dict[str, torch.Tensor]   # Δw_k, per-parameter-name state dict diff (on CPU)
    num_samples: int
    local_loss: float
    malicious: bool = False             # ground truth, for scoring the defence only


def state_dict_diff(new_sd: dict, old_sd: dict) -> dict[str, torch.Tensor]:
    return {k: (new_sd[k].detach().cpu() - old_sd[k].cpu()).clone() for k in new_sd}


def apply_state_dict_delta(sd: dict, delta: dict[str, torch.Tensor], scale: float = 1.0) -> dict:
    return {k: sd[k] + scale * delta[k].to(sd[k].dtype) for k in sd}


def label_map_for(attack: str | None, num_classes: int, client_id: int, seed: int = 0) -> torch.Tensor | None:
    """Label mapping a compromised client trains with, or None for honest training."""
    if attack == "label_flip":
        g = torch.Generator().manual_seed(seed * 1000 + client_id)
        shift = int(torch.randint(1, num_classes, (1,), generator=g))
        return (torch.arange(num_classes) + shift) % num_classes  # no class keeps its label
    if attack == "targeted_flip":
        return torch.zeros(num_classes, dtype=torch.long)         # every attack -> benign
    return None


class LocalClient:
    def __init__(
        self,
        client_id: int,
        dataset: Dataset,
        batch_size: int,
        lr: float,
        device: str = "cpu",
        indices=None,
        attack: str | None = None,
        num_classes: int | None = None,
        poison_scale: float = 10.0,
        class_weights: torch.Tensor | None = None,
        seed: int = 0,
    ):
        if attack is not None and attack not in ATTACKS:
            raise ValueError(f"Unknown attack {attack!r}; expected one of {ATTACKS}")
        self.client_id = client_id
        self.dataset = dataset
        self.indices = (torch.as_tensor(indices, dtype=torch.long) if indices is not None
                        else torch.arange(len(dataset)))
        self.batch_size = batch_size
        self.lr = lr
        self.device = device
        self.attack = attack
        self.poison_scale = poison_scale
        self.class_weights = class_weights
        self.seed = seed
        self.label_map = label_map_for(attack, num_classes, client_id, seed) if num_classes else None
        self._round = 0

    @property
    def malicious(self) -> bool:
        return self.attack is not None

    def __len__(self) -> int:
        return len(self.indices)

    def _batches(self, generator: torch.Generator):
        """Yield (inputs..., labels) on CPU. Fast path for datasets with get_batch()."""
        if hasattr(self.dataset, "get_batch"):
            perm = self.indices[torch.randperm(len(self.indices), generator=generator)]
            for chunk in perm.split(self.batch_size):
                yield self.dataset.get_batch(chunk)
        else:
            subset = Subset(self.dataset, self.indices.tolist())
            yield from DataLoader(subset, batch_size=self.batch_size, shuffle=True, generator=generator)

    def local_train(self, model_factory, global_state_dict: dict, local_epochs: int) -> ClientUpdate:
        """model_factory: zero-arg callable returning a fresh model of the global architecture."""
        model = model_factory().to(self.device)
        model.load_state_dict(global_state_dict)
        model.train()

        optimizer = torch.optim.Adam(model.parameters(), lr=self.lr)
        weight = self.class_weights.to(self.device) if self.class_weights is not None else None
        criterion = nn.CrossEntropyLoss(weight=weight)  # Sec 4.1 Phase 4: L(y_hat, y)
        generator = torch.Generator().manual_seed(self.seed * 1_000_003 + self.client_id * 1009 + self._round)
        self._round += 1

        total_loss, num_batches = 0.0, 0
        for _ in range(local_epochs):
            for batch in self._batches(generator):
                *inputs, labels = batch
                if self.label_map is not None:
                    labels = self.label_map.to(labels.device)[labels]
                inputs = [t.to(self.device, non_blocking=True) for t in inputs]
                labels = labels.to(self.device, non_blocking=True)

                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(*inputs), labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

        delta_w = state_dict_diff(model.state_dict(), global_state_dict)  # Δw_k = w_k - w_global
        if self.attack == "magnitude_poison":
            delta_w = {k: v * self.poison_scale for k, v in delta_w.items()}

        return ClientUpdate(
            client_id=self.client_id,
            delta_w=delta_w,
            num_samples=len(self.indices),
            local_loss=total_loss / max(num_batches, 1),
            malicious=self.malicious,
        )
