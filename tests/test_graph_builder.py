import pandas as pd

from grama.data.graph_builder import GraphBuilder
from grama.data.preprocess import Window

ECU_NODES = ["ENGINE", "TRANSMISSION", "BRAKES", "STEERING", "ADAS", "GATEWAY", "INFOTAINMENT", "BODY_CONTROL"]


def make_window() -> Window:
    frames = pd.DataFrame({
        "can_id": ["0x0C4", "0x0D0", "0x0C4", "0x999"],  # 0x999 unknown -> unknown_ecu_bucket
        "dlc": [8, 8, 8, 4],
        "delta_t": [0.001, 0.002, 0.001, 0.005],
        **{f"d{i}": [0.1 * i, 0.2 * i, 0.15 * i, 0.05 * i] for i in range(8)},
        "label": [0, 0, 0, 0],
    })
    return Window(frames=frames, can_ids=frames["can_id"].unique(), label=0)


def test_graph_shapes():
    builder = GraphBuilder(ecu_nodes=ECU_NODES)
    graph = builder.build(make_window())

    n = len(ECU_NODES)
    assert graph.node_features.shape == (n, 11)  # 8 payload + dlc + delta_t + frame_count
    assert graph.adjacency.shape == (n, n)
    assert graph.node_order == ECU_NODES


def test_adjacency_has_self_loops():
    builder = GraphBuilder(ecu_nodes=ECU_NODES)
    graph = builder.build(make_window())
    assert (graph.adjacency.diagonal() == 1.0).all()


def test_active_nodes_are_connected():
    builder = GraphBuilder(ecu_nodes=ECU_NODES)
    graph = builder.build(make_window())

    engine_idx = ECU_NODES.index("ENGINE")
    steering_idx = ECU_NODES.index("STEERING")
    # Both ECUs appeared in the same window -> co-occurrence edge should exist.
    assert graph.adjacency[engine_idx, steering_idx] == 1.0
    assert graph.adjacency[steering_idx, engine_idx] == 1.0


def test_unknown_can_id_routes_to_fallback_bucket():
    builder = GraphBuilder(ecu_nodes=ECU_NODES, unknown_ecu_bucket="GATEWAY")
    graph = builder.build(make_window())
    gateway_idx = ECU_NODES.index("GATEWAY")
    # 0x999 is unknown and should be bucketed into GATEWAY, giving it a nonzero frame_count.
    frame_count_feature_idx = -1
    assert graph.node_features[gateway_idx, frame_count_feature_idx] == 1
