"""can-train-and-test (Lampe and Meng, 2024): four cars, one training set and four test sets.

    https://data.dtu.dk/articles/dataset/can-train-and-test/24805533    1.5 GB zip, CC-BY 4.0

CSV files with columns timestamp, arbitration_id (hex), data_field (hex, up to
8 bytes) and attack (0 or 1, per frame). The data comes in four sets, each
with a known car (the one in training) and an unknown car:

    set_01  Chevrolet Impala     / Chevrolet Silverado
    set_02  Chevrolet Traverse   / Subaru Forester
    set_03  Chevrolet Silverado  / Subaru Forester
    set_04  Subaru Forester      / Chevrolet Traverse

and in each set one training folder and four test folders:

    train_01                                  -> train
    test_01_known_vehicle_known_attack        -> test
    test_02_unknown_vehicle_known_attack      -> unknown_vehicle
    test_03_known_vehicle_unknown_attack      -> unknown_attack
    test_04_unknown_vehicle_unknown_attack    -> unknown_vehicle_and_attack

Files are shared between sets (set_03 trains on the files set_01 tests on as
its unknown car, for example), but never between a set's training and test
folders. Going by the files, set_01's test_04 holds the Traverse recordings
(the same files as set_02's test_01), not the Silverado.

The attack names differ between the training and the "unknown attack"
folders, so the task is binary: benign or attack. Each attack file is mostly
normal traffic with one burst of attack frames; it is cut to that burst plus
context_rows frames on each side (at most max_rows). Attack-free files are
cut to benign_rows frames, in benign_chunks evenly spaced pieces.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from grama.data.build import Stream
from grama.data.rawfiles import RawFiles, hex_ids, hex_payloads
from grama.utils.logging import get_logger

logger = get_logger(__name__)

CLASSES = ["benign", "attack"]
FOLDERS = {
    "train": "train_01",
    "test": "test_01_known_vehicle_known_attack",
    "unknown_vehicle": "test_02_unknown_vehicle_known_attack",
    "unknown_attack": "test_03_known_vehicle_unknown_attack",
    "unknown_vehicle_and_attack": "test_04_unknown_vehicle_unknown_attack",
}
DEFAULTS = {
    "set": "set_01",
    "context_rows": 15000,
    "max_rows": 80000,
    "benign_rows": 90000,
    "benign_chunks": 3,
}


def cantt_files(root) -> RawFiles:
    return RawFiles(root, (".csv",))


def read_csv(files: RawFiles, name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = pd.read_csv(files.open(name), usecols=["arbitration_id", "data_field", "attack"],
                     dtype={"arbitration_id": str, "data_field": str})
    return hex_ids(df["arbitration_id"]), hex_payloads(df["data_field"]), df["attack"].to_numpy(np.int64)


def pieces(attack: np.ndarray, s: dict) -> list[tuple[int, int]]:
    """Row ranges to keep from one file."""
    n = len(attack)
    hits = np.flatnonzero(attack)
    if len(hits):
        lo = max(0, hits[0] - int(s["context_rows"]))
        hi = min(n, hits[-1] + 1 + int(s["context_rows"]), lo + int(s["max_rows"]))
        return [(lo, hi)]
    rows, chunks = int(s["benign_rows"]), int(s["benign_chunks"])
    if n <= rows:
        return [(0, n)]
    per = rows // chunks
    return [(int(a), int(a) + per) for a in np.linspace(0, n - per, chunks)]


def load_can_train_test(root, settings: dict, class_names: list[str] = CLASSES) -> dict[str, list[Stream]]:
    """One set of can-train-and-test -> {'train', 'test', 'unknown_vehicle', ...} streams."""
    s = {**DEFAULTS, **{k: v for k, v in settings.items() if k in DEFAULTS}}
    files = cantt_files(root)
    if not files.names():
        raise FileNotFoundError(f"No CSV files under {files.where}. See the README.")
    splits: dict[str, list[Stream]] = {}
    for split, folder in FOLDERS.items():
        names = [n for n in files.names() if f"/{s['set']}/{folder}/" in f"/{n}"]
        if not names:
            raise FileNotFoundError(f"No files for {s['set']}/{folder} under {files.where}")
        splits[split] = []
        for name in names:
            ids, payload, attack = read_csv(files, name)
            labels = (attack > 0).astype(np.int64)
            file = name.rsplit("/", 1)[-1][:-4]
            cls = 1 if labels.any() else 0
            for k, (lo, hi) in enumerate(pieces(labels, s)):
                splits[split].append(Stream(f"{s['set']}/{folder}/{file}#{k}", cls,
                                            ids[lo:hi], payload[lo:hi], labels[lo:hi]))
        n = sum(len(x) for x in splits[split])
        a = sum(int(x.frame_labels.sum()) for x in splits[split])
        logger.info("can-train-and-test %s %-27s %3d files %9d frames, %6d attack frames",
                    s["set"], split, len(names), n, a)
    return splits
