"""Custom federated round orchestration (Sec 4.1, Phase 5 end-to-end).

Not built on Flower: the aggregation step here can be HDBSCAN over latent
updates rather than a weighted mean, and a purpose-built loop is simpler to
reason about (and to test) than bending a framework's aggregation hook to
fit eq. 11-15. Any aggregator with the Aggregator interface plugs in.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from typing import Callable

import torch

from grama.attacks.poisoning import adaptive_attack, alie_attack
from grama.federated import checkpoint as ckpt
from grama.federated.aggregator import AggregationResult, Aggregator
from grama.federated.client import ClientUpdate, LocalClient
from grama.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RoundHistory:
    round_num: int
    participating_clients: list[int]
    avg_local_loss: float
    aggregation: AggregationResult
    malicious_clients: list[int] = field(default_factory=list)
    rejected_clients: list[int] = field(default_factory=list)
    metrics: dict | None = None      # test metrics of the new global model, when evaluated
    seconds: float = 0.0
    attack_scale: float | None = None  # poison scale the adaptive attackers sent this round


@dataclass
class FederatedServer:
    model_factory: Callable            # zero-arg -> fresh model instance
    clients: list[LocalClient]
    aggregator: Aggregator
    clients_per_round: int
    local_epochs: int
    seed: int = 42
    eval_fn: Callable | None = None    # global_state -> metrics dict
    eval_every: int = 1
    adaptive_max_scale: float = 10.0   # adaptive attack: largest poison scale it tries
    adaptive_steps: int = 7            # adaptive attack: bisection steps per round
    history: list[RoundHistory] = field(default_factory=list)
    last_round_num: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        self.rng = random.Random(self.seed)
        self.global_model = self.model_factory()
        self.global_state = {k: v.clone() for k, v in self.global_model.state_dict().items()}

    def sample_clients(self) -> list[LocalClient]:
        k = min(self.clients_per_round, len(self.clients))
        return self.rng.sample(self.clients, k)

    def run_round(self, round_num: int, evaluate: bool = False) -> RoundHistory:
        start = time.perf_counter()
        selected = self.sample_clients()
        updates: list[ClientUpdate] = []
        for client in selected:
            update = client.local_train(self.model_factory, self.global_state, self.local_epochs)
            updates.append(update)
            logger.debug(
                "round %d | client %d | n=%d | local_loss=%.4f",
                round_num, client.client_id, update.num_samples, update.local_loss,
            )

        colluders = [i for i, c in enumerate(selected) if getattr(c, "attack", None) == "alie"]
        if colluders:
            updates = alie_attack(updates, colluders)

        param_shapes = {k: v.shape for k, v in self.global_state.items()}
        attack_scale = None
        adaptive = [i for i, c in enumerate(selected) if getattr(c, "attack", None) == "adaptive"]
        if adaptive:
            updates, attack_scale = adaptive_attack(updates, adaptive, self.aggregator, param_shapes,
                                                    self.adaptive_max_scale, self.adaptive_steps)
        result = self.aggregator.aggregate(updates, param_shapes)
        self.global_state = self.aggregator.apply(self.global_state, result)

        record = RoundHistory(
            round_num=round_num,
            participating_clients=[c.client_id for c in selected],
            avg_local_loss=sum(u.local_loss for u in updates) / len(updates),
            aggregation=result,
            malicious_clients=[u.client_id for u in updates if u.malicious],
            rejected_clients=[cid for cid, w in result.trust_weights.items() if w == 0.0],
            attack_scale=attack_scale,
        )
        if evaluate and self.eval_fn is not None:
            record.metrics = self.eval_fn(self.global_state)
        record.seconds = time.perf_counter() - start
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
            evaluate = r == end or (self.eval_every > 0 and r % self.eval_every == 0)
            record = self.run_round(r, evaluate=evaluate)
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
