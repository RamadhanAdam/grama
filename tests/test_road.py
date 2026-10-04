"""ROAD reader on fake captures laid out like road.zip: labels, split, and a run end to end."""
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from grama.data.build import build_dataset
from grama.data.dataset import load_processed
from grama.data.rawfiles import RawFiles, hex_payloads
from grama.data.road import (
    CLASSES,
    attack_frames,
    capture_class,
    instance_of,
    line_chunks,
    load_road,
    parse_candump,
)

RATE = 400                                      # frames per second in the fake captures
IDS = np.array([0x0D0, 0x0F4, 0x1A0, 0x28B, 0x354, 0x4E7, 0x5E1, 0x6E0])
DLC = {0x1A0: 4}                                # one ID with a short payload, as on the real bus
SETTINGS = {"test_instance": 3, "test_ambient": ["ambient_dyno_drive_basic_short"],
            "context_seconds": 1.0, "ambient_rows": 2000, "ambient_chunks": 2}


def _benign(seconds, seed):
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    ids = IDS[np.arange(n) % len(IDS)]
    payload = rng.integers(0x10, 0xF0, (n, 8)).astype(np.uint8)  # never FF or 0C: no real frame looks injected
    return t, ids, payload


def _lines(t, ids, payload):
    out = []
    for ti, i, p in zip(t, ids, payload):
        p = bytes(p[: DLC.get(int(i), 8)])
        out.append(f"({1110000000 + ti:.6f}) can0 {int(i):03X}#{p.hex().upper()}")
    return "\n".join(out) + "\n"


def _inject(t, ids, payload, info, masquerade, seed):
    """Add (or, for a masquerade, overwrite) the injected frames. Returns the capture and the number injected."""
    lo, hi = info["injection_interval"]
    inside = (t >= lo) & (t + 0.0001 <= hi)          # injected frames go 0.1 ms after a real one
    pattern = info["injection_data_str"]
    if info["injection_id"] == "XXX":
        rng = np.random.default_rng(seed)
        when = t[inside][::5] + 0.0001
        new_ids = rng.integers(0x700, 0x7FF, len(when))
        new_payload = np.full((len(when), 8), 0xFF, np.uint8)
    else:
        target = int(info["injection_id"], 16)
        real = ((t >= lo) & (t <= hi) if masquerade else inside) & (ids == target)
        new_payload = payload[real].copy()
        for b in range(8):
            if "X" not in pattern[2 * b: 2 * b + 2]:
                new_payload[:, b] = int(pattern[2 * b: 2 * b + 2], 16)
        if masquerade:
            payload = payload.copy()
            payload[real] = new_payload
            return t, ids, payload, int(real.sum())
        when = t[real] + 0.0001
        new_ids = np.full(len(when), target)
    order = np.argsort(np.concatenate([t, when]), kind="stable")
    return (np.concatenate([t, when])[order], np.concatenate([ids, new_ids])[order],
            np.concatenate([payload, new_payload])[order], len(when))


CAPTURES = {
    "fuzzing_attack": {"injection_id": "XXX", "injection_data_str": "FFFFFFFFFFFFFFFF", "masq": False},
    "correlated_signal_attack": {"injection_id": "0x6e0", "injection_data_str": "595945450000FFFF", "masq": True},
    "max_speedometer_attack": {"injection_id": "0xd0", "injection_data_str": "XXXXXXXXXXFFXXXX", "masq": True},
    "reverse_light_on_attack": {"injection_id": "0xd0", "injection_data_str": "XXXX0CXXXXXXXXXX", "masq": True},
}


