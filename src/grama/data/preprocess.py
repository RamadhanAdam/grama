"""Preprocessing: min-max normalization and sliding-window segmentation.

Implements Sec 3.2 of the concept note:
  - payload bytes normalized to [0, 1] via min-max scaling (eq. 3)
  - continuous CAN frame streams segmented into sliding windows S_t = [s1..sW]
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


PAYLOAD_COLS = [f"d{i}" for i in range(8)]


def min_max_normalize(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Eq. 3: D_tilde_ij = (D_ij - min(D_j)) / (max(D_j) - min(D_j)), per column j."""
    columns = columns or PAYLOAD_COLS
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            continue
        col_min = out[col].min()
        col_max = out[col].max()
        denom = (col_max - col_min) or 1.0  # guard against constant columns
        out[col] = (out[col] - col_min) / denom
    return out


def add_inter_arrival_time(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """delta_tau = tau_k - tau_k-1, used as an extra feature (Sec 3.1)."""
    out = df.sort_values(timestamp_col).reset_index(drop=True)
    out["delta_t"] = out[timestamp_col].diff().fillna(0.0)
    return out


@dataclass
class Window:
    frames: pd.DataFrame       # the W rows belonging to this window
    can_ids: np.ndarray         # unique CAN IDs present, for graph construction
    label: int                   # window-level label (majority vote over frame labels)


def sliding_windows(
    df: pd.DataFrame,
    window_size: int,
    stride: int,
    label_col: str = "label",
    can_id_col: str = "can_id",
) -> list[Window]:
    """Segment a (already time-sorted) frame stream into overlapping windows.

    A window is labeled by majority vote of its constituent frames' labels —
    if any attack frames dominate the window, the window is treated as that
    attack class, matching how a detector would see the traffic in practice.
    """
    n = len(df)
    windows: list[Window] = []
    if n < window_size:
        return windows

    for start in range(0, n - window_size + 1, stride):
        chunk = df.iloc[start : start + window_size]
        label = int(chunk[label_col].mode().iloc[0]) if label_col in chunk else -1
        can_ids = chunk[can_id_col].unique() if can_id_col in chunk else np.array([])
        windows.append(Window(frames=chunk.reset_index(drop=True), can_ids=can_ids, label=label))
    return windows
