"""The adaptive attack: the strongest poison the aggregation rule still accepts."""
import json

import pytest
import torch

from grama.attacks.poisoning import adaptive_attack, shift_updates
from grama.federated.aggregator import LatentDensityAggregator
from grama.federated.client import ClientUpdate, label_map_for
from grama.federated.robust import FedAvgAggregator, FlameAggregator, KrumAggregator

SHAPES = {"w": torch.Size([40])}
BAD = [7, 8, 9]


def round_updates(seed=0, poison=3.0):
    """Seven honest updates around +e, three attackers around -e (a targeted poison)."""
    g = torch.Generator().manual_seed(seed)
    e = torch.zeros(40)
    e[:20] = 1.0
    ups = []
    for i in range(10):
        centre = e if i not in BAD else -poison * e
        ups.append(ClientUpdate(i, {"w": centre + 0.1 * torch.randn(40, generator=g)}, 100, 0.1,
                                malicious=i in BAD))
    return ups


def test_adaptive_trains_like_targeted_flip():
    assert label_map_for("adaptive", 6, 0).tolist() == [0] * 6


def test_attackers_send_one_update_between_the_honest_mean_and_their_poison():
    ups = round_updates()
    stack = torch.stack([u.delta_w["w"] for u in ups])
    honest_mean = stack[:7].mean(0)
    bad_mean = stack[7:].mean(0)
    for scale, expected in ((0.0, honest_mean), (1.0, bad_mean), (0.5, (honest_mean + bad_mean) / 2)):
        out = shift_updates(ups, BAD, scale)
        for i in BAD:
            assert torch.allclose(out[i].delta_w["w"], expected, atol=1e-5)
            assert out[i].malicious
        for i in range(7):
            assert torch.equal(out[i].delta_w["w"], ups[i].delta_w["w"])


def test_rules_that_reject_nobody_get_the_largest_scale():
    out, scale = adaptive_attack(round_updates(), BAD, FedAvgAggregator(), SHAPES, max_scale=10.0)
    assert scale == 10.0
    assert all(out[i].malicious for i in BAD)


def test_no_attackers_or_no_honest_clients_changes_nothing():
    ups = round_updates()
    assert adaptive_attack(ups, [], FedAvgAggregator(), SHAPES) == (ups, None)
    assert adaptive_attack(ups, list(range(10)), FedAvgAggregator(), SHAPES) == (ups, None)


@pytest.mark.parametrize("make", [
    lambda: LatentDensityAggregator(latent_dim=2, autoencoder_hidden=8, autoencoder_epochs=30,
                                    min_cluster_size=3, cluster_selection_epsilon=2.0),
    lambda: FlameAggregator(seed=0),
    lambda: KrumAggregator(assumed_fraction=0.3),
])
def test_against_a_detecting_rule_the_attack_is_accepted_but_weaker(make):
    ups = round_updates()
    agg = make()
    # The plain poison is caught...
    torch.manual_seed(0)
    plain = agg.aggregate(ups, SHAPES)
    assert any(plain.trust_weights[i] == 0.0 for i in BAD)
    # ...so the attackers back off to a scale the rule lets through, and every
    # one of their updates is accepted in the real aggregation that follows.
    torch.manual_seed(0)
    out, scale = adaptive_attack(ups, BAD, agg, SHAPES, max_scale=10.0, steps=7)
    assert 0.0 < scale < 1.0
    real = agg.aggregate(out, SHAPES)
    assert all(real.trust_weights[i] > 0.0 for i in BAD)


def test_the_search_leaves_the_random_state_alone():
    ups = round_updates()
    agg = LatentDensityAggregator(latent_dim=2, autoencoder_hidden=8, autoencoder_epochs=10)
    torch.manual_seed(1)
    adaptive_attack(ups, BAD, agg, SHAPES)
    after = torch.rand(3)
    torch.manual_seed(1)
    assert torch.equal(after, torch.rand(3))


def tiny(tmp_path, name):
    from grama.experiments.runner import Experiment
    exp = Experiment("smoke", device="cpu", results_dir=tmp_path / "results" / name)
    exp.data_cfg["dataset"]["processed_dir"] = str(tmp_path / "processed")
    exp.profile["data_overrides"] = {"max_rows_per_class": None, "synthetic_rows_per_class": 1500}
    exp.sim.update(num_clients=5, clients_per_round=5, num_rounds=2, local_epochs=1)
    exp.fed_cfg["aggregator"]["autoencoder_epochs"] = 10
    return exp


def test_a_run_records_the_scale_sent_each_round(tmp_path):
    from grama.experiments.runner import RunSpec
    exp = tiny(tmp_path, "attack")
    exp.prepare_data()
    rec = exp.run_one(RunSpec("grama", "hdbscan", 0.5, "adaptive", 0.4, 0))
    scales = [h["attack_scale"] for h in rec["history"] if "attack_scale" in h]
    assert scales and all(0.0 <= s <= 10.0 for s in scales)
    assert rec["compromised"]


def test_report_of_an_attack_only_profile(tmp_path):
    from grama.experiments.report import make_report
    from grama.experiments.runner import RunSpec
    exp = tiny(tmp_path, "attack")
    # Like cic_adaptive: no main, non-IID or ablation group.
    exp.profile = {k: v for k, v in exp.profile.items() if k not in ("main", "noniid", "ablation")}
    exp.profile["poisoning"] = {"seeds": [0], "attacks": ["adaptive"], "fractions": [0.4], "aggregators": ["hdbscan"]}
    exp._write_profile()
    exp.prepare_data()
    rec = exp.run_one(RunSpec("grama", "hdbscan", 0.5, "adaptive", 0.4, 0))
    exp.runs_path.write_text(json.dumps(rec) + "\n")
    summary = make_report(exp.out_dir).read_text()
    assert "Adaptive (knows the defence)" in summary and "how much poison got through" in summary
    assert "Main comparison" not in summary
    assert (exp.out_dir / "tables" / "adaptive_scale.csv").exists()
