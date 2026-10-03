"""Inference latency, throughput, model size and communication cost (Sec 6.1, 8.1).

A dev box or a GPU node is not a vehicle microcontroller, so these numbers
are for comparing models on the same hardware (GraMa against the CNN-BiGRU
baseline), which is what the complexity comparison needs. Single-sequence
latency on one CPU thread is the closest stand-in for an edge device.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import torch


@dataclass
class LatencyResult:
    mean_ms_per_sequence: float
    p95_ms_per_sequence: float
    num_runs: int
    device: str
    peak_memory_mb: float | None  # None on CPU


def count_parameters(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def model_size_kb(model: torch.nn.Module) -> float:
    """float32 size of all parameters and buffers, i.e. what one Δw upload costs."""
    n = sum(p.numel() * p.element_size() for p in model.parameters())
    n += sum(b.numel() * b.element_size() for b in model.buffers())
    return n / 1024.0


@torch.no_grad()
def benchmark_inference(model: torch.nn.Module, inputs: tuple[torch.Tensor, ...], device: str = "cpu",
                        num_warmup: int = 5, num_runs: int = 50) -> LatencyResult:
    """Time model(*inputs) on one batch (use batch size 1 for per-sequence latency)."""
    model = model.to(device).eval()
    inputs = tuple(t.to(device) for t in inputs)
    cuda = device.startswith("cuda")
    if cuda:
        torch.cuda.reset_peak_memory_stats(device)

    for _ in range(num_warmup):
        model(*inputs)
    if cuda:
        torch.cuda.synchronize()

    timings = []
    for _ in range(num_runs):
        start = time.perf_counter()
        model(*inputs)
        if cuda:
            torch.cuda.synchronize()
        timings.append((time.perf_counter() - start) * 1000.0)

    timings.sort()
    return LatencyResult(
        mean_ms_per_sequence=sum(timings) / len(timings),
        p95_ms_per_sequence=timings[max(0, int(0.95 * len(timings)) - 1)],
        num_runs=num_runs,
        device=device,
        peak_memory_mb=torch.cuda.max_memory_allocated(device) / 2**20 if cuda else None,
    )


@torch.no_grad()
def throughput(model: torch.nn.Module, inputs: tuple[torch.Tensor, ...], device: str = "cpu",
               num_runs: int = 10) -> float:
    """Sequences per second on a full batch."""
    model = model.to(device).eval()
    inputs = tuple(t.to(device) for t in inputs)
    model(*inputs)
    if device.startswith("cuda"):
        torch.cuda.synchronize()
    start = time.perf_counter()
    for _ in range(num_runs):
        model(*inputs)
    if device.startswith("cuda"):
        torch.cuda.synchronize()
    return inputs[0].shape[0] * num_runs / (time.perf_counter() - start)


def as_dict(result: LatencyResult) -> dict:
    return asdict(result)
