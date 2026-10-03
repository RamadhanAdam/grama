"""Device choice: CUDA when there is a GPU, else CPU. GRAMA_DEVICE overrides."""
from __future__ import annotations

import os

import torch


def pick_device() -> str:
    forced = os.environ.get("GRAMA_DEVICE")
    if forced:
        return forced
    return "cuda" if torch.cuda.is_available() else "cpu"


def describe_device(device: str) -> str:
    if device.startswith("cuda") and torch.cuda.is_available():
        props = torch.cuda.get_device_properties(torch.device(device))
        return f"{props.name} ({props.total_memory / 2**30:.0f} GB)"
    return f"CPU ({os.cpu_count()} cores, torch threads {torch.get_num_threads()})"
