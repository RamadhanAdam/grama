"""Standard classification metrics (Sec 6.1)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None = None) -> dict[str, float]:
    """
    y_true, y_pred: (N,) integer class labels
    y_proba: (N, num_classes) predicted probabilities, needed for ROC-AUC
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }

    if y_proba is not None:
        try:
            num_classes = y_proba.shape[1]
            if num_classes == 2:
                metrics["roc_auc"] = roc_auc_score(y_true, y_proba[:, 1])
            else:
                metrics["roc_auc"] = roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro")
        except ValueError as e:
            # e.g. a class missing from y_true in a small eval batch
            metrics["roc_auc"] = float("nan")
            metrics["roc_auc_error"] = str(e)

    return metrics
