"""Local client training loop (Sec 4.1, Phase 4).

Each simulated vehicle holds a shard of windowed samples (from
federated_split.dirichlet_partition), trains locally for a few epochs
starting from the current global weights, and returns Δw_k = w_k - w_global.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


@dataclass
class ClientUpdate:
    client_id: int
    delta_w: dict[str, torch.Tensor]   # Δw_k, per-parameter-name state dict diff
    num_samples: int                     # for optional sample-weighted diagnostics
    local_loss: float


def state_dict_diff(new_sd: dict, old_sd: dict) -> dict[str, torch.Tensor]:
    return {k: (new_sd[k] - old_sd[k]).detach().clone() for k in new_sd}


def apply_state_dict_delta(sd: dict, delta: dict[str, torch.Tensor], scale: float = 1.0) -> dict:
    return {k: sd[k] + scale * delta[k] for k in sd}


class LocalClient:
    def __init__(self, client_id: int, dataset: Dataset, batch_size: int, lr: float, device: str = "cpu"):
        self.client_id = client_id
        self.dataset = dataset
        self.batch_size = batch_size
        self.lr = lr
        self.device = device

    def local_train(
        self,
        model_factory,
        global_state_dict: dict,
        local_epochs: int,
    ) -> ClientUpdate:
        """
        model_factory: zero-arg callable returning a fresh, uninitialized model
                       instance matching the global architecture.
        """
        model = model_factory().to(self.device)
        model.load_state_dict(global_state_dict)
        model.train()

        loader = DataLoader(self.dataset, batch_size=self.batch_size, shuffle=True)
        optimizer = torch.optim.Adam(model.parameters(), lr=self.lr)
        criterion = nn.CrossEntropyLoss()  # eq. Sec 4.1 Phase 4: L(y_hat, y)

        total_loss, num_batches = 0.0, 0
        for _ in range(local_epochs):
            for node_features, adjacency, labels in loader:
                node_features = node_features.to(self.device)
                adjacency = adjacency.to(self.device)
                labels = labels.to(self.device)

                optimizer.zero_grad()
                logits = model(node_features, adjacency)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

        new_sd = model.state_dict()
        delta_w = state_dict_diff(new_sd, global_state_dict)  # Δw_k = w_k^(t) - w_global^(t)

        avg_loss = total_loss / max(num_batches, 1)
        return ClientUpdate(
            client_id=self.client_id,
            delta_w=delta_w,
            num_samples=len(self.dataset),
            local_loss=avg_loss,
        )
