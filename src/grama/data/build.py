"""Builds the window dataset from CIC-IoV2024 CSVs, or from synthetic CAN traffic.

Steps (Sec 3.2 and Sec 4.1 Phase 1 of the concept note):
  1. find the CSVs anywhere under data/raw (zip and tar.xz archives are unpacked first)
  2. one stream of frames per file, labelled from the file name
  3. optional cap on rows per class (the benign file alone has 1.2M rows)
  4. split every stream into train and test without any window crossing
     between them: interleaved blocks by default (every fifth block of
     1,000 rows tests), or a plain time split (last 20% tests)
  5. optional: interleave attack frames with benign traffic, the way a real
     injection attack looks on the bus (harder than the released files,
     where each attack file holds attack frames only)
  6. CAN-ID vocabulary and min-max scaling (eq. 3) fitted on train only
  7. sliding windows -> per-node features; consecutive windows -> sequences

Everything is vectorised with numpy (bincount and cumsum over the frames),
so the full 1.4M-row dataset builds in well under a minute.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from grama.utils.logging import get_logger

logger = get_logger(__name__)

PAYLOAD_COLS = [f"DATA_{i}" for i in range(8)]
NUM_FEATURES = len(PAYLOAD_COLS) + 2  # 8 mean bytes + frame share + burst flag
BUILD_VERSION = 2


@dataclass
class Stream:
    """Consecutive CAN frames from one source, in bus order."""
    name: str
    class_idx: int           # class of the file (attack class, or 0 for benign)
    ids: np.ndarray          # (n,) CAN arbitration IDs
    payload: np.ndarray      # (n, 8) uint8
    frame_labels: np.ndarray # (n,) class of each frame

    def __len__(self) -> int:
        return len(self.ids)

    def slice(self, start: int, stop: int | None) -> "Stream":
        s = slice(start, stop)
        return Stream(self.name, self.class_idx, self.ids[s], self.payload[s], self.frame_labels[s])


# ----------------------------------------------------------------------------- files

def canonical(name: str) -> str:
    """'decimal_spoofing-STEERING_WHEEL' -> 'steeringwheel', 'DoS' -> 'dos'."""
    s = name.lower()
    s = re.sub(r"^(decimal|hexadecimal|hex|binary)[_\- ]*", "", s)
    s = s.replace("spoofing", "")
    return re.sub(r"[^a-z0-9]", "", s)


def class_index(name: str, class_names: list[str]) -> int | None:
    c = canonical(name)
    for i, cls in enumerate(class_names):
        if canonical(cls) == c:
            return i
    return None


ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.xz", ".txz", ".tar.bz2")


def _is_decimal(name: str) -> bool:
    n = name.lower()
    return "decimal" in n and "hexadecimal" not in n


def _archive_folder(archive: Path) -> Path:
    name = archive.name
    for suffix in sorted(ARCHIVE_SUFFIXES, key=len, reverse=True):
        if name.lower().endswith(suffix):
            return archive.with_name(name[: -len(suffix)])
    return archive.with_suffix("")


def _check_inside(target: Path, names: list[str]) -> None:
    root = target.resolve()
    for name in names:
        dest = (target / name).resolve()
        if root not in dest.parents and dest != root:
            raise ValueError(f"Refusing to unpack {name}: path leaves {target}")


def unpack_archives(raw_dir: Path) -> None:
    """Unpack every archive under raw_dir (zip, tar, tar.gz, tar.xz) next to itself, once.

    The CIC release (CICIoV2024.tar.xz) holds decimal, binary and hexadecimal
    versions of the data. Only the decimal files are extracted when they are
    there, which saves disk space; otherwise everything is.
    """
    import tarfile

    archives = [p for p in raw_dir.rglob("*") if p.is_file() and p.name.lower().endswith(ARCHIVE_SUFFIXES)]
    for archive in sorted(archives):
        target = _archive_folder(archive)
        marker = target / ".unpacked"
        if marker.exists():
            continue
        logger.info("Unpacking %s (a few minutes for the full CIC archive)", archive.name)
        target.mkdir(parents=True, exist_ok=True)
        if archive.name.lower().endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                names = zf.namelist()
                _check_inside(target, names)
                wanted = [n for n in names if _is_decimal(n)]
                if not any(n.lower().endswith(".csv") for n in wanted):
                    wanted = names
                zf.extractall(target, members=wanted)
        else:
            # One pass for the decimal files (a .tar.xz is slow to read twice);
            # a second, full pass only if the archive has no decimal CSVs.
            with tarfile.open(archive) as tf:
                found = _extract_tar(tf, target, decimal_only=True)
            if not found:
                with tarfile.open(archive) as tf:
                    _extract_tar(tf, target, decimal_only=False)
        marker.touch()


def _extract_tar(tf, target: Path, decimal_only: bool) -> int:
    """Extract regular files and folders (no links); return how many CSVs came out."""
    import tarfile

    csvs = 0
    for member in tf:
        if not (member.isfile() or member.isdir()):
            continue
        if decimal_only and not _is_decimal(member.name):
            continue
        _check_inside(target, [member.name])
        if hasattr(tarfile, "data_filter"):
            tf.extract(member, target, filter="data")
        else:
            tf.extract(member, target)
        csvs += member.isfile() and member.name.lower().endswith(".csv")
    return csvs


def find_csv_files(raw_dir: Path) -> list[Path]:
    """All CSVs under raw_dir. If the decimal version of the release is there, only those."""
    csvs = []
    for p in raw_dir.rglob("*.csv"):
        parts = p.relative_to(raw_dir).parts
        if any(part.startswith(".") or part == "__MACOSX" for part in parts):
            continue
        csvs.append(p)
    decimal = [p for p in csvs if "decimal" in str(p.relative_to(raw_dir)).lower()
               and "hexadecimal" not in str(p.relative_to(raw_dir)).lower()]
    return sorted(decimal or csvs)


def _to_int(col: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(col):
        return col.to_numpy(dtype=np.int64)
    return col.astype(str).str.strip().map(lambda v: int(v, 16)).to_numpy(dtype=np.int64)


def read_streams(path: Path, class_names: list[str]) -> list[Stream]:
    """One CSV -> one stream. Label from the file name, else from a label column."""
    label_cols = ("specific_class", "category", "label")
    df = pd.read_csv(path, usecols=lambda c: c.strip() in ["ID", *PAYLOAD_COLS, *label_cols])
    df.columns = [c.strip() for c in df.columns]
    missing = {"ID", *PAYLOAD_COLS} - set(df.columns)
    if missing:
        logger.warning("Skipping %s: missing columns %s", path.name, sorted(missing))
        return []

    ids = _to_int(df["ID"])
    payload = np.stack([_to_int(df[c]) for c in PAYLOAD_COLS], axis=1).clip(0, 255).astype(np.uint8)

    cls = class_index(path.stem, class_names)
    if cls is not None:
        return [Stream(path.stem, cls, ids, payload, np.full(len(ids), cls, dtype=np.int64))]

    # No class in the file name: label each row from its own label column.
    for col in label_cols:
        if col not in df.columns:
            continue
        mapping = {v: class_index(str(v), class_names) for v in df[col].unique()}
        if all(m is not None for m in mapping.values()):
            labels = df[col].map(mapping).to_numpy(dtype=np.int64)
            main = int(np.bincount(labels).argmax())
            return [Stream(path.stem, main, ids, payload, labels)]
    logger.warning("Skipping %s: can't tell its class from the name or the label columns", path.name)
    return []


# ----------------------------------------------------------------------------- synthetic

def synthetic_streams(class_names: list[str], rows_per_class: int, seed: int = 0,
                      num_ids: int = 16, attack_ratio: float = 0.2) -> list[Stream]:
    """Periodic CAN-like traffic with injected attack frames, for tests and the smoke profile.

    Benign: num_ids IDs, each sent with its own period and a slowly varying
    payload. Attacks: the same traffic with frames injected at attack_ratio:
    DoS floods ID 0x000 with zeros; each spoofing class sends one victim ID
    with a fixed forged payload.
    """
    rng = np.random.default_rng(seed)
    can_ids = np.sort(rng.choice(np.arange(0x080, 0x7FF), num_ids, replace=False))
    periods = rng.integers(1, 6, num_ids)
    base = rng.integers(0, 256, (num_ids, 8))
    schedule = np.array([i for t in range(60) for i in range(num_ids) if t % periods[i] == 0])

    def benign(n: int, offset: int) -> tuple[np.ndarray, np.ndarray]:
        idx = np.tile(schedule, n // len(schedule) + 2)[offset: offset + n]
        drift = (np.arange(n)[:, None] // 50) % 7
        payload = base[idx] + drift + rng.integers(-2, 3, (n, 8))
        payload[:, 7] = np.arange(n) % 256  # rolling counter byte
        return can_ids[idx], payload.clip(0, 255).astype(np.uint8)

    streams = []
    ids, payload = benign(rows_per_class, 0)
    streams.append(Stream("synthetic_benign", 0, ids, payload, np.zeros(rows_per_class, dtype=np.int64)))

    for k in range(1, len(class_names)):
        n_attack = int(rows_per_class * attack_ratio)
        n_benign = rows_per_class - n_attack
        b_ids, b_payload = benign(n_benign, int(rng.integers(0, len(schedule))))
        if canonical(class_names[k]) == "dos":
            a_ids = np.zeros(n_attack, dtype=np.int64)
            a_payload = np.zeros((n_attack, 8), dtype=np.uint8)
        else:
            victim = (k * 3) % num_ids
            a_ids = np.full(n_attack, can_ids[victim])
            forged = base[victim].copy()
            forged[k % 7] = 255 - forged[k % 7]
            a_payload = np.tile(forged, (n_attack, 1)).astype(np.uint8)
        is_attack = np.zeros(rows_per_class, dtype=bool)
        is_attack[rng.choice(rows_per_class, n_attack, replace=False)] = True
        ids = np.empty(rows_per_class, dtype=np.int64)
        pl = np.empty((rows_per_class, 8), dtype=np.uint8)
        ids[is_attack], ids[~is_attack] = a_ids, b_ids
        pl[is_attack], pl[~is_attack] = a_payload, b_payload
        labels = np.where(is_attack, k, 0).astype(np.int64)
        streams.append(Stream(f"synthetic_{class_names[k]}", k, ids, pl, labels))
    return streams


# ----------------------------------------------------------------------------- transforms

def cap_rows(streams: list[Stream], caps, class_names: list[str]) -> list[Stream]:
    """caps: None, one int for every class, or {class_name: int}."""
    if not caps:
        return streams
    out = []
    for s in streams:
        cap = caps.get(class_names[s.class_idx]) if isinstance(caps, dict) else caps
        out.append(s.slice(0, int(cap)) if cap and len(s) > cap else s)
    return out


def inject_into_benign(attack: Stream, benign: Stream, ratio: float, rng) -> Stream:
    """Interleave an attack stream with benign frames so attack frames make up `ratio` of it."""
    n_a = len(attack)
    n_b = int(round(n_a * (1 - ratio) / ratio))
    take = (int(rng.integers(0, len(benign))) + np.arange(n_b)) % len(benign)
    total = n_a + n_b
    is_attack = np.zeros(total, dtype=bool)
    is_attack[rng.choice(total, n_a, replace=False)] = True
    ids = np.empty(total, dtype=np.int64)
    payload = np.empty((total, 8), dtype=np.uint8)
    labels = np.empty(total, dtype=np.int64)
    ids[is_attack], ids[~is_attack] = attack.ids, benign.ids[take]
    payload[is_attack], payload[~is_attack] = attack.payload, benign.payload[take]
    labels[is_attack], labels[~is_attack] = attack.frame_labels, benign.frame_labels[take]
    return Stream(attack.name, attack.class_idx, ids, payload, labels)


def split_stream(s: Stream, settings: dict) -> tuple[list[Stream], list[Stream]]:
    """Cut one stream into train pieces and test pieces.

    "blocks" (default): blocks of block_rows rows, every k-th block to test
    (k = 1 / test_fraction). Each recorded segment of a file then shows up in
    both splits, and windows are built inside a piece, so none crosses over.
    "temporal": the last test_fraction of the stream tests. On CIC-IoV2024 this
    puts frames in the test set that never occur in training (the RPM and SPEED
    files end on CAN ID 513 with new payloads), which caps every model.
    """
    method = settings.get("split", "blocks")
    test_fraction = settings["test_fraction"]
    n = len(s)
    if method not in ("blocks", "temporal"):
        raise ValueError(f"split must be 'blocks' or 'temporal', got {method!r}")
    rows = int(settings.get("block_rows", 1000))
    every = max(2, round(1 / test_fraction))
    n_blocks = -(-n // rows)
    if method == "temporal" or n_blocks < every:
        cut = int(n * (1 - test_fraction))
        return [s.slice(0, cut)], [s.slice(cut, None)]
    is_test = [b % every == every - 1 for b in range(n_blocks)]
    train, test = [], []
    b = 0
    while b < n_blocks:
        e = b
        while e + 1 < n_blocks and is_test[e + 1] == is_test[b]:
            e += 1
        piece = s.slice(b * rows, min((e + 1) * rows, n))
        (test if is_test[b] else train).append(piece)
        b = e + 1
    return train, test


def fit_vocabulary(train_ids: np.ndarray, max_nodes: int) -> np.ndarray:
    """Most frequent CAN IDs in train (max_nodes - 1 of them). Every other ID maps to one 'other' node."""
    values, counts = np.unique(train_ids, return_counts=True)
    keep = values[np.argsort(-counts, kind="stable")[: max_nodes - 1]]
    return np.sort(keep)


def map_ids(ids: np.ndarray, vocab: np.ndarray) -> np.ndarray:
    pos = np.searchsorted(vocab, ids).clip(0, len(vocab) - 1)
    return np.where(vocab[pos] == ids, pos, len(vocab)).astype(np.int64)


def window_stream(node_ids, payload_norm, payload_raw, frame_labels, *, window_size, stride,
                  num_nodes, num_classes, min_attack_frames=1):
    """Sliding windows over one stream -> per-window node features and labels.

    Node features (F = 10): mean of the 8 scaled payload bytes the node sent
    in the window, the node's share of the window's frames, and a burst flag
    (the node sent more frames than the average active node).
    """
    n = len(node_ids)
    if n < window_size:
        return None
    W, N = window_size, num_nodes
    starts = np.arange(0, n - W + 1, stride)
    nw = len(starts)
    frame_idx = (starts[:, None] + np.arange(W)).ravel()
    node = node_ids[frame_idx]
    key = np.repeat(np.arange(nw), W) * N + node

    counts = np.bincount(key, minlength=nw * N).reshape(nw, N).astype(np.float32)
    x = np.zeros((nw, N, NUM_FEATURES), dtype=np.float32)
    denom = np.maximum(counts, 1.0)
    for j in range(len(PAYLOAD_COLS)):
        sums = np.bincount(key, weights=payload_norm[frame_idx, j], minlength=nw * N).reshape(nw, N)
        x[..., j] = sums / denom
    x[..., -2] = counts / W
    active = counts > 0
    mean_active = counts.sum(1) / np.maximum(active.sum(1), 1)
    x[..., -1] = (counts > mean_active[:, None]).astype(np.float32)

    # Window label: the dominant attack class if it sent at least
    # min_attack_frames frames in the window, otherwise benign.
    onehot = np.zeros((n, num_classes), dtype=np.int32)
    onehot[np.arange(n), frame_labels] = 1
    cs = np.vstack([np.zeros((1, num_classes), dtype=np.int64), np.cumsum(onehot, axis=0)])
    per_class = cs[starts + W] - cs[starts]
    attack = per_class[:, 1:]
    labels = np.where(attack.sum(1) >= min_attack_frames, attack.argmax(1) + 1, 0)

    return {
        "x": x,
        "frame_ids": node.reshape(nw, W).astype(np.int16),
        "frame_bytes": payload_raw[frame_idx].reshape(nw, W, 8),
        "window_labels": labels.astype(np.int64),
    }


# ----------------------------------------------------------------------------- build

def build_from_streams(streams: list[Stream], settings: dict, class_names: list[str], seed: int = 0) -> dict:
    """Streams -> {'meta', 'splits': {'train': ..., 'test': ...}} of torch tensors."""
    rng = np.random.default_rng(seed)
    num_classes = len(class_names)
    W = settings["window_size"]
    L = settings["seq_len"]

    streams = cap_rows(streams, settings.get("max_rows_per_class"), class_names)

    split_streams = {"train": [], "test": []}
    for s in streams:
        train_pieces, test_pieces = split_stream(s, settings)
        split_streams["train"].extend(train_pieces)
        split_streams["test"].extend(test_pieces)

    inj = settings.get("injection") or {}
    if inj.get("enabled"):
        for split, ss in split_streams.items():
            benign = [s for s in ss if s.class_idx == 0]
            if not benign:
                raise ValueError("Injection needs a benign stream")
            pool = Stream("benign_pool", 0, np.concatenate([b.ids for b in benign]),
                          np.concatenate([b.payload for b in benign]),
                          np.concatenate([b.frame_labels for b in benign]))
            split_streams[split] = [s if s.class_idx == 0 else
                                    inject_into_benign(s, pool, inj["attack_ratio"], rng) for s in ss]

    train_ids = np.concatenate([s.ids for s in split_streams["train"]])
    vocab = fit_vocabulary(train_ids, settings["max_nodes"])
    num_nodes = len(vocab) + 1
    train_payload = np.concatenate([s.payload for s in split_streams["train"]])
    lo = train_payload.min(axis=0).astype(np.float32)
    span = np.maximum(train_payload.max(axis=0).astype(np.float32) - lo, 1.0)

    splits, counts = {}, {}
    for split, ss in split_streams.items():
        xs, fids, fbytes, starts, labels = [], [], [], [], []
        offset, skipped_rows = 0, 0
        for s in ss:
            payload_norm = ((s.payload.astype(np.float32) - lo) / span).clip(0.0, 1.0)
            out = window_stream(
                map_ids(s.ids, vocab), payload_norm, s.payload, s.frame_labels,
                window_size=W, stride=settings["stride"], num_nodes=num_nodes,
                num_classes=num_classes, min_attack_frames=settings.get("min_attack_frames", 1),
            )
            if out is None or len(out["x"]) < L:
                skipped_rows += len(s)   # a piece too short for one sequence (e.g. a file's last block)
                continue
            nw = len(out["x"])
            seq_starts = np.arange(0, nw - L + 1, settings["seq_stride"])
            xs.append(out["x"])
            fids.append(out["frame_ids"])
            fbytes.append(out["frame_bytes"])
            starts.append(seq_starts + offset)
            labels.append(out["window_labels"][seq_starts + L - 1])
            offset += nw
        if not labels:
            raise ValueError(f"No sequences in the {split} split. Use more rows or a smaller window.")
        if skipped_rows:
            logger.info("%s: %d rows in pieces too short for a sequence were left out", split, skipped_rows)
        y = np.concatenate(labels)
        splits[split] = {
            "x": torch.from_numpy(np.concatenate(xs)),
            "frame_ids": torch.from_numpy(np.concatenate(fids)),
            "frame_bytes": torch.from_numpy(np.concatenate(fbytes)),
            "starts": torch.from_numpy(np.concatenate(starts)),
            "labels": torch.from_numpy(y),
        }
        counts[split] = np.bincount(y, minlength=num_classes).tolist()

    meta = {
        "build_version": BUILD_VERSION,
        "class_names": list(class_names),
        "num_classes": num_classes,
        "num_nodes": num_nodes,
        "in_features": NUM_FEATURES,
        "vocab": vocab.tolist(),
        "payload_min": lo.tolist(),
        "payload_span": span.tolist(),
        "class_counts": counts,
        "streams": [s.name for s in streams],
        **{k: settings[k] for k in ("window_size", "stride", "seq_len", "seq_stride", "edge_mode")},
        "split": settings.get("split", "blocks"),
        "block_rows": settings.get("block_rows", 1000),
        "injection": inj if inj.get("enabled") else None,
    }
    return {"meta": meta, "splits": splits}


def _settings_hash(settings: dict, files: list[Path]) -> str:
    sig = {"v": BUILD_VERSION, "settings": settings,
           "files": [(p.name, p.stat().st_size) for p in files]}
    return hashlib.sha1(json.dumps(sig, sort_keys=True, default=str).encode()).hexdigest()[:8]


def build_dataset(data_cfg: dict, source: str = "real", overrides: dict | None = None,
                  force: bool = False, seed: int = 0) -> Path:
    """Build (or reuse) the processed dataset and return its path.

    source: "real" (CSV files under data/raw) or "synthetic".
    overrides: settings that replace the data config, e.g. a profile's row caps.
    The output name carries a hash of the settings and input files, so a
    changed setting gives a new file and an unchanged one is reused.
    """
    settings = dict(data_cfg["build"])
    settings.update(overrides or {})
    class_names = data_cfg["classes"]
    processed_dir = Path(data_cfg["dataset"]["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    if source == "synthetic":
        files: list[Path] = []
        tag = "synthetic"
    else:
        raw_dir = Path(data_cfg["dataset"]["raw_dir"])
        unpack_archives(raw_dir)
        files = find_csv_files(raw_dir)
        if not files:
            raise FileNotFoundError(f"No CSV files under {raw_dir.resolve()}. See the README, 'Getting the data'.")
        tag = "cic_iov2024"

    out_path = processed_dir / f"{tag}_{_settings_hash(settings, files)}.pt"
    if out_path.exists() and not force:
        logger.info("Reusing %s", out_path)
        return out_path

    if source == "synthetic":
        streams = synthetic_streams(class_names, settings.get("synthetic_rows_per_class", 6000), seed=seed)
    else:
        streams = []
        for f in files:
            new = read_streams(f, class_names)
            for s in new:
                logger.info("%-40s %9d rows  -> %s", f.name, len(s), class_names[s.class_idx])
            streams.extend(new)
        if not streams:
            raise ValueError("None of the CSV files could be read. Check that they are the CIC-IoV2024 files.")

    payload = build_from_streams(streams, settings, class_names, seed=seed)
    payload["meta"]["source"] = source
    torch.save(payload, out_path)

    meta = payload["meta"]
    logger.info("Saved %s | %d CAN-ID nodes | sequences per class (train) %s | (test) %s",
                out_path, meta["num_nodes"], meta["class_counts"]["train"], meta["class_counts"]["test"])
    return out_path
