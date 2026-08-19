import numpy as np

from grama.data.federated_split import client_label_distribution, dirichlet_partition


def test_partition_covers_all_samples_exactly_once():
    labels = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 2])
    parts = dirichlet_partition(labels, num_clients=4, alpha=1.0, seed=0)

    all_idx = np.concatenate(parts)
    assert len(all_idx) == len(labels)
    assert sorted(all_idx.tolist()) == list(range(len(labels)))


def test_low_alpha_produces_more_skew_than_high_alpha():
    """Lower alpha -> more heterogeneous client label distributions (higher variance)."""
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 4, size=400)

    low_alpha_parts = dirichlet_partition(labels, num_clients=10, alpha=0.1, seed=1)
    high_alpha_parts = dirichlet_partition(labels, num_clients=10, alpha=100.0, seed=1)

    low_dist = client_label_distribution(labels, low_alpha_parts)
    high_dist = client_label_distribution(labels, high_alpha_parts)

    # Normalize rows to proportions, then compare per-client variance across classes.
    low_props = low_dist / low_dist.sum(axis=1, keepdims=True).clip(min=1)
    high_props = high_dist / high_dist.sum(axis=1, keepdims=True).clip(min=1)

    assert low_props.var() > high_props.var()


def test_empty_labels_returns_empty_partitions():
    parts = dirichlet_partition(np.array([]), num_clients=3, alpha=1.0)
    assert len(parts) == 3
    assert all(len(p) == 0 for p in parts)
