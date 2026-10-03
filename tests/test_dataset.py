import torch

from grama.data.build import build_from_streams, synthetic_streams
from grama.data.dataset import dataset_from_payload

CLASSES = ["benign", "DoS", "spoofing-GAS", "spoofing-RPM", "spoofing-SPEED", "spoofing-STEERING_WHEEL"]
SETTINGS = dict(window_size=16, stride=8, seq_len=4, seq_stride=2, test_fraction=0.2,
                max_nodes=64, edge_mode="transition", min_attack_frames=1,
                max_rows_per_class=None, injection={"enabled": False})
PAYLOAD = build_from_streams(synthetic_streams(CLASSES, rows_per_class=800, seed=0), SETTINGS, CLASSES)


def test_graph_view_shapes_and_self_loops():
    ds = dataset_from_payload(PAYLOAD, "train", view="graph")
    x, adj, y = ds.get_batch(torch.arange(5))
    N = PAYLOAD["meta"]["num_nodes"]
    assert x.shape == (5, 4, N, 10) and adj.shape == (5, 4, N, N) and y.shape == (5,)
    active = x[..., -2] > 0
    diag = torch.diagonal(adj, dim1=-2, dim2=-1) > 0
    assert torch.equal(active, diag)                         # self-loops exactly on active nodes
    assert torch.equal(adj, adj.transpose(-1, -2))           # undirected


def test_edges_only_between_active_nodes():
    for mode in ("transition", "cooccurrence"):
        ds = dataset_from_payload(PAYLOAD, "train", view="graph", edge_mode=mode)
        x, adj, _ = ds.get_batch(torch.arange(3))
        inactive = x[..., -2] == 0
        assert adj[inactive.unsqueeze(-1).expand_as(adj)].sum() == 0


def test_transition_edges_are_a_subset_of_cooccurrence():
    t = dataset_from_payload(PAYLOAD, "test", edge_mode="transition")
    c = t.with_view(edge_mode="cooccurrence")
    _, a_t, _ = t.get_batch(torch.arange(4))
    _, a_c, _ = c.get_batch(torch.arange(4))
    assert (a_t <= a_c).all()


def test_frames_view_and_item_access():
    ds = dataset_from_payload(PAYLOAD, "train", view="frames")
    ids, payload, y = ds.get_batch(torch.tensor([0, 1]))
    assert ids.shape == (2, 4, 16) and payload.shape == (2, 4, 16, 8)
    assert 0.0 <= payload.min() and payload.max() <= 1.0
    single = ds[0]
    assert single[0].shape == (4, 16)
    assert ds.with_view("graph").x is ds.x                   # views share storage
