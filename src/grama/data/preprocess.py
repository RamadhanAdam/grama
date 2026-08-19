"""Preprocessing: deduplication, min-max normalization, and sliding-window segmentation.

Implements Sec 3.2 of the concept note:
  - deduplication: drop ~99.7% of exact duplicate frames (critical to prevent train/test leakage)
  - payload bytes normalized to [0, 1] via min-max scaling (eq. 3)
  - continuous CAN frame streams segmented into sliding windows S_t = [s1..sW]

NOTE: Real CICIoV2024 has NO timestamp column, so inter-arrival time is unavailable.
Instead, we use frame count per window as a burst-intensity signal.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


PAYLOAD_COLS = [f"DATA_{i}" for i in range(8)]


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows.
    
    CICIoV2024 is ~99.7% duplicates (per Stiawan et al., IJAIT 2024).
    Deduplication MUST happen before train/test split to avoid leakage.
    """
    n_before = len(df)
    out = df.drop_duplicates(subset=PAYLOAD_COLS + ["ID", "label"], keep="first").reset_index(drop=True)
    n_after = len(out)
    pct_removed = 100 * (n_before - n_after) / max(n_before, 1)
    print(f"Deduplicated: {n_before} → {n_after} rows ({pct_removed:.1f}% removed)")
    return out


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
    can_id_col: str = "ID",
) -> list[Window]:
    """Segment a frame stream into overlapping windows.

    A window is labeled by majority vote of its constituent frames' labels —
    if any attack frames dominate the window, the window is treated as that
    attack class, matching how a detector would see the traffic in practice.
    
    NOTE: No timestamp column in real CICIoV2024, so windows are segmented by
    row order only (no explicit timing). Inter-arrival time is not available.
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
