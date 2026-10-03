"""CNN-BiGRU baseline (Sec 2 / Sec 6.2.1).

The architecture GraMa is meant to replace: a 1D CNN for local patterns in
the frame stream, a bidirectional GRU for order over time, and attention
pooling over the GRU states. This is our own implementation of that family
of models on the same windows and sequences GraMa sees. It is not a line by
line reproduction of Mnkash et al.; their adaptive weighting aggregation
(AWI) is not reproduced either, so the baseline is trained with FedAvg (and
can be paired with any other aggregator).

Input is the raw frames, not GraMa's per-node summaries, so the baseline
sees at least as much information as GraMa does:
  frame_ids   (B, L, W)     CAN-ID vocabulary index of each frame
  frame_bytes (B, L, W, 8)  payload bytes scaled to [0, 1]
"""
from __future__ import annotations

import contextlib

import torch
import torch.nn as nn
import torch.nn.functional as F


def _no_nnpack():
    nnpack = getattr(torch.backends, "nnpack", None)
    if nnpack is not None and hasattr(nnpack, "flags"):
        return nnpack.flags(enabled=False)
    return contextlib.nullcontext()


class CNNBiGRUBaseline(nn.Module):
    def __init__(self, num_nodes: int, num_classes: int, id_dim: int = 16, conv_channels: int = 64,
                 gru_hidden: int = 32, head_hidden: int = 32, dropout: float = 0.1):
        super().__init__()
        self.id_embedding = nn.Embedding(num_nodes, id_dim)
        in_ch = id_dim + 8
        self.conv = nn.Sequential(
            nn.Conv1d(in_ch, conv_channels, kernel_size=3, padding=1), nn.ReLU(),
            nn.Conv1d(conv_channels, conv_channels, kernel_size=3, padding=1), nn.ReLU(),
        )
        self.gru = nn.GRU(conv_channels, gru_hidden, batch_first=True, bidirectional=True)
        self.attn = nn.Linear(2 * gru_hidden, 1)
        self.head = nn.Sequential(
            nn.Linear(2 * gru_hidden, head_hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(head_hidden, num_classes),
        )

    def forward(self, frame_ids: torch.Tensor, frame_bytes: torch.Tensor) -> torch.Tensor:
        B, L, W = frame_ids.shape
        frames = torch.cat([self.id_embedding(frame_ids), frame_bytes], dim=-1)  # (B, L, W, id_dim+8)
        frames = frames.reshape(B * L, W, -1).transpose(1, 2)
        # NNPACK makes this conv ~7x slower on CPU; turning it off changes nothing on GPU.
        with _no_nnpack():
            h = self.conv(frames)                                                # (B*L, C, W)
        tokens = h.amax(dim=-1).reshape(B, L, -1)                                # one token per window
        states, _ = self.gru(tokens)                                             # (B, L, 2H)
        weights = F.softmax(self.attn(states).squeeze(-1), dim=1)                # attention over windows
        pooled = (weights.unsqueeze(-1) * states).sum(dim=1)
        return self.head(pooled)
