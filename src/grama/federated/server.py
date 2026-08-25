"""Custom federated round orchestration (Sec 4.1, Phase 5 end-to-end).

Deliberately not built on Flower/FedAvg assumptions — the aggregation step
here is HDBSCAN-latent-density-based, not a simple weighted mean, so a
purpose-built loop is simpler to reason about (and to test) than bending
a general FL framework's aggregation hook to fit eq. 11-15.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field

import torch

from grama.federated import checkpoint as ckpt
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
    last_round_num: int = field(default=0, init=False, repr=False)

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

    def run(
        self,
        num_rounds: int,
        checkpoint_dir: str | None = None,
        checkpoint_every: int = 1,
    ) -> list[RoundHistory]:
        """Run `num_rounds` more rounds from wherever this server currently
        is — round 1 for a fresh server, or one past whatever load_checkpoint()
        restored. (So a fresh run's `num_rounds` still means "total rounds",
        matching the old behaviour; a resumed run's means "additional rounds".)

        If checkpoint_dir is given, writes checkpoint_dir/latest.pt every
        `checkpoint_every` rounds (and always after the last round of this
        call, even if that doesn't land on the interval), plus one JSON line
        per round to checkpoint_dir/history.jsonl for cheap tail -f monitoring.
        checkpoint_every=1 (default) checkpoints after every round — the
        safest setting, at the cost of one extra disk write per round.
        """
        start = self.last_round_num + 1
        end = self.last_round_num + num_rounds
        for r in range(start, end + 1):
            record = self.run_round(r)
            self.last_round_num = r
            if checkpoint_dir:
                summary = ckpt.round_summary_from_history(record)
                ckpt.append_round_log(os.path.join(checkpoint_dir, "history.jsonl"), summary)
                if r % checkpoint_every == 0 or r == end:
                    path = os.path.join(checkpoint_dir, "latest.pt")
                    self.save_checkpoint(path)
                    logger.info("checkpoint saved: round %d -> %s", r, path)
        return self.history

    def save_checkpoint(self, path: str) -> None:
        """Write model weights + RNG state + round counter + a scalar summary
        of every completed round to `path`, atomically."""
        summaries = [ckpt.round_summary_from_history(rec) for rec in self.history]
        ckpt.save_checkpoint(
            path=path,
            round_num=self.last_round_num,
            global_state=self.global_state,
            history_summaries=summaries,
            py_rng_state=self.rng.getstate(),
            torch_rng_state=torch.get_rng_state(),
        )

    def load_checkpoint(self, path: str) -> list[ckpt.RoundSummary]:
        """Restore global weights, RNG state, and the round counter from a
        checkpoint. Returns the RoundSummary list for rounds completed
        *before* this checkpoint, for logging/inspection — these are NOT
        merged into self.history, since only scalar summaries (not full
        per-client delta tensors) survive a checkpoint round-trip. Call this
        before run(); run()'s returned history will then hold only rounds
        executed in this process, starting after the resume point.
        """
        payload = ckpt.load_checkpoint(path)
        self.global_state = payload["global_state"]
        self.rng.setstate(payload["py_rng_state"])
        torch.set_rng_state(payload["torch_rng_state"])
        self.last_round_num = payload["round_num"]
        logger.info("resumed from checkpoint %s at round %d", path, self.last_round_num)
        return payload["history_summaries"]

    def current_global_model(self):
        model = self.model_factory()
        model.load_state_dict(self.global_state)
        return model
