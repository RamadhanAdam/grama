"""Inference latency (ms/frame) and memory footprint (MB) benchmarking,
approximating edge-microcontroller deployment characteristics (Sec 6.1, 8.1).

Real MCU deployment obviously can't be measured on a dev/GPU box — this
gives a same-hardware, apples-to-apples comparison against the CNN-BiGRU
baseline, which is what Table 1's complexity comparison is actually for.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import torch


@dataclass
class LatencyResult:
    mean_ms_per_window: float
    p95_ms_per_window: float
    num_windows_measured: int
    peak_memory_mb: float | None  # None on CPU-only runs


def benchmark_inference(
    model: torch.nn.Module,
    node_features: torch.Tensor,
    adjacency: torch.Tensor,
    num_warmup: int = 5,
    num_runs: int = 50,
    device: str = "cpu",
) -> LatencyResult:
    """
    node_features: (1, L, N, F_in) single sequence to repeatedly time
    adjacency:      (1, L, N, N)
    """
    model = model.to(device).eval()
    node_features = node_features.to(device)
    adjacency = adjacency.to(device)

    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats(device)

    with torch.no_grad():
        for _ in range(num_warmup):
            model(node_features, adjacency)
        if device.startswith("cuda"):
            torch.cuda.synchronize()

        timings = []
        for _ in range(num_runs):
            start = time.perf_counter()
            model(node_features, adjacency)
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            timings.append((time.perf_counter() - start) * 1000.0)  # ms

    timings.sort()
    mean_ms = sum(timings) / len(timings)
    p95_ms = timings[int(0.95 * len(timings)) - 1]

    peak_mb = None
    if device.startswith("cuda"):
        peak_mb = torch.cuda.max_memory_allocated(device) / (1024 ** 2)

    return LatencyResult(
        mean_ms_per_window=mean_ms,
        p95_ms_per_window=p95_ms,
        num_windows_measured=num_runs,
        peak_memory_mb=peak_mb,
    )
