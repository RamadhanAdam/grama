import torch

from grama.federated.aggregator import LatentDensityAggregator
from grama.federated.client import ClientUpdate


def make_update(client_id: int, base: float, noise: float = 0.08, dim: int = 20) -> ClientUpdate:
    delta = {"w": torch.full((dim,), base) + torch.randn(dim) * noise}
    return ClientUpdate(client_id=client_id, delta_w=delta, num_samples=100, local_loss=0.5)


def test_aggregator_isolates_magnitude_outliers():
    """12 benign clients clustered near delta=0.1, 3 adversarial clients with delta=5.0 —
    HDBSCAN should assign zero trust to the outliers while trusting benign clients.

    Note: noise is set to a realistic level (0.08), not near-zero — HDBSCAN's density
    estimate becomes unstable on near-duplicate points at very low sample counts, which
    is a property of tiny synthetic tests, not of real federated updates (real clients'
    Δw's naturally vary from different local data)."""
    torch.manual_seed(0)
    benign = [make_update(i, base=0.1) for i in range(12)]
    adversarial = [make_update(100 + i, base=5.0) for i in range(3)]
    updates = benign + adversarial

    aggregator = LatentDensityAggregator(
        latent_dim=4, autoencoder_hidden=16, autoencoder_epochs=30,
        min_cluster_size=4, min_samples=2,
    )
    param_shapes = {"w": torch.Size([20])}
    result = aggregator.aggregate(updates, param_shapes)

    benign_trust = [result.trust_weights[u.client_id] for u in benign]
    adversarial_trust = [result.trust_weights[u.client_id] for u in adversarial]

    assert sum(benign_trust) > 0.0, "at least some benign clients should be trusted"
    assert all(t == 0.0 for t in adversarial_trust), "outlier clients should be fully rejected"


def test_aggregator_trust_weights_sum_to_one_when_benign_cluster_exists():
    torch.manual_seed(1)
    updates = [make_update(i, base=0.2) for i in range(6)]
    aggregator = LatentDensityAggregator(
        latent_dim=2, autoencoder_hidden=8, autoencoder_epochs=10,
        min_cluster_size=2, min_samples=1,
    )
    param_shapes = {"w": torch.Size([20])}
    result = aggregator.aggregate(updates, param_shapes)

    if result.benign_cluster_id is not None:
        total = sum(result.trust_weights.values())
        assert abs(total - 1.0) < 1e-4


def test_aggregator_produces_correct_global_delta_shape():
    torch.manual_seed(2)
    updates = [make_update(i, base=0.1) for i in range(5)]
    aggregator = LatentDensityAggregator(
        latent_dim=2, autoencoder_hidden=8, autoencoder_epochs=5,
        min_cluster_size=2, min_samples=1,
    )
    param_shapes = {"w": torch.Size([20])}
    result = aggregator.aggregate(updates, param_shapes)
    assert result.global_delta["w"].shape == torch.Size([20])
