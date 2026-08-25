"""Checkpointing for federated training runs (Sec 4.1, Phase 5 loop).

Saves/restores everything needed to resume a federated run after a crash
or preemption:
  - the current global model state_dict (w_global^(t))
  - the round number reached
  - RNG state (python `random` + torch) driving client sampling and local
    training, so a resumed run's *subsequent* rounds are reproducible
    given the same seed, even though the interrupted round itself is not
  - a lightweight summary of every completed round (NOT the full
    AggregationResult, which holds a per-client delta tensor for every
    parameter — that's fine for one round in memory, but would make a
    checkpoint file grow without bound over hundreds of rounds)

Two things make this safe to use on a long unattended run:
  - Writes are atomic: payload is written to a temp file in the same
    directory, then `os.replace`'d over the target path. A crash mid-write
    leaves the old checkpoint intact rather than a truncated/corrupt one.
  - A human-readable `history.jsonl` (one JSON object per completed round)
    is appended alongside the binary checkpoint, so round-by-round progress
    can be tailed (`tail -f history.jsonl`) without loading torch or the
    (potentially large) model weights.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass

import torch


@dataclass
class RoundSummary:
    """Scalar-only summary of one completed round — safe to accumulate
    indefinitely in a checkpoint without the file growing per-round."""

    round_num: int
    participating_clients: list[int]
    avg_local_loss: float
    benign_cluster_id: int | None
    num_rejected: int
    num_participants: int


def round_summary_from_history(record) -> RoundSummary:
    """Build a RoundSummary from a full RoundHistory record (see server.py)."""
    return RoundSummary(
        round_num=record.round_num,
        participating_clients=list(record.participating_clients),
        avg_local_loss=record.avg_local_loss,
        benign_cluster_id=record.aggregation.benign_cluster_id,
        num_rejected=sum(1 for w in record.aggregation.trust_weights.values() if w == 0.0),
        num_participants=len(record.participating_clients),
    )


def append_round_log(path: str, summary: RoundSummary) -> None:
    """Append one JSON line for this round. Best-effort: a logging failure
    here should never take down an otherwise-successful training round."""
    try:
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(asdict(summary)) + "\n")
    except OSError:
        pass


def save_checkpoint(
    path: str,
    round_num: int,
    global_state: dict[str, torch.Tensor],
    history_summaries: list[RoundSummary],
    py_rng_state,
    torch_rng_state: torch.Tensor,
) -> None:
    """Atomically write a full checkpoint (model weights + resume metadata)."""
    payload = {
        "round_num": round_num,
        "global_state": global_state,
        "history_summaries": [asdict(s) for s in history_summaries],
        "py_rng_state": py_rng_state,
        "torch_rng_state": torch_rng_state,
    }
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".ckpt_tmp_", suffix=".pt")
    os.close(fd)
    try:
        torch.save(payload, tmp_path)
        os.replace(tmp_path, path)  # atomic on POSIX filesystems
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_checkpoint(path: str) -> dict:
    """Load a checkpoint written by save_checkpoint(). Raises FileNotFoundError
    / torch's own errors on a missing or corrupt file — callers should let
    these surface rather than silently starting from scratch."""
    payload = torch.load(path, map_location="cpu", weights_only=False)
    payload["history_summaries"] = [RoundSummary(**s) for s in payload["history_summaries"]]
    return payload