def write_fake_road(root, zipped=False):
    """A small ROAD-like release. Returns {capture: number of injected frames}."""
    files, meta, injected = {}, {}, {}
    for name, seconds, seed in [("ambient_dyno_drive_basic_long", 12, 1), ("ambient_dyno_drive_basic_short", 8, 2),
                                ("ambient_highway_street_driving_long", 10, 3)]:
        files[f"road/ambient/{name}.log"] = _lines(*_benign(seconds, seed))
    seed = 10
    for base, c in CAPTURES.items():
        for inst in (1, 2, 3):
            for masq in ([False, True] if c["masq"] else [False]):
                name = f"{base}_{inst}" + ("_masquerade" if masq else "")
                info = {"injection_id": c["injection_id"], "injection_data_str": c["injection_data_str"],
                        "injection_interval": [3.0, 6.0], "modified": masq, "elapsed_sec": 10.0}
                t, ids, payload, k = _inject(*_benign(10, seed), info, masq, seed)
                files[f"road/attacks/{name}.log"] = _lines(t, ids, payload)
                meta[name], injected[name] = info, k
                seed += 1
    for masq in (False, True):
        name = "max_engine_coolant_temp_attack" + ("_masquerade" if masq else "")
        info = {"injection_id": "0x4e7", "injection_data_str": "XXXXXXXXXXFFXXXX",
                "injection_interval": [4.0, 8.0], "modified": masq, "elapsed_sec": 10.0}
        t, ids, payload, k = _inject(*_benign(10, 99), info, masq, 99)
        files[f"road/attacks/{name}.log"] = _lines(t, ids, payload)
        meta[name], injected[name] = info, k
    files["road/attacks/accelerator_attack_drive_1.log"] = _lines(*_benign(6, 7))
    meta["accelerator_attack_drive_1"] = {"injection_id": None, "injection_data_str": None,
                                          "injection_interval": None, "modified": False}
    files["road/attacks/capture_metadata.json"] = json.dumps(meta)

    root.mkdir(parents=True, exist_ok=True)
    if zipped:
        with zipfile.ZipFile(root / "road.zip", "w", zipfile.ZIP_DEFLATED) as zf:
            for name, text in files.items():
                zf.writestr(name, text)
            zf.writestr("__MACOSX/road/._readme.md", "junk")
    else:
        for name, text in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text)
    return injected


@pytest.fixture(scope="module")
def fake_road(tmp_path_factory):
    root = tmp_path_factory.mktemp("road")
    injected = write_fake_road(root, zipped=True)
    return root, injected


# ----------------------------------------------------------------------------- parsing and labels

def test_candump_lines_parse_with_short_payloads():
    t, ids, payload = parse_candump(b"(1110000000.000001) can0 5E1#893FE00B0A000080\n"
                                    b"(1110000000.000500) can0 1A0#0102\n")
    assert ids.tolist() == [0x5E1, 0x1A0]
    assert payload[0].tolist() == [0x89, 0x3F, 0xE0, 0x0B, 0x0A, 0x00, 0x00, 0x80]
    assert payload[1].tolist() == [1, 2, 0, 0, 0, 0, 0, 0]
    assert np.allclose(t - t[0], [0, 0.000499], atol=1e-6)
    assert hex_payloads(pd.Series(["", None, "FF"])).tolist()[2][0] == 255


def test_attack_rule_uses_interval_id_and_fixed_bytes():
    t = np.array([0.5, 1.5, 1.6, 1.7, 2.5])
    ids = np.array([0xD0, 0xD0, 0xD0, 0x1A0, 0xD0])
    payload = np.zeros((5, 8), np.uint8)
    payload[[0, 1, 3, 4], 5] = 0xFF
    info = {"injection_interval": [1.0, 2.0], "injection_id": "0xd0", "injection_data_str": "XXXXXXXXXXFFXXXX"}
    # only frame 1: in the interval, the right ID and byte 5 = FF
    assert attack_frames(t, ids, payload, info).tolist() == [False, True, False, False, False]
    fuzz = {"injection_interval": [1.0, 2.0], "injection_id": "XXX", "injection_data_str": "FFFFFFFFFFFFFFFF"}
    payload[2] = 0xFF
    assert attack_frames(t, ids, payload, fuzz).tolist() == [False, False, True, False, False]


@pytest.mark.parametrize("name,cls,inst", [
    ("max_speedometer_attack_3_masquerade", "max_speedometer", 3), ("fuzzing_attack_1", "fuzzing", 1),
    ("reverse_light_off_attack_2", "reverse_light", 2), ("max_engine_coolant_temp_attack", "max_coolant_temp", None),
    ("accelerator_attack_drive_1", None, 1),
])
def test_capture_names(name, cls, inst):
    assert capture_class(name) == cls
    assert instance_of(name) == inst


def test_line_chunks_are_whole_lines_spread_over_the_file():
    data = "".join(f"line {i}\n" for i in range(100)).encode()
    chunks = line_chunks(data, rows=20, chunks=2)
    lines = [c.decode().splitlines() for c in chunks]
    assert [len(x) for x in lines] == [10, 10]
    assert lines[0][0] == "line 0" and lines[1][-1] == "line 99"


def test_zip_and_folder_give_the_same_files(tmp_path):
    write_fake_road(tmp_path / "a", zipped=True)
    write_fake_road(tmp_path / "b", zipped=False)
    za, fb = RawFiles(tmp_path / "a", (".log", ".json")), RawFiles(tmp_path / "b", (".log", ".json"))
    assert za.where.endswith("road.zip")
    assert za.signature() == fb.signature()
    assert not any("__MACOSX" in n for n in za.names())


# ----------------------------------------------------------------------------- split

