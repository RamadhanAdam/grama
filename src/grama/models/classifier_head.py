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

    Input is a sequence of L windows. The GAT encodes each window's CAN-ID
    graph, the nodes are pooled into one token per window, and Mamba reads
    the token sequence over time (Sec 4.1, Phases 2-3).

    With num_nodes given, each CAN ID also gets a learned embedding that is
    appended to its features, so the GAT knows which ID a node is (the
    vocabulary is fixed per dataset). gat_cfg["node_embedding_dim"] = 0 turns
    this off. mamba_cfg["temporal"] can swap Mamba for a GRU or for nothing
    (last window only), for the ablation study.
    """

    def __init__(self, gat_cfg: dict, mamba_cfg: dict, head_cfg: dict, num_nodes: int | None = None):
        super().__init__()
        emb_dim = gat_cfg.get("node_embedding_dim", 0) if num_nodes else 0
        self.node_embedding = nn.Embedding(num_nodes, emb_dim) if emb_dim else None
        self.gat = SpatialTopologicalGAT(
            in_features=gat_cfg["in_features"] + emb_dim,
            hidden_features=gat_cfg["hidden_features"],
            out_features=gat_cfg["out_features"],
            num_heads=gat_cfg["num_heads"],
            dropout=gat_cfg["dropout"],
            leaky_relu_slope=gat_cfg["leaky_relu_slope"],
            activation=gat_cfg["activation"],
            residual=gat_cfg.get("residual", True),
            pooling=gat_cfg.get("pooling", "attention"),
        )
        self.temporal = mamba_cfg.get("temporal", "mamba")
        d = mamba_cfg["d_model"]
        if self.temporal == "mamba":
            self.mamba = MambaBlock(
                d_model=d,
                d_state=mamba_cfg["d_state"],
                d_conv=mamba_cfg["d_conv"],
                expand=mamba_cfg["expand"],
                dt_rank=mamba_cfg["dt_rank"],
                backend=mamba_cfg["backend"],
            )
        elif self.temporal == "gru":
            self.gru = nn.GRU(d, d, batch_first=True)
        elif self.temporal != "none":
            raise ValueError(f"temporal must be mamba, gru or none, got {self.temporal!r}")
        self.head = ClassifierHead(
            d_model=d,
            hidden_dim=head_cfg["hidden_dim"],
            num_classes=head_cfg["num_classes"],
            dropout=head_cfg["dropout"],
        )

    def forward(self, node_features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """
        node_features: (B, L, N, F_in), L windows per sequence, N CAN-ID nodes each
        adjacency:      (B, L, N, N)
        returns: (B, num_classes) logits from the final timestep's hidden state
        """
        if self.temporal == "none":
            node_features, adjacency = node_features[:, -1:], adjacency[:, -1:]
        B, L, N, F_in = node_features.shape
        # All B*L windows go through the GAT in one call.
        x = node_features.reshape(B * L, N, F_in)
        adj = adjacency.reshape(B * L, N, N)
        if self.node_embedding is not None:
            x = torch.cat([x, self.node_embedding.weight.expand(B * L, -1, -1)], dim=-1)
        z = self.gat(x, adj)                                     # (B*L, N, d)
        seq = self.gat.pool_to_sequence_token(z, adj).reshape(B, L, -1)

        if self.temporal == "mamba":
            y = self.mamba(seq)       # (B, L, d)
        elif self.temporal == "gru":
            y, _ = self.gru(seq)
        else:
            y = seq
        h_last = y[:, -1, :]          # h_W, the final hidden state (Sec 4.1 Phase 3)
        return self.head(h_last)
