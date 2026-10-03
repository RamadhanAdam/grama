"""Window-sequence dataset read by the federated clients.

The builder (grama.data.build) stores one row per *window*, not per sequence:

    x            (num_windows, N, F)   node features per CAN-ID node
    frame_ids    (num_windows, W)      node index of every frame in the window
    frame_bytes  (num_windows, W, 8)   raw payload bytes, for the frame-level baseline
    starts       (num_sequences,)      index of each sequence's first window
    labels       (num_sequences,)      class of each sequence (its last window)

A sequence is the L consecutive windows starting at starts[i]. Building
sequences on the fly keeps memory at one copy of each window even though
consecutive sequences overlap, and get_batch() does it for a whole batch
with a single indexing operation, which is much faster than a DataLoader
calling __getitem__ per sample.

Two views of the same data:
  "graph"  -> (node_features (B,L,N,F), adjacency (B,L,N,N), labels)  for GraMa
  "frames" -> (frame_ids (B,L,W), frame_bytes (B,L,W,8), labels)       for the CNN-BiGRU baseline
"""
from __future__ import annotations

from pathlib import Path

import torch
from torch.utils.data import Dataset

EDGE_MODES = ("cooccurrence", "transition")


class WindowSequenceDataset(Dataset):
    def __init__(
        self,
        x: torch.Tensor,
        frame_ids: torch.Tensor,
        frame_bytes: torch.Tensor,
        starts: torch.Tensor,
        labels: torch.Tensor,
        seq_len: int,
        edge_mode: str = "cooccurrence",
        view: str = "graph",
        count_col: int = -2,
    ):
        if edge_mode not in EDGE_MODES:
            raise ValueError(f"edge_mode must be one of {EDGE_MODES}, got {edge_mode!r}")
        if view not in ("graph", "frames"):
            raise ValueError(f"view must be 'graph' or 'frames', got {view!r}")
        self.x = x
        self.frame_ids = frame_ids
        self.frame_bytes = frame_bytes
        self.starts = starts.long()
        self.labels = labels.long()
        self.seq_len = seq_len
        self.edge_mode = edge_mode
        self.view = view
        self.count_col = count_col
        self.num_nodes = x.shape[1]
        self._offsets = torch.arange(seq_len, device=self.starts.device)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        batch = self.get_batch(torch.tensor([idx]))
        return tuple(t[0] for t in batch)

    def to(self, device) -> "WindowSequenceDataset":
        """Move the dataset to a device. On a GPU this removes per-batch copies."""
        for name in ("x", "frame_ids", "frame_bytes", "starts", "labels", "_offsets"):
            setattr(self, name, getattr(self, name).to(device))
        return self

    def with_view(self, view: str | None = None, edge_mode: str | None = None) -> "WindowSequenceDataset":
        """Same data, other view or edge type. Tensors are shared, not copied."""
        return WindowSequenceDataset(
            self.x, self.frame_ids, self.frame_bytes, self.starts, self.labels,
            self.seq_len, edge_mode or self.edge_mode, view or self.view, self.count_col,
        )

    def get_batch(self, idx: torch.Tensor) -> tuple[torch.Tensor, ...]:
        idx = torch.as_tensor(idx, dtype=torch.long, device=self.starts.device)
        win = self.starts[idx].unsqueeze(1) + self._offsets  # (B, L)
        y = self.labels[idx]
        if self.view == "frames":
            ids = self.frame_ids[win].long()                   # (B, L, W)
            payload = self.frame_bytes[win].float() / 255.0    # (B, L, W, 8)
            return ids, payload, y
        x = self.x[win]                                        # (B, L, N, F)
        return x, self._adjacency(win, x), y

    def _adjacency(self, win: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """Edges of each window graph. Self-loops only on nodes that sent a frame."""
        active = x[..., self.count_col] > 0                    # (B, L, N)
        if self.edge_mode == "cooccurrence":
            # Sec 4.1 Phase 1: two IDs seen in the same window share an edge.
            return (active.unsqueeze(-1) & active.unsqueeze(-2)).float()

        # "transition": an edge between IDs that follow each other on the bus.
        B, L = win.shape
        N = self.num_nodes
        ids = self.frame_ids[win].long().reshape(B * L, -1)    # (B*L, W)
        flat = torch.zeros(B * L, N * N, device=x.device)
        flat.scatter_(1, ids[:, :-1] * N + ids[:, 1:], 1.0)
        adj = flat.reshape(B, L, N, N)
        adj = torch.maximum(adj, adj.transpose(-1, -2))
        eye = torch.diag_embed(active.float())
        return torch.maximum(adj, eye)


def load_processed(path: str | Path) -> dict:
    """Load a file written by grama.data.build.save_processed()."""
    return torch.load(path, map_location="cpu", weights_only=False)


def dataset_from_payload(payload: dict, split: str, view: str = "graph",
                         edge_mode: str | None = None) -> WindowSequenceDataset:
    meta = payload["meta"]
    if split not in payload["splits"]:
        raise KeyError(f"No '{split}' split in the processed file. Rebuild the dataset.")
    s = payload["splits"][split]
    return WindowSequenceDataset(
        x=s["x"], frame_ids=s["frame_ids"], frame_bytes=s["frame_bytes"],
        starts=s["starts"], labels=s["labels"], seq_len=meta["seq_len"],
        edge_mode=edge_mode or meta["edge_mode"], view=view,
    )
