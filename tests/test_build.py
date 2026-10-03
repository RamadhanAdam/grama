import numpy as np
import pytest
import torch

from grama.data.build import (
    Stream,
    build_from_streams,
    canonical,
    class_index,
    fit_vocabulary,
    inject_into_benign,
    map_ids,
    synthetic_streams,
    window_stream,
)

CLASSES = ["benign", "DoS", "spoofing-GAS", "spoofing-RPM", "spoofing-SPEED", "spoofing-STEERING_WHEEL"]
SETTINGS = dict(window_size=16, stride=8, seq_len=4, seq_stride=2, test_fraction=0.2,
                max_nodes=64, edge_mode="transition", min_attack_frames=1,
                max_rows_per_class=None, injection={"enabled": False})


@pytest.mark.parametrize("name,expected", [
    ("decimal_benign", 0), ("decimal_DoS", 1), ("decimal_spoofing-GAS", 2),
    ("decimal_spoofing-STEERING_WHEEL", 5), ("STEERING_WHEEL", 5), ("RPM", 3), ("BENIGN", 0),
])
def test_file_names_map_to_classes(name, expected):
    assert class_index(name, CLASSES) == expected


def test_unknown_name_maps_to_none():
    assert class_index("decimal_replay", CLASSES) is None
    assert canonical("hexadecimal_spoofing-SPEED") == "speed"


def test_vocabulary_keeps_most_frequent_and_maps_rest_to_other():
    ids = np.array([5, 5, 5, 7, 7, 9])
    vocab = fit_vocabulary(ids, max_nodes=3)  # 2 real nodes + "other"
    assert vocab.tolist() == [5, 7]
    assert map_ids(np.array([5, 7, 9, 42]), vocab).tolist() == [0, 1, 2, 2]


def test_window_features_are_shares_and_means():
    node_ids = np.array([0, 1, 0, 1, 0, 0, 2, 2])
    payload = np.tile(np.linspace(0, 1, 8, dtype=np.float32), (8, 1))
    out = window_stream(node_ids, payload, (payload * 255).astype(np.uint8), np.zeros(8, dtype=np.int64),
                        window_size=4, stride=4, num_nodes=3, num_classes=2)
    x = out["x"]
    assert x.shape == (2, 3, 10)
    np.testing.assert_allclose(x[..., -2].sum(axis=1), 1.0)       # frame shares sum to 1 per window
    np.testing.assert_allclose(x[0, 0, :8], payload[0])             # mean payload of node 0
    assert x[0, 2, -2] == 0                                         # node 2 silent in window 0
    assert out["frame_ids"].tolist() == [[0, 1, 0, 1], [0, 0, 2, 2]]


def test_window_label_needs_attack_frames():
    labels = np.array([0, 0, 0, 0, 0, 0, 3, 0])
    out = window_stream(np.zeros(8, dtype=np.int64), np.zeros((8, 8), np.float32), np.zeros((8, 8), np.uint8),
                        labels, window_size=4, stride=4, num_nodes=1, num_classes=4)
    assert out["window_labels"].tolist() == [0, 3]


def test_build_splits_in_time_and_balances_classes():
    streams = synthetic_streams(CLASSES, rows_per_class=1200, seed=0)
    payload = build_from_streams(streams, SETTINGS, CLASSES)
    meta, splits = payload["meta"], payload["splits"]
    assert meta["num_classes"] == 6 and meta["in_features"] == 10
    for split in ("train", "test"):
        s = splits[split]
        assert s["x"].shape[1:] == (meta["num_nodes"], 10)
        assert s["frame_ids"].shape[1] == SETTINGS["window_size"]
        assert int(s["starts"].max()) + SETTINGS["seq_len"] <= len(s["x"])
        assert set(s["labels"].tolist()) == set(range(6))
    assert sum(meta["class_counts"]["train"]) > 3 * sum(meta["class_counts"]["test"])


def test_injection_keeps_attack_ratio():
    rng = np.random.default_rng(0)
    attack = Stream("a", 2, np.full(300, 7), np.zeros((300, 8), np.uint8), np.full(300, 2))
    benign = Stream("b", 0, np.arange(1000) % 5, np.ones((1000, 8), np.uint8), np.zeros(1000, dtype=np.int64))
    mixed = inject_into_benign(attack, benign, ratio=0.3, rng=rng)
    assert len(mixed) == 1000
    assert (mixed.frame_labels == 2).sum() == 300
    assert (mixed.ids[mixed.frame_labels == 2] == 7).all()


def test_saved_payload_is_torch():
    streams = synthetic_streams(CLASSES, rows_per_class=600, seed=1)
    payload = build_from_streams(streams, SETTINGS, CLASSES)
    assert isinstance(payload["splits"]["train"]["x"], torch.Tensor)
    assert payload["splits"]["train"]["frame_bytes"].dtype == torch.uint8


def test_block_split_puts_every_segment_in_both_splits():
    from grama.data.build import split_stream
    n = 10_000
    labels = np.zeros(n, dtype=np.int64)
    s = Stream("x", 0, np.repeat(np.arange(4), n // 4), np.zeros((n, 8), np.uint8), labels)  # 4 segments
    train, test = split_stream(s, {"split": "blocks", "block_rows": 500, "test_fraction": 0.2})
    test_ids = set(np.concatenate([p.ids for p in test]).tolist())
    train_ids = set(np.concatenate([p.ids for p in train]).tolist())
    assert test_ids == train_ids == {0, 1, 2, 3}
    assert sum(len(p) for p in test) == 2000 and sum(len(p) for p in train) == 8000
    assert all(len(p) == 500 for p in test)                  # test pieces are single blocks

    t_train, t_test = split_stream(s, {"split": "temporal", "test_fraction": 0.2})
    assert set(t_test[0].ids.tolist()) == {3}                 # a time split only tests the last segment
