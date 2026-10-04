"""The ROAD and can-train-and-test readers on the real files, when they are in data/raw (skipped otherwise)."""
from pathlib import Path

import numpy as np
import pytest

from grama.data.can_train_test import cantt_files, read_csv
from grama.data.road import attack_frames, parse_candump, road_files

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw"
ROAD = road_files(ROOT / "road")
CANTT = cantt_files(ROOT / "can-train-and-test")


def _road_labels(capture):
    import json
    meta = json.loads(ROAD.read_bytes(next(n for n in ROAD.names() if n.endswith("attacks/capture_metadata.json"))))
    name = next(n for n in ROAD.names() if n.endswith(f"/{capture}.log"))
    t, ids, payload = parse_candump(ROAD.read_bytes(name))
    return attack_frames(t - t[0], ids, payload, meta[capture]), ids, t - t[0], meta[capture]


@pytest.mark.skipif(not ROAD.names(), reason="ROAD is not in data/raw/road")
@pytest.mark.parametrize("capture,expected", [
    ("correlated_signal_attack_1", 2086), ("correlated_signal_attack_1_masquerade", 2086),
    ("max_speedometer_attack_1", 2443), ("max_engine_coolant_temp_attack", 43), ("fuzzing_attack_1", 591),
])
def test_road_attack_frame_counts(capture, expected):
    mask = _road_labels(capture)[0]
    assert int(mask.sum()) == expected


@pytest.mark.skipif(not ROAD.names(), reason="ROAD is not in data/raw/road")
def test_road_plain_capture_has_half_injected_frames_and_masquerade_all():
    for capture, share in [("max_speedometer_attack_2", 0.5), ("max_speedometer_attack_2_masquerade", 1.0)]:
        mask, ids, t, info = _road_labels(capture)
        lo, hi = info["injection_interval"]
        of_id = (ids == int(info["injection_id"], 16)) & (t >= lo) & (t <= hi)
        assert abs(mask.sum() / of_id.sum() - share) < 0.01


@pytest.mark.skipif(not CANTT.names(), reason="can-train-and-test is not in data/raw/can-train-and-test")
def test_cantt_reads_ids_payloads_and_labels():
    ids, payload, attack = read_csv(CANTT, "can-train-and-test/set_01/train_01/DoS-1.csv")
    assert len(ids) == 90169 and int(attack.sum()) == 9139
    assert payload.shape == (90169, 8) and payload.dtype == np.uint8
    assert ids.max() < 0x800
