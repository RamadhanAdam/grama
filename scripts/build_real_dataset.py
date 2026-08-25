"""Builds the real CIC-IoV2024 tensor dataset from data/raw/*.csv.

Wires src/grama/data/preprocess.py and graph_builder.py into an actual
pipeline: load -> label (from filename) -> dedup -> normalize -> sliding
windows (per-file, so windows never straddle two attack classes) -> graphs
over a GLOBAL CAN-ID vocabulary (so every window's graph has the same
number of nodes N, required for batching) -> grouped into sequences of
`seq_len` consecutive windows -> saved as tensors to data/processed/.

Usage:
    python scripts/build_real_dataset.py
    python scripts/build_real_dataset.py --seq-len 8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from grama.data.preprocess import PAYLOAD_COLS, deduplicate, min_max_normalize, sliding_windows
from grama.utils.config import Config
from grama.utils.logging import get_logger

logger = get_logger(__name__)


def infer_label_from_filename(path: Path, benign_name: str, attack_classes: list[str]) -> str:
    """decimal_benign.csv -> 'benign'; decimal_spoofing-GAS.csv -> 'spoofing-GAS'."""
    stem = path.stem
    if stem.startswith("decimal_"):
        stem = stem[len("decimal_"):]
    candidates = [benign_name] + attack_classes
    for c in candidates:
        if stem.lower() == c.lower():
            return c
    raise ValueError(f"Could not infer class from filename {path.name}; expected one of {candidates}")


def load_and_label(raw_dir: Path, expected_columns: list[str], benign_name: str,
                    attack_classes: list[str]) -> pd.DataFrame:
    label_map = {benign_name.lower(): 0}
    for i, c in enumerate(attack_classes):
        label_map[c.lower()] = i + 1

    frames = []
    for path in sorted(raw_dir.glob("*.csv")):
        cls = infer_label_from_filename(path, benign_name, attack_classes)
        df = pd.read_csv(path)
        # Normalize column name casing to match expected_columns exactly.
        rename = {c: e for c in df.columns for e in expected_columns if c.strip().lower() == e.lower()}
        df = df.rename(columns=rename)
        # Filename is the source of truth for the label (robust to inconsistent label text in-file).
        df["label"] = label_map[cls.lower()]
        df["_source_file"] = path.name
        frames.append(df)
        logger.info("%s -> class '%s' (label=%d), %d rows", path.name, cls, label_map[cls.lower()], len(df))

    if not frames:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    return pd.concat(frames, ignore_index=True)


def build_fixed_vocab_graph(frames: pd.DataFrame, vocab_to_idx: dict[int, int], num_nodes: int) -> tuple[np.ndarray, np.ndarray]:
    """Like GraphBuilder.build, but indexed into a GLOBAL CAN-ID vocabulary so
    every window produces the same (num_nodes, num_nodes) / (num_nodes, feat) shape."""
    feat_dim = len(PAYLOAD_COLS) + 2
    node_features = np.zeros((num_nodes, feat_dim), dtype=np.float32)
    counts = np.zeros(num_nodes, dtype=np.int32)
    adjacency = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    active: set[int] = set()

    for _, row in frames.iterrows():
        can_id = row["ID"]
        idx = vocab_to_idx.get(can_id)
        if idx is None:
            continue  # unseen CAN ID (shouldn't happen if vocab built from same data)
        active.add(idx)
        payload = np.array([row.get(c, 0.0) for c in PAYLOAD_COLS], dtype=np.float32)
        node_features[idx, : len(PAYLOAD_COLS)] += payload
        counts[idx] += 1

    nonzero = counts > 0
    if nonzero.any():
        node_features[nonzero, :-2] /= counts[nonzero, None]
    node_features[:, -2] = counts
    mean_count = counts[counts > 0].mean() if (counts > 0).any() else 0.0
    node_features[:, -1] = (counts > mean_count).astype(np.float32)

    for i in active:
        for j in active:
            if i != j:
                adjacency[i, j] = 1.0
    np.fill_diagonal(adjacency, 1.0)
    return node_features, adjacency


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-config", default="config/data.yaml")
    parser.add_argument("--seq-len", type=int, default=8, help="Windows per training sequence")
    parser.add_argument("--dedupe", action="store_true",
                         help="Apply exact-duplicate-row dedup before windowing. OFF by default: "
                              "DoS/spoofing attacks in CIC-IoV2024 are near-total repetition of a "
                              "handful of frames (e.g. spoofing-GAS: 9,991 rows -> 2 unique combos), "
                              "so exact dedup destroys the attack signal, not just leakage risk.")
    parser.add_argument("--max-rows-per-class", type=int, default=None,
                         help="Optional cap on rows per class after loading (applied before windowing), "
                              "e.g. to bound the huge benign file (1.2M+ rows) to a tractable size.")
    parser.add_argument("--test-fraction", type=float, default=0.2,
                         help="Fraction of each file's rows (last, contiguous) held out as a time-based "
                              "test split, so no window straddles train/test — this is the leakage guard "
                              "used INSTEAD OF exact dedup.")
    args = parser.parse_args()

    data_cfg = Config.from_yaml(args.data_config)
    raw_dir = Path(data_cfg.dataset["raw_dir"])
    processed_dir = Path(data_cfg.dataset["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    expected_columns = data_cfg.dataset["expected_columns"]
    benign_name = data_cfg.labels["benign"]
    attack_classes = data_cfg.labels["attack_classes"]
    window_size = data_cfg.sliding_window["window_size"]
    stride = data_cfg.sliding_window["stride"]

    logger.info("== Loading + labeling raw CSVs ==")
    df = load_and_label(raw_dir, expected_columns, benign_name, attack_classes)
    logger.info("Combined: %d rows across %d file(s)", len(df), df["_source_file"].nunique())

    if args.max_rows_per_class:
        capped = []
        for src_file, group in df.groupby("_source_file", sort=False):
            capped.append(group.head(args.max_rows_per_class))
        df = pd.concat(capped, ignore_index=True)
        logger.info("Capped to %d rows/class -> %d total rows", args.max_rows_per_class, len(df))

    if args.dedupe:
        logger.info("== Deduplicating (--dedupe passed) ==")
        df = deduplicate(df)
    else:
        logger.info("== Skipping exact-duplicate dedup (default): DoS/spoofing attacks are near-total "
                     "repetition of a few frames, so dedup would erase the attack signal itself. "
                     "Train/test leakage is instead avoided via a time-based split (--test-fraction).")

    logger.info("== Normalizing payload bytes ==")
    df = min_max_normalize(df, columns=data_cfg.normalization["payload_columns"])

    logger.info("== Building global CAN-ID vocabulary ==")
    all_ids = sorted(df["ID"].unique().tolist())
    vocab_to_idx = {cid: i for i, cid in enumerate(all_ids)}
    num_nodes = len(all_ids)
    logger.info("num_nodes (unique CAN IDs) = %d", num_nodes)

    seq_len = args.seq_len

    def windows_to_sequences(group: pd.DataFrame) -> tuple[list, list, list]:
        windows = sliding_windows(group, window_size=window_size, stride=stride)
        graphs = [(*build_fixed_vocab_graph(w.frames, vocab_to_idx, num_nodes), w.label) for w in windows]
        nf_out, adj_out, lbl_out = [], [], []
        for start in range(0, len(graphs) - seq_len + 1, seq_len):
            chunk = graphs[start : start + seq_len]
            nf_out.append(np.stack([g[0] for g in chunk]))
            adj_out.append(np.stack([g[1] for g in chunk]))
            labels_in_seq = [g[2] for g in chunk]
            lbl_out.append(max(set(labels_in_seq), key=labels_in_seq.count))
        return nf_out, adj_out, lbl_out

    split_data = {"train": {"nf": [], "adj": [], "lbl": []}, "test": {"nf": [], "adj": [], "lbl": []}}

    logger.info("== Windowing + graph-building per source file (label-contiguous, time-based split) ==")
    for src_file, group in df.groupby("_source_file", sort=False):
        group = group.reset_index(drop=True)
        n = len(group)
        split_point = int(n * (1 - args.test_fraction))
        train_group, test_group = group.iloc[:split_point], group.iloc[split_point:].reset_index(drop=True)

        for split_name, split_df in [("train", train_group), ("test", test_group)]:
            nf, adj, lbl = windows_to_sequences(split_df)
            split_data[split_name]["nf"].extend(nf)
            split_data[split_name]["adj"].extend(adj)
            split_data[split_name]["lbl"].extend(lbl)
        logger.info("%s: %d rows -> %d train seq, %d test seq",
                     src_file, n, len(split_data["train"]["lbl"]) - 0, len(split_data["test"]["lbl"]))

    if not split_data["train"]["lbl"]:
        logger.error("No training sequences produced — check window_size/stride/seq_len against your data volume.")
        return 1

    num_classes = 1 + len(attack_classes)
    out_path = processed_dir / "dataset.pt"
    payload = {"num_nodes": num_nodes, "in_features": len(PAYLOAD_COLS) + 2,
               "num_classes": num_classes, "seq_len": seq_len}
    for split_name in ["train", "test"]:
        d = split_data[split_name]
        if not d["lbl"]:
            logger.warning("%s split is empty (increase data volume or lower --test-fraction)", split_name)
            continue
        nf_t = torch.tensor(np.stack(d["nf"]), dtype=torch.float32)
        adj_t = torch.tensor(np.stack(d["adj"]), dtype=torch.float32)
        lbl_t = torch.tensor(d["lbl"], dtype=torch.long)
        payload[f"{split_name}_node_features"] = nf_t
        payload[f"{split_name}_adjacency"] = adj_t
        payload[f"{split_name}_labels"] = lbl_t
        logger.info("%s: node_features=%s labels=%s | class dist=%s", split_name,
                     tuple(nf_t.shape), tuple(lbl_t.shape),
                     dict(zip(*np.unique(lbl_t.numpy(), return_counts=True))))

    torch.save(payload, out_path)
    logger.info("Saved: %s", out_path.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())