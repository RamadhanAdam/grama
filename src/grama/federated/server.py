"""Custom federated round orchestration (Sec 4.1, Phase 5 end-to-end).

Deliberately not built on Flower/FedAvg assumptions — the aggregation step
here is HDBSCAN-latent-density-based, not a simple weighted mean, so a
purpose-built loop is simpler to reason about (and to test) than bending
a general FL framework's aggregation hook to fit eq. 11-15.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import torch

from grama.federated.aggregator import AggregationResult, LatentDensityAggregator
from grama.federated.client import ClientUpdate, LocalClient
from grama.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RoundHistory:
    round_num: int
    participating_clients: list[int]
    avg_local_loss: float
    aggregation: AggregationResult


@dataclass
class FederatedServer:
    model_factory: callable            # zero-arg -> fresh model instance
    clients: list[LocalClient]
    aggregator: LatentDensityAggregator
    clients_per_round: int
    local_epochs: int
    seed: int = 42
    history: list[RoundHistory] = field(default_factory=list)

    def __post_init__(self):
        self.rng = random.Random(self.seed)
        self.global_model = self.model_factory()
        self.global_state = {k: v.clone() for k, v in self.global_model.state_dict().items()}

    def sample_clients(self) -> list[LocalClient]:
        k = min(self.clients_per_round, len(self.clients))
        return self.rng.sample(self.clients, k)

    def run_round(self, round_num: int) -> RoundHistory:
        selected = self.sample_clients()
        updates: list[ClientUpdate] = []
        for client in selected:
            update = client.local_train(self.model_factory, self.global_state, self.local_epochs)
            updates.append(update)
            logger.info(
                "round %d | client %d | n=%d | local_loss=%.4f",
                round_num, client.client_id, update.num_samples, update.local_loss,
            )

        param_shapes = {k: v.shape for k, v in self.global_state.items()}
        result = self.aggregator.aggregate(updates, param_shapes)
        self.global_state = self.aggregator.apply(self.global_state, result)

        avg_loss = sum(u.local_loss for u in updates) / len(updates)
        record = RoundHistory(
            round_num=round_num,
            participating_clients=[c.client_id for c in selected],
            avg_local_loss=avg_loss,
            aggregation=result,
        )
        self.history.append(record)
        return record

    def run(self, num_rounds: int) -> list[RoundHistory]:
        for r in range(1, num_rounds + 1):
            self.run_round(r)
        return self.history

    def current_global_model(self):
        model = self.model_factory()
        model.load_state_dict(self.global_state)
        return model