def test_labels_count_every_injected_frame(fake_road):
    root, injected = fake_road
    splits = load_road(root, {**SETTINGS, "context_seconds": 100.0})
    found = {}
    for split in ("train", "test"):
        for s in splits[split]:
            found[s.name] = found.get(s.name, 0) + int((s.frame_labels > 0).sum())
    for name, k in injected.items():
        assert found[name] == k, name


def test_split_by_instance_with_masquerade_set(fake_road):
    root, _ = fake_road
    splits = load_road(root, SETTINGS)
    names = {k: {s.name.split("#")[0] for s in v} for k, v in splits.items()}
    assert "correlated_signal_attack_3" in names["test"] and "correlated_signal_attack_1" in names["train"]
    assert not {n for n in names["train"] if n.endswith(("_3", "_3_masquerade"))}
    assert names["masquerade"] == {"correlated_signal_attack_3_masquerade", "max_speedometer_attack_3_masquerade",
                                   "reverse_light_on_attack_3_masquerade", "max_engine_coolant_temp_attack_masquerade"}
    assert "ambient_dyno_drive_basic_short" in names["test"] and "ambient_dyno_drive_basic_short" not in names["train"]
    assert not any("accelerator" in n for v in names.values() for n in v)
    # the coolant attack, recorded once, is in both splits, with attack frames in each
    for split in ("train", "test"):
        coolant = [s for s in splits[split] if s.name == "max_engine_coolant_temp_attack"]
        assert coolant and (coolant[0].frame_labels == CLASSES.index("max_coolant_temp")).any()


def test_ambient_keeps_only_the_chunks(fake_road):
    root, _ = fake_road
    splits = load_road(root, SETTINGS)
    amb = [s for s in splits["train"] if s.name.startswith("ambient_dyno_drive_basic_long")]
    assert len(amb) == 2 and sum(len(s) for s in amb) == 2000


def test_build_road_end_to_end(fake_road, tmp_path):
    root, _ = fake_road
    cfg = {"dataset": {"processed_dir": str(tmp_path)},
           "build": {"window_size": 16, "stride": 8, "seq_len": 4, "seq_stride": 2, "max_nodes": 64,
                     "edge_mode": "transition", "min_attack_frames": 1, "max_rows_per_class": {"benign": 5},
                     "split": "blocks", "test_fraction": 0.2},
           "road": {"raw_dir": str(root), "classes": CLASSES, "build": {**SETTINGS, "min_id_count": 20}}}
    path = build_dataset(cfg, source="road")
    assert path.name.startswith("road_")
    payload = load_processed(path)
    meta = payload["meta"]
    assert meta["extra_tests"] == ["masquerade"] and set(payload["splits"]) == {"train", "test", "masquerade"}
    assert meta["num_nodes"] == len(IDS) + 1               # fuzzing IDs (sent once each) stay out of the vocabulary
    assert all(c > 0 for c in meta["class_counts"]["train"])
    assert meta["class_counts"]["masquerade"][CLASSES.index("fuzzing")] == 0
    assert "max_rows_per_class" not in meta["settings"]    # CIC-only settings don't apply
    assert build_dataset(cfg, source="road") == path       # reused, not rebuilt


def test_road_profile_runs_and_reports_the_masquerade_set(fake_road, tmp_path):
    from grama.experiments.report import make_report
    from grama.experiments.runner import Experiment, RunSpec

    root, _ = fake_road
    exp = Experiment("road", device="cpu", results_dir=tmp_path / "results")
    exp.data_cfg["dataset"]["processed_dir"] = str(tmp_path / "processed")
    exp.data_cfg["build"].update(window_size=16, stride=8, seq_len=4, seq_stride=2)
    exp.data_cfg["road"] = {**exp.data_cfg["road"], "raw_dir": str(root),
                            "build": {**exp.data_cfg["road"]["build"], **SETTINGS}}
    exp.sim.update(num_clients=4, clients_per_round=3, num_rounds=2, local_epochs=1)
    exp.prepare_data()
    specs = [RunSpec("grama", "hdbscan", 0.5, None, 0.0, 0), RunSpec("cnn_bigru", "fedavg", 0.5, None, 0.0, 0),
             RunSpec("grama", "central", 0.5, None, 0.0, 0)]
    with exp.runs_path.open("w") as f:
        for spec in specs:
            rec = exp.run_one(spec)
            assert set(rec["tests"]) == {"masquerade"}
            assert len(rec["final"]["confusion_matrix"]) == len(CLASSES)
            f.write(json.dumps(rec) + "\n")
    summary = make_report(exp.out_dir).read_text()
    assert "Masquerade attacks only" in summary and "| masquerade |" in summary
    assert "Data: ROAD" in summary and "by capture" in summary
