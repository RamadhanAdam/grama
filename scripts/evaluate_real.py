"""Evaluates a federated checkpoint's global model on the held-out real test split.

Usage:
    python scripts/evaluate_real.py --checkpoint checkpoints/latest.pt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from grama.eval.metrics import compute_metrics
from grama.federated import checkpoint as ckpt
from grama.models.classifier_head import GraMaLocalModel
from grama.utils.config import Config
from grama.utils.logging import get_logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_federated_train import RealWindowSequenceDataset  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--processed-path", default="data/processed/dataset.pt")
    parser.add_argument("--model-config", default="config/model.yaml")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    model_cfg = Config.from_yaml(args.model_config)
    test_ds = RealWindowSequenceDataset(args.processed_path, split="test")
    loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    model = GraMaLocalModel(model_cfg.gat_encoder, model_cfg.mamba_block, model_cfg.classifier_head)
    payload = ckpt.load_checkpoint(args.checkpoint)
    model.load_state_dict(payload["global_state"])
    model.eval()

    all_true, all_pred, all_proba = [], [], []
    with torch.no_grad():
        for node_features, adjacency, labels in loader:
            logits = model(node_features, adjacency)
            proba = torch.softmax(logits, dim=-1)
            pred = proba.argmax(dim=-1)
            all_true.append(labels.numpy())
            all_pred.append(pred.numpy())
            all_proba.append(proba.numpy())

    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_pred)
    y_proba = np.concatenate(all_proba)

    metrics = compute_metrics(y_true, y_pred, y_proba)
    logger.info("== Test metrics (checkpoint: %s, round %d) ==", args.checkpoint, payload["round_num"])
    for k, v in metrics.items():
        logger.info("%s: %s", k, v)

    logger.info("Per-class support: %s", dict(zip(*np.unique(y_true, return_counts=True))))
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred)
    logger.info("Confusion matrix (rows=true, cols=pred):\n%s", cm)
    return 0


if __name__ == "__main__":
    sys.exit(main())