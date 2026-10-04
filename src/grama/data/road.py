"""ROAD, the Real ORNL Automotive Dynamometer CAN dataset (Verma et al., PLOS ONE 2024).

    https://doi.org/10.5281/zenodo.10462796    road.zip, 557 MB, CC-BY 4.0

One car, recorded on a dynamometer and on the road. Logs are in candump
format, one frame per line:

    (1110000000.000001) can0 5E1#893FE00B0A000080

Attack captures come with attacks/capture_metadata.json, which gives each
capture's injected ID, the injection interval in seconds from the start of
the capture, and the payload written ("X" = a nibble left as it was).

Labels. ROAD labels time intervals, not frames. A frame is an attack frame
when it falls inside the interval and matches the injection:
  - fuzzing: payload FFFFFFFFFFFFFFFF (the IDs are random);
  - the others: the injected ID with the injected bytes.
In the plain captures the injected frames run next to the real ones (exactly
half of that ID's frames in the interval match). In the masquerade versions
the real frames were taken out, and every frame of that ID in the interval
matches, so the same rule labels both. The four accelerator captures give no
ID, interval or payload, so their frames can't be labelled; they are left out.

Classes: benign, fuzzing, correlated signal (ID 0x6E0), max speedometer
(0xD0), max coolant temperature (0x4E7), reverse light (0xD0, on and off).

Split, by capture rather than by block, so no test frame sits next to a
training frame:
  - every attack was recorded three times: instances 1-2 train, 3 tests,
    with their masquerade versions;
  - the coolant attack was recorded once: both versions are cut at the middle
    of the injection interval, the first half trains, the second tests;
  - ambient (benign) captures: the ones named in test_ambient test, the rest
    train. Only a few evenly spaced chunks of each are kept (ambient_rows in
    ambient_chunks pieces); the long highway log alone has ten million frames.
Attack captures are cut to the injection interval plus context_seconds on
each side. A third split, "masquerade", holds only the masquerade captures of
the test split: the attacks that replace real frames instead of adding to them.
"""
from __future__ import annotations

import io
import json
import re

import numpy as np
import pandas as pd

from grama.data.build import Stream
from grama.data.rawfiles import RawFiles, hex_ids, hex_payloads
from grama.utils.logging import get_logger

logger = get_logger(__name__)

CLASSES = ["benign", "fuzzing", "correlated_signal", "max_speedometer", "max_coolant_temp", "reverse_light"]
CAPTURE_CLASS = {
    "fuzzing_attack": "fuzzing",
    "correlated_signal_attack": "correlated_signal",
    "max_speedometer_attack": "max_speedometer",
    "max_engine_coolant_temp_attack": "max_coolant_temp",
    "reverse_light_on_attack": "reverse_light",
    "reverse_light_off_attack": "reverse_light",
}
DEFAULTS = {
    "test_instance": 3,
    "test_ambient": ["ambient_dyno_drive_basic_short", "ambient_highway_street_driving_diagnostics"],
    "context_seconds": 5.0,
    "ambient_rows": 60000,
    "ambient_chunks": 3,
}


def road_files(root) -> RawFiles:
    return RawFiles(root, (".log", "capture_metadata.json"))


# ----------------------------------------------------------------------------- parsing

