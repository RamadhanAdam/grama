"""Maps CAN traffic windows to a dynamic directed graph G = (V, E, X).

Nodes V = ECUs (fixed vocabulary from config/model.yaml: graph.ecu_nodes).
Edges E = historical message propagation paths — here, co-occurrence of two
ECUs' CAN IDs within the same sliding window (Sec 4.1, Phase 1 / Fig. 1).

NOTE: the CAN-ID -> ECU mapping below is illustrative. Replace
`DEFAULT_CAN_ID_TO_ECU` with the actual mapping once the real CIC-IoV2024
CAN ID space is known — arbitration IDs are dataset/vehicle-specific.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from grama.data.preprocess import PAYLOAD_COLS, Window

# Placeholder mapping — extend/replace once real CAN IDs are confirmed.
DEFAULT_CAN_ID_TO_ECU: dict[str, str] = {
    "0x0C4": "ENGINE",
    "0x0D0": "STEERING",
    "0x000": "GATEWAY",       # DoS dominant-ID target frames route through gateway
    "0x1A0": "TRANSMISSION",
    "0x2B3": "BRAKES",
    "0x3F1": "ADAS",
    "0x4E2": "INFOTAINMENT",
    "0x5C7": "BODY_CONTROL",
}


@dataclass
class ECUGraph:
    node_features: np.ndarray   # X ∈ R^{|V| x F}, per-ECU aggregated features for this window
    adjacency: np.ndarray         # binary adjacency ∈ {0,1}^{|V| x |V|}
    node_order: list[str]           # ECU name per row/col index, for interpretability


class GraphBuilder:
    def __init__(
        self,
        ecu_nodes: list[str],
        can_id_to_ecu: dict[str, str] | None = None,
        unknown_ecu_bucket: str = "GATEWAY",
    ):
        self.ecu_nodes = list(ecu_nodes)
        self.node_index = {name: i for i, name in enumerate(self.ecu_nodes)}
        self.can_id_to_ecu = can_id_to_ecu or DEFAULT_CAN_ID_TO_ECU
        self.unknown_ecu_bucket = unknown_ecu_bucket

    def _ecu_for_can_id(self, can_id) -> str:
        key = str(can_id)
        return self.can_id_to_ecu.get(key, self.unknown_ecu_bucket)

    def build(self, window: Window) -> ECUGraph:
        n = len(self.ecu_nodes)
        feat_dim = len(PAYLOAD_COLS) + 3  # payload bytes + dlc + delta_t + frame_count
        node_features = np.zeros((n, feat_dim), dtype=np.float32)
        counts = np.zeros(n, dtype=np.int32)
        adjacency = np.zeros((n, n), dtype=np.float32)

        frames = window.frames
        active_nodes: list[int] = []

        for _, row in frames.iterrows():
            ecu = self._ecu_for_can_id(row.get("can_id"))
            idx = self.node_index.get(ecu)
            if idx is None:
                continue
            active_nodes.append(idx)
            payload = np.array([row.get(c, 0.0) for c in PAYLOAD_COLS], dtype=np.float32)
            dlc = float(row.get("dlc", 0.0))
            delta_t = float(row.get("delta_t", 0.0))
            node_features[idx, : len(PAYLOAD_COLS)] += payload
            node_features[idx, len(PAYLOAD_COLS)] += dlc
            node_features[idx, len(PAYLOAD_COLS) + 1] += delta_t
            counts[idx] += 1

        # Average pooled features per ECU (avoid double-counting bursty ECUs).
        nonzero = counts > 0
        node_features[nonzero, :-1] /= counts[nonzero, None]
        node_features[:, -1] = counts  # frame_count feature, unnormalized on purpose (burst signal)

        # Edge = temporal co-occurrence within this window (message propagation proxy).
        unique_active = sorted(set(active_nodes))
        for i in unique_active:
            for j in unique_active:
                if i != j:
                    adjacency[i, j] = 1.0
        # Self-loops so GAT attention can attend to the node's own prior state.
        np.fill_diagonal(adjacency, 1.0)

        return ECUGraph(node_features=node_features, adjacency=adjacency, node_order=self.ecu_nodes)
