"""Spatial-Topological Graph Attention Network encoder (Sec 5.1, eq. 4-6).

Uses a dense adjacency mask rather than torch_geometric. The CAN-ID graph is
small (tens of nodes per window), so a dense mask keeps the dependency list
short and the module easy to test on a CPU.

Node activity is carried by the adjacency itself: a node that sent no frame
in the window has no edges, not even a self-loop. Such nodes get zero
attention and are left out of the pooled window token.

Two additions to plain eq. 4-6, both switchable in config/model.yaml:
  residual   each layer adds a linear map of the node's own input,
             z_i = sigma(sum_j alpha_ij W x_j + W_res x_i). On a dense
             graph the attention sum alone averages a node with all its
             neighbours, and the one ID that is under attack gets washed out.
  pooling    "attention" learns which nodes matter for the window token;
             "mean" averages the active nodes.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class GATLayer(nn.Module):
    """One multi-head graph attention layer implementing eq. 4-6."""

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

        # W: learnable projection, one per head (eq. 4's W x_i).
        self.W = nn.Parameter(torch.empty(num_heads, in_features, out_features))
        # a: attention vector, one per head (eq. 4's a^T [Wx_i || Wx_j]).
        self.a = nn.Parameter(torch.empty(num_heads, 2 * out_features))

        nn.init.xavier_uniform_(self.W)
        nn.init.xavier_uniform_(self.a.unsqueeze(0))

        self.leaky_relu = nn.LeakyReLU(leaky_relu_slope)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """
        x: (B, N, F_in) node features
        adjacency: (B, N, N), nonzero = edge (self-loops mark active nodes)
        returns: (B, N, out_features * num_heads) if concat_heads else (B, N, out_features)
        """
        B, N, _ = x.shape
        H, Fo = self.num_heads, self.out_features

        Wx = torch.einsum("bnf,hfo->bhno", x, self.W)  # (B, H, N, Fo)

        # eq. 4: a^T [Wx_i || Wx_j] = a_left . Wx_i + a_right . Wx_j.
        # Splitting a this way gives the same scores without building the
        # (B, H, N, N, 2Fo) pairwise tensor.
        score_i = torch.einsum("bhno,ho->bhn", Wx, self.a[:, :Fo])
        score_j = torch.einsum("bhno,ho->bhn", Wx, self.a[:, Fo:])
        e = self.leaky_relu(score_i.unsqueeze(-1) + score_j.unsqueeze(-2))  # (B, H, N, N)

        # eq. 5: softmax over the neighbourhood N(i) only. A large negative
        # fill (not -inf) keeps rows with no neighbours finite; multiplying by
        # the mask afterwards sets those rows to zero.
        mask = (adjacency > 0).unsqueeze(1)  # (B, 1, N, N)
        e = e.masked_fill(~mask, torch.finfo(e.dtype).min)
        alpha = F.softmax(e, dim=-1) * mask
        alpha = self.dropout(alpha)

        z = torch.einsum("bhij,bhjo->bhio", alpha, Wx)  # eq. 6, before sigma

        if self.concat_heads:
            return z.permute(0, 2, 1, 3).reshape(B, N, H * Fo)
        return z.mean(dim=1)


class SpatialTopologicalGAT(nn.Module):
    """Two GAT layers producing Z_topo, one embedding per CAN-ID node."""

    def __init__(
        self,
        in_features: int,
        hidden_features: int,
        out_features: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        leaky_relu_slope: float = 0.2,
        activation: str = "elu",
        residual: bool = True,
        pooling: str = "attention",
    ):
        super().__init__()
        if pooling not in ("attention", "mean"):
            raise ValueError(f"pooling must be 'attention' or 'mean', got {pooling!r}")
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
        self.res1 = nn.Linear(in_features, hidden_features * num_heads, bias=False) if residual else None
        self.res2 = nn.Linear(hidden_features * num_heads, out_features, bias=False) if residual else None
        self.pooling = pooling
        self.pool_score = nn.Linear(out_features, 1) if pooling == "attention" else None
        self.act = {"elu": F.elu, "relu": F.relu, "gelu": F.gelu}[activation]

    def forward(self, x: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """x: (B, N, F_in), adjacency: (B, N, N) -> (B, N, out_features)"""
        h = self.layer1(x, adjacency)
        if self.res1 is not None:
            h = h + self.res1(x)
        h = self.act(h)
        z = self.layer2(h, adjacency)
        if self.res2 is not None:
            z = z + self.res2(h)
        return self.act(z)

    def pool_to_sequence_token(self, z: torch.Tensor, adjacency: torch.Tensor | None = None) -> torch.Tensor:
        """Pool node embeddings into one token per window, for the Mamba block.

        Only active nodes (those with a self-loop) count, so the many silent
        IDs of a global vocabulary don't dilute the token. Without an
        adjacency every node counts. z: (B, N, d) -> (B, d)
        """
        if adjacency is None:
            active = torch.ones(z.shape[:2], dtype=torch.bool, device=z.device)
        else:
            active = torch.diagonal(adjacency, dim1=-2, dim2=-1).gt(0)  # (B, N)
        if self.pool_score is not None:
            scores = self.pool_score(z).squeeze(-1).masked_fill(~active, torch.finfo(z.dtype).min)
            weights = torch.softmax(scores, dim=-1) * active
            return (weights.unsqueeze(-1) * z).sum(dim=1)
        w = active.to(z.dtype).unsqueeze(-1)
        return (z * w).sum(dim=1) / w.sum(dim=1).clamp(min=1.0)
