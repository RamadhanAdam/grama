import pytest
import torch

from grama.federated.client import ClientUpdate
from grama.federated.robust import (
    FedAvgAggregator,
    KrumAggregator,
    MedianAggregator,
    TrimmedMeanAggregator,
    make_aggregator,
)

SHAPES = {"a": torch.Size([2, 2]), "b": torch.Size([3])}


def upd(cid, value, n=100):
    return ClientUpdate(cid, {"a": torch.full((2, 2), float(value)), "b": torch.full((3,), float(value))}, n, 0.1)


def test_fedavg_is_sample_weighted_mean():
    res = FedAvgAggregator().aggregate([upd(0, 1.0, n=100), upd(1, 4.0, n=300)], SHAPES)
    assert torch.allclose(res.global_delta["a"], torch.full((2, 2), 3.25))
    assert res.global_delta["b"].shape == (3,)


def test_median_and_trimmed_mean_ignore_one_outlier():
    ups = [upd(i, 1.0) for i in range(4)] + [upd(9, 1000.0)]
    assert torch.allclose(MedianAggregator().aggregate(ups, SHAPES).global_delta["b"], torch.ones(3))
    assert torch.allclose(TrimmedMeanAggregator(0.2).aggregate(ups, SHAPES).global_delta["b"], torch.ones(3))


def test_krum_rejects_the_outlier():
    torch.manual_seed(0)
    ups = [ClientUpdate(i, {"a": torch.randn(2, 2) * 0.1, "b": torch.randn(3) * 0.1}, 100, 0.1) for i in range(7)]
    ups.append(upd(99, 50.0))
    res = KrumAggregator(assumed_fraction=0.2).aggregate(ups, SHAPES)
    assert res.trust_weights[99] == 0.0
    assert sum(res.trust_weights.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("name", ["fedavg", "median", "trimmed_mean", "krum", "hdbscan"])
def test_factory_builds_every_rule(name):
    cfg = {"aggregator": {"latent_dim": 2, "autoencoder_hidden": 8, "autoencoder_epochs": 5,
                          "hdbscan": {"min_cluster_size": 2, "min_samples": 1}}}
    agg = make_aggregator(name, cfg)
    res = agg.aggregate([upd(i, 0.1 * (i + 1)) for i in range(5)], SHAPES)
    assert set(res.global_delta) == {"a", "b"}
