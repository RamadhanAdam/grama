import pandas as pd

from grama.data.graph_builder import GraphBuilder
from grama.data.preprocess import Window


def make_window() -> Window:
    """Create a test window with CAN IDs and DATA_0..7 columns (real schema)."""
    frames = pd.DataFrame({
        "ID": [0x0C4, 0x0D0, 0x0C4, 0x999],  # Unique CAN IDs
        **{f"DATA_{i}": [0.1 * i, 0.2 * i, 0.15 * i, 0.05 * i] for i in range(8)},
        "label": [0, 0, 0, 0],
    })
    return Window(frames=frames, can_ids=frames["ID"].unique(), label=0)


def test_graph_shapes():
    """Graph should have one node per unique CAN ID (data-driven vocabulary)."""
    builder = GraphBuilder()
    graph = builder.build(make_window())

    n_unique_ids = 4  # [0x0C4, 0x0D0, 0x999] but 0x0C4 appears twice -> 3 unique, 4 frames
    n_unique_ids_corrected = 3  # Actually 3 unique CAN IDs
    assert graph.node_features.shape == (n_unique_ids_corrected, 10)  # 8 payload + frame_count + burst_flag
    assert graph.adjacency.shape == (n_unique_ids_corrected, n_unique_ids_corrected)
    assert len(graph.node_order) == n_unique_ids_corrected


def test_adjacency_has_self_loops():
    """All nodes should have self-loops."""
    builder = GraphBuilder()
    graph = builder.build(make_window())
    assert (graph.adjacency.diagonal() == 1.0).all()


def test_active_nodes_are_connected():
    """All CAN IDs in the window should be pairwise connected (co-occurrence)."""
    builder = GraphBuilder()
    graph = builder.build(make_window())

    # All 3 unique CAN IDs should be in the graph, so we expect a fully connected subgraph.
    for i in range(len(graph.node_order)):
        for j in range(len(graph.node_order)):
            # All pairs should have edges (clique in this window).
            assert graph.adjacency[i, j] == 1.0


def test_data_driven_vocabulary():
    """Graph vocabulary should be discovered from the data, not hardcoded."""
    builder = GraphBuilder()
    graph = builder.build(make_window())

    # node_order should contain the actual CAN IDs present in the data (sorted).
    expected_ids = sorted([0x0C4, 0x0D0, 0x999])
    assert graph.node_order == expected_ids


def test_frame_count_feature():
    """Frame count should reflect how many times each CAN ID appeared."""
    builder = GraphBuilder()
    graph = builder.build(make_window())

    frame_count_idx = -2  # Second-to-last feature (before burst_flag)
    # 0x0C4 appears twice, others appear once.
    can_id_to_count = {0x0C4: 2, 0x0D0: 1, 0x999: 1}

    for idx, can_id in enumerate(graph.node_order):
        expected_count = can_id_to_count[can_id]
        assert graph.node_features[idx, frame_count_idx] == expected_count
