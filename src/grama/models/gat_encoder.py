"""Spatial-Topological Graph Attention Network encoder (Sec 5.1, eq. 4-6).

Uses a dense adjacency mask rather than torch_geometric, since the ECU graph
is small (single-digit to low tens of nodes per vehicle) — this keeps the
dependency footprint light and the module trivially portable/CPU-testable.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class GATLayer(nn.Module):
    """One multi-head graph attention layer implementing eq. 4-6 directly."""

    def __init__(
        self,
        in_features: int,
        out_features: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        leaky_relu_slope: float = 0.2,
        concat_heads: bool = True,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.out_features = out_features
        self.concat_heads = concat_heads

        # W: learnable projection, one per head, matching eq. 4's W x_i.
        self.W = nn.Parameter(torch.empty(num_heads, in_features, out_features))
        # a: learnable attention vector, one per head, matching eq. 4's a^T [Wx_i || Wx_j].
        self.a = nn.Parameter(torch.empty(num_heads, 2 * out_features))

        nn.init.xavier_uniform_(self.W)
        nn.init.xavier_uniform_(self.a.unsqueeze(0))

        self.leaky_relu = nn.LeakyReLU(leaky_relu_slope)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """
        x: (B, N, F_in) node features per batch of windows
        adjacency: (B, N, N) binary adjacency (1 = edge, includes self-loops)
        returns: (B, N, out_features * num_heads) if concat_heads else averaged
        """
        B, N, _ = x.shape
        H, Fo = self.num_heads, self.out_features

        # Project features per head: (B, H, N, Fo)
        Wx = torch.einsum("bnf,hfo->bhno", x, self.W)

        # Build pairwise concatenations [Wx_i || Wx_j] -> (B, H, N, N, 2*Fo)
        Wx_i = Wx.unsqueeze(3).expand(B, H, N, N, Fo)
        Wx_j = Wx.unsqueeze(2).expand(B, H, N, N, Fo)
        concat = torch.cat([Wx_i, Wx_j], dim=-1)  # (B, H, N, N, 2*Fo)

        # eq. 4: e_ij = LeakyReLU(a^T [Wx_i || Wx_j])
        e = self.leaky_relu(torch.einsum("bhijf,hf->bhij", concat, self.a))

        # Mask out non-neighbors before softmax (eq. 5's sum over N(i) only).
        mask = adjacency.unsqueeze(1).expand(B, H, N, N)  # (B, H, N, N)
        e = e.masked_fill(mask == 0, float("-inf"))

        alpha = F.softmax(e, dim=-1)  # eq. 5
        alpha = torch.nan_to_num(alpha, nan=0.0)  # isolated nodes -> all -inf row -> softmax NaN
        alpha = self.dropout(alpha)

        # eq. 6: z_i = sigma( sum_j alpha_ij * W x_j )
        z = torch.einsum("bhij,bhjo->bhio", alpha, Wx)  # (B, H, N, Fo)

        if self.concat_heads:
            z = z.permute(0, 2, 1, 3).reshape(B, N, H * Fo)
        else:
            z = z.mean(dim=1)
        return z


class SpatialTopologicalGAT(nn.Module):
    """Stacks a GAT layer + activation to produce Z_topo ∈ R^{W x d} per window's graph."""

    def __init__(
        self,
        in_features: int,
        hidden_features: int,
        out_features: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        leaky_relu_slope: float = 0.2,
        activation: str = "elu",
    ):
        super().__init__()
        self.layer1 = GATLayer(
            in_features, hidden_features, num_heads, dropout, leaky_relu_slope, concat_heads=True
        )
        self.layer2 = GATLayer(
            hidden_features * num_heads,
            out_features,
            num_heads=1,
            dropout=dropout,
            leaky_relu_slope=leaky_relu_slope,
            concat_heads=False,
        )
        self.act = {"elu": F.elu, "relu": F.relu, "gelu": F.gelu}[activation]

    def forward(self, x: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """
        x: (B, N, F_in), adjacency: (B, N, N)
        returns: (B, N, out_features) topological embeddings per ECU node
        """
        h = self.act(self.layer1(x, adjacency))
        z = self.act(self.layer2(h, adjacency))
        return z

    def pool_to_sequence_token(self, z: torch.Tensor) -> torch.Tensor:
        """Mean-pool node embeddings -> one token per window, for feeding into Mamba.

        z: (B, N, out_features) -> (B, out_features)
        """
        return z.mean(dim=1)