def parse_candump(data: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """candump text -> (time in seconds, CAN IDs, (n, 8) payload bytes)."""
    df = pd.read_csv(io.BytesIO(data), sep=" ", header=None, names=["t", "iface", "frame"],
                     usecols=[0, 2], dtype=str)
    t = df["t"].str.strip("()").astype(float).to_numpy()
    parts = df["frame"].str.split("#", n=1, expand=True)
    payload = parts[1] if parts.shape[1] > 1 else pd.Series([""] * len(df))
    return t, hex_ids(parts[0]), hex_payloads(payload)


def line_chunks(data: bytes, rows: int, chunks: int) -> list[bytes]:
    """`chunks` evenly spaced pieces of the text, with `rows` lines in all."""
    ends = np.flatnonzero(np.frombuffer(data, dtype=np.uint8) == 10)   # newline positions
    n = len(ends)
    if n <= rows:
        return [data]
    per = rows // chunks
    starts = np.linspace(0, n - per, chunks).astype(int)
    out = []
    for s in starts:
        lo = 0 if s == 0 else ends[s - 1] + 1
        out.append(data[lo: ends[s + per - 1] + 1])
    return out


def attack_frames(t: np.ndarray, ids: np.ndarray, payload: np.ndarray, meta: dict) -> np.ndarray:
    """Boolean mask of the injected frames of one attack capture (times from the start of the capture)."""
    lo, hi = meta["injection_interval"]
    inside = (t >= lo) & (t <= hi)
    pattern = meta["injection_data_str"].upper()
    if str(meta["injection_id"]).upper() == "XXX":            # fuzzing: random IDs, all-FF payload
        return inside & (payload == 0xFF).all(axis=1)
    mask = inside & (ids == int(meta["injection_id"], 16))
    for b in range(8):
        byte = pattern[2 * b: 2 * b + 2]
        if "X" not in byte:
            mask &= payload[:, b] == int(byte, 16)
    return mask


def capture_class(name: str) -> str | None:
    base = re.sub(r"(_\d+)?(_masquerade)?$", "", name)
    return CAPTURE_CLASS.get(base)


def instance_of(name: str) -> int | None:
    m = re.search(r"_(\d+)(_masquerade)?$", name)
    return int(m.group(1)) if m else None


# ----------------------------------------------------------------------------- streams

def _stream(name, cls, t, ids, payload, labels, keep) -> Stream | None:
    if not keep.any():
        return None
    idx = np.flatnonzero(keep)
    idx = np.arange(idx[0], idx[-1] + 1)            # one unbroken piece of the capture
    return Stream(name, cls, ids[idx], payload[idx], labels[idx])


def load_road(root, settings: dict, class_names: list[str] = CLASSES) -> dict[str, list[Stream]]:
    """ROAD -> {'train': [...], 'test': [...], 'masquerade': [...]} streams."""
    s = {**DEFAULTS, **{k: v for k, v in settings.items() if k in DEFAULTS}}
    files = road_files(root)
    meta_name = next((n for n in files.names() if n.endswith("attacks/capture_metadata.json")), None)
    if meta_name is None:
        raise FileNotFoundError(f"No attacks/capture_metadata.json under {files.where}. See the README.")
    meta = json.loads(files.read_bytes(meta_name))
    cls_index = {c: i for i, c in enumerate(class_names)}
    splits: dict[str, list[Stream]] = {"train": [], "test": [], "masquerade": []}
    ctx = float(s["context_seconds"])

    for name in files.names():
        if not name.endswith(".log"):
            continue
        capture = name.rsplit("/", 1)[-1][:-4]
        if "/ambient/" in f"/{name}":
            split = "test" if capture in s["test_ambient"] else "train"
            pieces = line_chunks(files.read_bytes(name), int(s["ambient_rows"]), int(s["ambient_chunks"]))
            for k, piece in enumerate(pieces):
                _, ids, payload = parse_candump(piece)
                splits[split].append(Stream(f"{capture}#{k}", 0, ids, payload, np.zeros(len(ids), np.int64)))
            continue

        info = meta.get(capture)
        cls = capture_class(capture)
        if info is None or info.get("injection_interval") is None or cls is None:
            logger.info("ROAD: leaving out %s (no labels)", capture)
            continue
        t, ids, payload = parse_candump(files.read_bytes(name))
        t = t - t[0]
        k = cls_index[cls]
        labels = np.where(attack_frames(t, ids, payload, info), k, 0).astype(np.int64)
        lo, hi = info["injection_interval"]
        near = (t >= lo - ctx) & (t <= hi + ctx)
        masquerade = bool(info.get("modified")) or capture.endswith("_masquerade")

        inst = instance_of(capture)
        if inst is None:                      # one recording only: cut in the middle of the attack
            mid = (lo + hi) / 2
            parts = {"train": near & (t < mid), "test": near & (t >= mid)}
        else:
            parts = {"test" if inst == int(s["test_instance"]) else "train": near}
        for split, keep in parts.items():
            st = _stream(capture, k, t, ids, payload, labels, keep)
            if st is None:
                continue
            splits[split].append(st)
            if split == "test" and masquerade:
                splits["masquerade"].append(st)

    for split, ss in splits.items():
        n = sum(len(x) for x in ss)
        attack = sum(int((x.frame_labels > 0).sum()) for x in ss)
        logger.info("ROAD %-10s %3d pieces %9d frames, %7d attack frames", split, len(ss), n, attack)
    return splits
