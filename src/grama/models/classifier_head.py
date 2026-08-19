"""Dense classification head + the full local GraMa model (GAT -> Mamba -> head)."""
from __future__ import annotations

import torch
import torch.nn as nn

from grama.models.gat_encoder import SpatialTopologicalGAT
from grama.models.mamba_block import MambaBlock


class ClassifierHead(nn.Module):
    def __init__(self, d_model: int, hidden_dim: int, num_classes: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, h_last: torch.Tensor) -> torch.Tensor:
        """h_last: (B, d_model) final hidden state h_W -> (B, num_classes) logits."""
        return self.net(h_last)


class GraMaLocalModel(nn.Module):
    """Full local client model: GAT node encoder -> pooled sequence -> Mamba -> classifier.

    Input is a *sequence of windows*: for each window we have (node_features,
    adjacency); the GAT encodes each window's ECU graph, we pool to one token
    per window, then Mamba processes the resulting token sequence over time
    (Sec 4.1, Phases 2-3).
    """

    def __init__(self, gat_cfg: dict, mamba_cfg: dict, head_cfg: dict):
        super().__init__()
        self.gat = SpatialTopologicalGAT(
            in_features=gat_cfg["in_features"],
            hidden_features=gat_cfg["hidden_features"],
            out_features=gat_cfg["out_features"],
            num_heads=gat_cfg["num_heads"],
            dropout=gat_cfg["dropout"],
            leaky_relu_slope=gat_cfg["leaky_relu_slope"],
            activation=gat_cfg["activation"],
        )
        self.mamba = MambaBlock(
            d_model=mamba_cfg["d_model"],
            d_state=mamba_cfg["d_state"],
            d_conv=mamba_cfg["d_conv"],
            expand=mamba_cfg["expand"],
            dt_rank=mamba_cfg["dt_rank"],
            backend=mamba_cfg["backend"],
        )
        self.head = ClassifierHead(
            d_model=mamba_cfg["d_model"],
            hidden_dim=head_cfg["hidden_dim"],
            num_classes=head_cfg["num_classes"],
            dropout=head_cfg["dropout"],
        )

    def forward(self, node_features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """
        node_features: (B, L, N, F_in) — L windows per sequence, N ECU nodes each
        adjacency:      (B, L, N, N)
        returns: (B, num_classes) logits, using the final timestep's hidden state
        """
        B, L, N, F_in = node_features.shape
        tokens = []
        for t in range(L):
            z = self.gat(node_features[:, t], adjacency[:, t])       # (B, N, d)
            token = self.gat.pool_to_sequence_token(z)                  # (B, d)
            tokens.append(token)
        seq = torch.stack(tokens, dim=1)  # (B, L, d)

        y = self.mamba(seq)  # (B, L, d)
        h_last = y[:, -1, :]  # h_W: final hidden state (eq. Sec 4.1 Phase 3)
        return self.head(h_last)
