"""Two more detectors for the comparison with GraMa, on the same windows and sequences.

GCNWindowIDS     a graph detector of the kind used for CAN intrusion detection: graph convolution
                 (symmetric-normalised adjacency, no attention) over the window's CAN-ID graph, mean
                 pooling of the active nodes, an MLP. temporal="last" classifies the last window alone,
                 as single-window graph detectors do; temporal="gru" runs a GRU over the L window vectors,
                 which keeps everything of GraMa except the attention in the graph layers and the Mamba block.
TransformerIDS   a Transformer over the frames: one encoder layer reads the frames of each window, the window
                 vectors get positions and go through two more layers. It sees the same frames as the
                 CNN-BiGRU, and the same CAN-ID embeddings.

Inputs match the two dataset views (see data/dataset.py):
  GCNWindowIDS     node_features (B, L, N, F), adjacency (B, L, N, N)
  TransformerIDS   frame_ids (B, L, W), frame_bytes (B, L, W, 8)
"""
from __future__ import annotations

import torch
import torch.nn as nn


class GCNWindowIDS(nn.Module):
    def __init__(self, in_features: int, num_nodes: int, num_classes: int, hidden_features: int = 64,
                 id_dim: int = 8, layers: int = 2, dropout: float = 0.1, head_hidden: int = 32,
                 temporal: str = "last"):
        super().__init__()
        if temporal not in ("last", "gru"):
            raise ValueError(f"temporal must be 'last' or 'gru', got {temporal!r}")
        self.temporal = temporal
        self.id_embedding = nn.Embedding(num_nodes, id_dim) if id_dim else None
        dims = [in_features + (id_dim or 0)] + [hidden_features] * layers
        self.layers = nn.ModuleList(nn.Linear(a, b) for a, b in zip(dims[:-1], dims[1:]))
        self.dropout = nn.Dropout(dropout)
        if temporal == "gru":
            self.gru = nn.GRU(hidden_features, hidden_features, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(hidden_features, head_hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(head_hidden, num_classes),
        )

    def forward(self, node_features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        if self.temporal == "last":
            node_features, adjacency = node_features[:, -1:], adjacency[:, -1:]
        B, L, N, _ = node_features.shape
        h = node_features
        if self.id_embedding is not None:
            ids = self.id_embedding(torch.arange(N, device=h.device)).expand(B, L, N, -1)
            h = torch.cat([h, ids], dim=-1)
        deg = adjacency.sum(dim=-1).clamp(min=1.0)                          # (B, L, N)
        norm = deg.rsqrt()
        a_hat = adjacency * norm.unsqueeze(-1) * norm.unsqueeze(-2)         # D^-1/2 A D^-1/2
        for layer in self.layers:
            h = self.dropout(torch.relu(a_hat @ layer(h)))
        active = (adjacency.diagonal(dim1=-2, dim2=-1) > 0).unsqueeze(-1).float()   # nodes that sent a frame
        tokens = (h * active).sum(dim=2) / active.sum(dim=2).clamp(min=1.0)           # (B, L, hidden)
        if self.temporal == "gru":
            states, _ = self.gru(tokens)
            return self.head(states[:, -1])
        return self.head(tokens[:, -1])


class TransformerIDS(nn.Module):
    def __init__(self, num_nodes: int, num_classes: int, id_dim: int = 16, d_model: int = 64, heads: int = 4,
                 frame_layers: int = 1, window_layers: int = 2, ff_mult: int = 2, dropout: float = 0.1,
                 head_hidden: int = 32, seq_len: int = 8):
        super().__init__()
        self.id_embedding = nn.Embedding(num_nodes, id_dim)
        self.frame_proj = nn.Linear(id_dim + 8, d_model)

        def encoder(n_layers):
            layer = nn.TransformerEncoderLayer(d_model, heads, d_model * ff_mult, dropout, batch_first=True,
                                               norm_first=True)
            return nn.TransformerEncoder(layer, n_layers, enable_nested_tensor=False)

        self.frame_encoder = encoder(frame_layers)
        self.window_encoder = encoder(window_layers)
        self.position = nn.Parameter(torch.randn(1, seq_len, d_model) * 0.02)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Sequential(
            nn.Linear(d_model, head_hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(head_hidden, num_classes),
        )

    def forward(self, frame_ids: torch.Tensor, frame_bytes: torch.Tensor) -> torch.Tensor:
        B, L, W = frame_ids.shape
        frames = self.frame_proj(torch.cat([self.id_embedding(frame_ids), frame_bytes], dim=-1))   # (B, L, W, d)
        windows = self.frame_encoder(frames.reshape(B * L, W, -1)).mean(dim=1).reshape(B, L, -1)  # (B, L, d)
        states = self.window_encoder(windows + self.position[:, :L])
        return self.head(self.norm(states.mean(dim=1)))
