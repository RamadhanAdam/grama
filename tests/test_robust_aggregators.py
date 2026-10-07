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


@pytest.mark.parametrize("name", ["fedavg", "median", "trimmed_mean", "krum", "norm_clip", "flame", "hdbscan"])
def test_factory_builds_every_rule(name):
    cfg = {"aggregator": {"latent_dim": 2, "autoencoder_hidden": 8, "autoencoder_epochs": 5,
                          "hdbscan": {"min_cluster_size": 2, "min_samples": 1}}}
    agg = make_aggregator(name, cfg)
    res = agg.aggregate([upd(i, 0.1 * (i + 1)) for i in range(5)], SHAPES)
    assert set(res.global_delta) == {"a", "b"}


def test_norm_clip_bounds_an_oversized_update():
    from grama.federated.robust import NormClipAggregator
    ups = [upd(i, 1.0) for i in range(4)] + [upd(9, 1000.0)]
    res = NormClipAggregator().aggregate(ups, SHAPES)
    assert torch.allclose(res.global_delta["a"], torch.ones(2, 2), atol=1e-5)


def test_flame_drops_updates_pointing_the_other_way():
    from grama.federated.robust import FlameAggregator
    torch.manual_seed(0)
    base = torch.randn(7)
    honest = [ClientUpdate(i, {"a": (base[:4] + 0.05 * torch.randn(4)).reshape(2, 2),
                               "b": base[4:] + 0.05 * torch.randn(3)}, 100, 0.1) for i in range(7)]
    bad = [ClientUpdate(90 + i, {"a": -base[:4].reshape(2, 2) * 3, "b": -base[4:] * 3}, 100, 0.1) for i in range(3)]
    res = FlameAggregator(noise_lambda=0.0).aggregate(honest + bad, SHAPES)
    assert all(res.trust_weights[90 + i] == 0.0 for i in range(3))
    assert sum(res.trust_weights[i] > 0 for i in range(7)) >= 6   # HDBSCAN may drop an edge point


HEAD_SHAPES = {"body": torch.Size([6]), "out_w": torch.Size([4, 5]), "out_b": torch.Size([4])}


def head_upd(cid, gen, scale=1.0, label=None, n=100):
    """An update whose last two entries are an output layer; `label` puts its energy on one class."""
    w = 0.3 + torch.randn(4, 5, generator=gen) * 0.02      # honest: every class moves about equally
    b = 0.3 + torch.randn(4, generator=gen) * 0.02
    if label is not None:
        w, b = w * 0.05, b * 0.05
        w[label] += 3.0
        b[label] += 3.0
    return ClientUpdate(cid, {"body": torch.randn(6, generator=gen) * scale, "out_w": w, "out_b": b}, n, 0.1)


def test_foolsgold_gives_identical_clients_no_weight():
    gen = torch.Generator().manual_seed(0)
    honest = [head_upd(i, gen) for i in range(6)]
    twin = head_upd(90, gen)
    colluders = [twin, ClientUpdate(91, {k: v.clone() for k, v in twin.delta_w.items()}, 100, 0.1)]
    res = make_aggregator("foolsgold", {}).aggregate(honest + colluders, HEAD_SHAPES)
    assert res.trust_weights[90] == 0.0 and res.trust_weights[91] == 0.0
    assert sum(res.trust_weights.values()) == pytest.approx(1.0)


def test_foolsgold_keeps_history_across_rounds():
    gen = torch.Generator().manual_seed(1)
    agg = make_aggregator("foolsgold", {})
    agg.aggregate([head_upd(i, gen) for i in range(5)], HEAD_SHAPES)
    assert set(agg.history) == set(range(5))


def test_deepsight_drops_single_label_updates():
    gen = torch.Generator().manual_seed(2)
    honest = [head_upd(i, gen) for i in range(7)]
    poisoned = [head_upd(50 + i, gen, label=2) for i in range(3)]
    res = make_aggregator("deepsight", {}).aggregate(honest + poisoned, HEAD_SHAPES)
    assert all(res.trust_weights[50 + i] == 0.0 for i in range(3))
    assert sum(res.trust_weights.values()) == pytest.approx(1.0)


def test_freqfed_drops_a_minority_pointing_the_other_way():
    gen = torch.Generator().manual_seed(3)
    base = torch.randn(6, generator=gen)
    ups = []
    for i in range(7):
        w, b = torch.randn(4, 5, generator=gen) * 0.01, torch.randn(4, generator=gen) * 0.01
        ups.append(ClientUpdate(i, {"body": base + 0.05 * torch.randn(6, generator=gen), "out_w": w, "out_b": b}, 100, 0.1))
    for i in range(3):
        ups.append(ClientUpdate(50 + i, {"body": -base, "out_w": torch.zeros(4, 5), "out_b": torch.zeros(4)}, 100, 0.1))
    res = make_aggregator("freqfed", {"aggregator": {"freqfed_low_fraction": 1.0}}).aggregate(ups, HEAD_SHAPES)
    assert all(res.trust_weights[50 + i] == 0.0 for i in range(3))
    assert sum(res.trust_weights.values()) == pytest.approx(1.0)


def test_hdbscan_variants_build_with_one_setting_changed():
    cfg = {"aggregator": {"latent_dim": 2, "autoencoder_hidden": 8, "autoencoder_epochs": 1,
                          "hdbscan": {"min_cluster_size": 3, "min_samples": 1, "cluster_selection_epsilon": 2.0,
                                      "allow_single_cluster": True, "standardize_latent": True}}}
    assert make_aggregator("hdbscan_pca", cfg).latent_method == "pca"
    assert make_aggregator("hdbscan_raw", cfg).latent_method == "raw"
    assert make_aggregator("hdbscan_eps4", cfg).cluster_selection_epsilon == 4.0
    assert make_aggregator("hdbscan_mcs5", cfg).min_cluster_size == 5
    no_rescale = make_aggregator("hdbscan_no_rescale", cfg)
    assert not no_rescale.normalize and not no_rescale.standardize_latent
    assert make_aggregator("hdbscan", cfg).latent_method == "autoencoder"


@pytest.mark.parametrize("method", ["autoencoder", "pca", "raw"])
def test_every_latent_method_separates_a_far_cluster(method):
    gen = torch.Generator().manual_seed(4)
    ups = [head_upd(i, gen, scale=0.1) for i in range(8)]
    ups += [ClientUpdate(60 + i, {"body": torch.full((6,), 5.0) + 0.01 * torch.randn(6, generator=gen),
                                  "out_w": torch.full((4, 5), 5.0), "out_b": torch.full((4,), 5.0)}, 100, 0.1)
            for i in range(2)]
    cfg = {"aggregator": {"latent_dim": 2, "autoencoder_hidden": 8, "autoencoder_epochs": 20,
                          "hdbscan": {"min_cluster_size": 3, "min_samples": 1, "cluster_selection_epsilon": 2.0,
                                      "allow_single_cluster": True, "standardize_latent": True}}}
    name = "hdbscan" if method == "autoencoder" else f"hdbscan_{method}"
    res = make_aggregator(name, cfg).aggregate(ups, HEAD_SHAPES)
    assert sum(res.trust_weights.values()) == pytest.approx(1.0)
    assert all(res.trust_weights[60 + i] < res.trust_weights[0] for i in range(2))
