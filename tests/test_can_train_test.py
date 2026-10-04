"""can-train-and-test reader on a fake zip laid out like the release, and a run end to end."""
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from grama.data.build import build_dataset
from grama.data.can_train_test import CLASSES, FOLDERS, load_can_train_test, pieces
from grama.data.dataset import load_processed
from grama.experiments.report import make_report
from grama.experiments.runner import Experiment, RunSpec

CAR_A = np.array([0x0C9, 0x0F1, 0x1A1, 0x1E9, 0x2C3, 0x3C9])
CAR_B = np.array([0x0C9, 0x110, 0x2F9, 0x3D1, 0x4C1, 0x500])          # the "unknown" car, one ID shared
SETTINGS = {"set": "set_01", "context_rows": 300, "max_rows": 1500, "benign_rows": 1200, "benign_chunks": 2}


def _csv(ids_pool, n, attack_at=None, seed=0):
    rng = np.random.default_rng(seed)
    ids = ids_pool[np.arange(n) % len(ids_pool)]
    data = ["".join(f"{b:02X}" for b in rng.integers(0, 256, 1 + i % 8)) for i in range(n)]
    attack = np.zeros(n, dtype=int)
    if attack_at is not None:
        lo, hi = attack_at
        attack[lo:hi:4] = 1
        ids = ids.copy()
        ids[attack == 1] = 0x000
        for i in np.flatnonzero(attack):
            data[i] = "0000000000000000"
    return pd.DataFrame({"timestamp": 1672531200 + np.arange(n) / 2000,
                         "arbitration_id": [f"{v:03X}" for v in ids], "data_field": data,
                         "attack": attack}).to_csv(index=False)


def write_fake_cantt(path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("can-train-and-test/README.md", "fake")
        for split, folder in FOLDERS.items():
            car = CAR_B if "unknown_vehicle" in split else CAR_A
            for k, name in enumerate(["DoS-1", "rpm-1", "attack-free-1"]):
                at = None if name.startswith("attack-free") else (2000, 2400)
                zf.writestr(f"can-train-and-test/set_01/{folder}/{name}.csv", _csv(car, 5000, at, seed=k))


@pytest.fixture(scope="module")
def fake_cantt(tmp_path_factory):
    root = tmp_path_factory.mktemp("cantt")
    write_fake_cantt(root / "can-train-and-test.zip")
    return root


def test_pieces_cut_attack_files_and_chunk_attack_free_ones():
    attack = np.zeros(10000, dtype=int)
    attack[5000:5100] = 1
    assert pieces(attack, SETTINGS) == [(4700, 5400)]
    assert pieces(attack, {**SETTINGS, "max_rows": 500}) == [(4700, 5200)]
    chunks = pieces(np.zeros(10000, dtype=int), SETTINGS)
    assert chunks == [(0, 600), (9400, 10000)]


def test_splits_come_from_the_folders(fake_cantt):
    splits = load_can_train_test(fake_cantt, SETTINGS)
    assert set(splits) == set(FOLDERS)
    for ss in splits.values():
        assert sum(int(s.frame_labels.sum()) for s in ss) == 2 * 100       # two attack files, 100 attack frames each
        assert {s.name.split("/")[-1].split("#")[0] for s in ss} == {"DoS-1", "rpm-1", "attack-free-1"}


def test_build_end_to_end_with_four_test_sets(fake_cantt, tmp_path):
    cfg = {"dataset": {"processed_dir": str(tmp_path)},
           "build": {"window_size": 16, "stride": 8, "seq_len": 4, "seq_stride": 2, "max_nodes": 64,
                     "edge_mode": "transition", "min_attack_frames": 1},
           "can_train_test": {"raw_dir": str(fake_cantt), "classes": CLASSES, "build": SETTINGS}}
    meta = load_processed(build_dataset(cfg, source="can_train_test"))["meta"]
    assert meta["extra_tests"] == ["unknown_vehicle", "unknown_attack", "unknown_vehicle_and_attack"]
    assert meta["num_nodes"] == len(CAR_A) + 2                       # car A's IDs, the attack ID 0x000, "other"
    share = meta["other_node_share"]
    assert share["train"] == 0 and share["unknown_vehicle"] > 0.6   # car B's IDs are new, except one
    assert all(c[1] > 0 for c in meta["class_counts"].values())


def test_runs_report_the_extra_test_sets(fake_cantt, tmp_path):
    exp = Experiment("cantt1", device="cpu", results_dir=tmp_path / "results")
    exp.data_cfg["dataset"]["processed_dir"] = str(tmp_path / "processed")
    exp.data_cfg["build"].update(window_size=16, stride=8, seq_len=4, seq_stride=2)
    exp.data_cfg["can_train_test"] = {**exp.data_cfg["can_train_test"], "raw_dir": str(fake_cantt),
                                      "build": {**exp.data_cfg["can_train_test"]["build"], **SETTINGS}}
    exp.sim.update(num_clients=4, clients_per_round=3, num_rounds=2, local_epochs=1)
    exp.prepare_data()
    specs = [RunSpec("grama", "hdbscan", 0.5, None, 0.0, 0), RunSpec("grama", "fedavg", 0.5, None, 0.0, 0),
             RunSpec("cnn_bigru", "fedavg", 0.5, None, 0.0, 0),
             RunSpec("grama", "hdbscan", 0.5, "targeted_flip", 0.4, 0)]
    with exp.runs_path.open("w") as f:
        for spec in specs:
            rec = exp.run_one(spec)
            assert set(rec["tests"]) == {"unknown_vehicle", "unknown_attack", "unknown_vehicle_and_attack"}
            assert len(rec["final"]["confusion_matrix"]) == 2
            f.write(json.dumps(rec) + "\n")
    data = json.loads((exp.out_dir / "dataset.json").read_text())
    assert data["source"] == "can_train_test" and "other_node_share" in data
    summary = make_report(exp.out_dir).read_text()
    assert "Other test sets" in summary and "Unknown car, unknown attacks" in summary
    assert "can-train-and-test" in summary and "train_01 trains" in summary
