"""Partitions windowed samples across simulated vehicle clients under
Non-IID skew via Dirichlet allocation (Sec 6.2.2).

Lower `alpha` -> more skewed / heterogeneous client label distributions,
approximating divergent driving behaviors and attack exposure across vehicles.
"""
from __future__ import annotations

import numpy as np


def dirichlet_partition(
    labels: np.ndarray,
    num_clients: int,
    alpha: float,
    seed: int = 42,
) -> list[np.ndarray]:
    """Return, for each client, an array of sample indices into `labels`.

    Standard Dirichlet-based Non-IID partitioning (as used in FL benchmarks):
    for each class, draw a proportion vector ~ Dir(alpha) over clients and
    assign that class's samples accordingly.
    """
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    num_classes = int(labels.max()) + 1 if len(labels) else 0
    client_indices: list[list[int]] = [[] for _ in range(num_clients)]

    for c in range(num_classes):
        class_idx = np.where(labels == c)[0]
        rng.shuffle(class_idx)
        if len(class_idx) == 0:
            continue

        proportions = rng.dirichlet(alpha=np.repeat(alpha, num_clients))
        # Convert proportions to cumulative split points over this class's samples.
        split_points = (np.cumsum(proportions) * len(class_idx)).astype(int)[:-1]
        splits = np.split(class_idx, split_points)

        for client_id, idx_chunk in enumerate(splits):
            client_indices[client_id].extend(idx_chunk.tolist())

    return [np.array(sorted(idxs), dtype=int) for idxs in client_indices]


def client_label_distribution(labels: np.ndarray, client_indices: list[np.ndarray]) -> np.ndarray:
    """Diagnostic: rows = clients, cols = classes, values = sample counts.

    Useful for sanity-checking that `alpha` actually produces the intended
    heterogeneity before burning compute on a full federated run.
    """
    num_classes = int(labels.max()) + 1
    dist = np.zeros((len(client_indices), num_classes), dtype=int)
    for i, idxs in enumerate(client_indices):
        for c in labels[idxs]:
            dist[i, c] += 1
    return dist
