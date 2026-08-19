"""Maps CAN traffic windows to a dynamic directed graph G = (V, E, X).

Nodes V = CAN IDs (learned dynamically from data; no fixed ECU vocabulary).
Edges E = temporal message propagation paths — here, co-occurrence of two
CAN IDs within the same sliding window (Sec 4.1, Phase 1 / Fig. 1).

IMPORTANT: The real CICIoV2024 dataset does NOT publish ECU-to-CAN-ID mappings.
Nodes are discovered from the data itself, not from a hardcoded name vocabulary.
This makes the graph truly data-driven and avoids the need for external domain knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from grama.data.preprocess import PAYLOAD_COLS, Window


@dataclass
class CANIDGraph:
    node_features: np.ndarray   # X ∈ R^{|V| x F}, per-CAN-ID aggregated features for this window
    adjacency: np.ndarray         # binary adjacency ∈ {0,1}^{|V| x |V|}
    node_order: list[int]           # CAN ID per row/col index (sorted, for interpretability)


class GraphBuilder:
    """Build CAN traffic graphs with data-driven node vocabulary.
    
    Nodes are discovered from unique CAN IDs in the data (no hardcoded ECU names).
    Edges represent temporal co-occurrence within sliding windows.
    """

    def __init__(self):
        # No fixed vocabulary; learned per-dataset.
        pass

    def build(self, window: Window) -> CANIDGraph:
        """Construct a graph from a single sliding window.
        
        Args:
            window: a Window containing frames and their CAN IDs
            
        Returns:
            CANIDGraph with learned node/edge structure for this window
        """
        frames = window.frames
        can_id_col = "ID"

        # Discover unique CAN IDs in this window (data-driven vocabulary).
        unique_can_ids = sorted(frames[can_id_col].unique())
        if len(unique_can_ids) == 0:
            # Empty window; return degenerate graph.
            return CANIDGraph(
                node_features=np.zeros((0, len(PAYLOAD_COLS) + 2), dtype=np.float32),
                adjacency=np.zeros((0, 0), dtype=np.float32),
                node_order=[],
            )

        n = len(unique_can_ids)
        can_id_to_idx = {cid: i for i, cid in enumerate(unique_can_ids)}

        # Feature dimension: 8 DATA bytes + frame_count + burst_indicator
        feat_dim = len(PAYLOAD_COLS) + 2
        node_features = np.zeros((n, feat_dim), dtype=np.float32)
        counts = np.zeros(n, dtype=np.int32)
        adjacency = np.zeros((n, n), dtype=np.float32)

        active_nodes: set[int] = set()

        # Aggregate features per CAN ID.
        for _, row in frames.iterrows():
            can_id = row[can_id_col]
            idx = can_id_to_idx[can_id]
            active_nodes.add(idx)
            
            # Extract payload bytes.
            payload = np.array(
                [row.get(c, 0.0) for c in PAYLOAD_COLS],
                dtype=np.float32
            )
            node_features[idx, : len(PAYLOAD_COLS)] += payload
            counts[idx] += 1

        # Average pooled features per CAN ID (avoid double-counting).
        nonzero = counts > 0
        node_features[nonzero, :-2] /= counts[nonzero, None]

        # frame_count and burst_indicator (unnormalized, for anomaly signal).
        node_features[:, -2] = counts
        node_features[:, -1] = (counts > counts.mean()).astype(np.float32)  # burst flag

        # Edges: temporal co-occurrence within this window.
        unique_active = sorted(active_nodes)
        for i in unique_active:
            for j in unique_active:
                if i != j:
                    adjacency[i, j] = 1.0

        # Self-loops so GAT attention can attend to the node's own state.
        np.fill_diagonal(adjacency, 1.0)

        return CANIDGraph(
            node_features=node_features,
            adjacency=adjacency,
            node_order=unique_can_ids,
        )
