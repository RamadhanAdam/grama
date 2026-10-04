"""Evaluation metrics (Sec 6.1) and the evaluation loop used by the experiments."""
from __future__ import annotations

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None = None,
                    num_classes: int | None = None, benign_class: int = 0, present_only: bool = False) -> dict:
    """
    y_true, y_pred: (N,) integer class labels
    y_proba: (N, num_classes) predicted probabilities, needed for ROC-AUC

    Besides the multi-class scores, reports the two numbers an IDS is judged
    on: detection rate (attacks flagged as any attack) and false alarm rate
    (benign traffic flagged as an attack).

    present_only: average the macro scores over the classes in y_true only.
    For test sets that lack some classes (ROAD's masquerade set has no
    fuzzing), so an absent class doesn't count as an F1 of zero.
    """
    labels = list(range(num_classes)) if num_classes else None
    if present_only:
        labels = sorted(int(c) for c in np.unique(y_true))
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
    }

    attack = y_true != benign_class
    flagged = y_pred != benign_class
    metrics["detection_rate"] = float(flagged[attack].mean()) if attack.any() else float("nan")
    metrics["false_alarm_rate"] = float(flagged[~attack].mean()) if (~attack).any() else float("nan")

    if y_proba is not None:
        try:
            if y_proba.shape[1] == 2:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
            else:
                present = np.unique(y_true)
                if len(present) < 2:
                    raise ValueError("only one class present")
                # One-vs-rest AUC over the classes present in y_true.
                metrics["roc_auc"] = float(np.mean([
                    roc_auc_score(y_true == c, y_proba[:, c]) for c in present
                ]))
        except ValueError:
            metrics["roc_auc"] = float("nan")
    return metrics


def detailed_metrics(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> dict:
    """Per-class F1 and the confusion matrix (rows = true, cols = predicted)."""
    labels = list(range(num_classes))
    return {
        "f1_per_class": f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0).tolist(),
        "support": np.bincount(y_true, minlength=num_classes).tolist(),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }


@torch.no_grad()
def predict(model: torch.nn.Module, dataset, device: str = "cpu", batch_size: int = 512):
    """Run the model over a dataset with get_batch(). Returns y_true, y_pred, y_proba."""
    model = model.to(device).eval()
    ys, preds, probas = [], [], []
    for chunk in torch.arange(len(dataset)).split(batch_size):
        *inputs, y = dataset.get_batch(chunk)
        logits = model(*[t.to(device, non_blocking=True) for t in inputs])
        proba = torch.softmax(logits.float(), dim=-1).cpu()
        ys.append(y.cpu().numpy())
        preds.append(proba.argmax(dim=-1).numpy())
        probas.append(proba.numpy())
    return np.concatenate(ys), np.concatenate(preds), np.concatenate(probas)


def evaluate(model, dataset, num_classes: int, device: str = "cpu", batch_size: int = 512,
             detailed: bool = False, present_only: bool = False) -> dict:
    y_true, y_pred, y_proba = predict(model, dataset, device, batch_size)
    out = compute_metrics(y_true, y_pred, y_proba, num_classes=num_classes, present_only=present_only)
    if detailed:
        out.update(detailed_metrics(y_true, y_pred, num_classes))
    return out
