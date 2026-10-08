import json
import math

import numpy as np
import pytest

from grama.experiments.stats import (bootstrap_ci, compare, holm, load_records, method_name, metric_value,
                                     paired_tests, to_markdown)


def rec(model, agg, seed, f1, variant="", attack=None, fraction=0.0, data_file="d.pt"):
    return {"run_id": f"{model}-{agg}-{variant}-{attack}-{fraction}-s{seed}", "data_file": data_file,
            "model": model, "aggregator": agg, "variant": variant, "attack": attack, "fraction": fraction,
            "alpha": 0.5, "seed": seed, "data_source": "road", "final": {"f1_macro": f1},
            "tests": {"masquerade": {"f1_macro": f1 - 0.1}}}


def test_bootstrap_interval_contains_the_mean_and_shrinks_with_n():
    rng = np.random.default_rng(0)
    small = bootstrap_ci(rng.normal(0.8, 0.05, 5))
    large = bootstrap_ci(rng.normal(0.8, 0.05, 200))
    assert small[1] <= small[0] <= small[2]
    assert (large[2] - large[1]) < (small[2] - small[1])
    assert math.isnan(bootstrap_ci([0.9])[1])


def test_paired_test_finds_a_consistent_shift_and_not_noise():
    base = np.linspace(0.70, 0.80, 10)
    shifted = paired_tests(base + 0.05, base)
    assert shifted["mean_diff"] == pytest.approx(0.05)
    assert shifted["ci_lo"] > 0 and shifted["wilcoxon_p"] < 0.01
    assert shifted["min_wilcoxon_p"] == pytest.approx(2 / 1024)
    rng = np.random.default_rng(1)
    noise = paired_tests(base + rng.normal(0, 0.05, 10), base)
    assert noise["ci_lo"] < 0 < noise["ci_hi"]
    same = paired_tests(base, base)
    assert same["wilcoxon_p"] == 1.0


def test_five_seeds_cannot_reach_005_with_wilcoxon():
    base = np.linspace(0.70, 0.80, 5)
    res = paired_tests(base + 0.1, base)
    assert res["wilcoxon_p"] == pytest.approx(0.0625)


def test_holm_adjustment():
    adj = holm([0.01, 0.04, 0.03, math.nan])
    assert adj[0] == pytest.approx(0.03) and adj[2] == pytest.approx(0.06) and adj[1] == pytest.approx(0.06)
    assert math.isnan(adj[3])


def test_compare_pairs_on_the_seed_and_uses_the_reference():
    records = []
    for seed in range(10):
        records.append(rec("grama", "central", seed, 0.90 + 0.001 * seed))
        records.append(rec("cnn_bigru", "central", seed, 0.85 + 0.001 * seed))
        records.append(rec("gcn_ids", "central", seed, 0.90 + 0.001 * seed))
    out = compare(records, "final.f1_macro", "grama_central", n_boot=500)
    assert len(out) == 1
    rows = {r["method"]: r for r in out[0]["rows"]}
    assert "vs_reference" not in rows["grama_central"]
    assert rows["cnn_bigru_central"]["vs_reference"]["mean_diff"] == pytest.approx(-0.05)
    assert rows["cnn_bigru_central"]["vs_reference"]["wilcoxon_p_holm"] < 0.05
    assert rows["gcn_ids_central"]["vs_reference"]["wilcoxon_p"] == 1.0
    text = to_markdown(out, "final.f1_macro")
    assert "cnn_bigru_central" in text and "grama_central (reference)" in text


def test_compare_keeps_attack_cells_apart_and_reads_other_metrics():
    records = [rec("grama", "hdbscan", s, 0.9, attack="alie", fraction=0.4) for s in range(3)]
    records += [rec("grama", "flame", s, 0.5, attack="alie", fraction=0.4) for s in range(3)]
    records += [rec("grama", "hdbscan", s, 0.95) for s in range(3)]
    out = compare(records, "tests.masquerade.f1_macro", "grama_hdbscan", n_boot=200)
    assert len(out) == 2
    attack = [o for o in out if o["condition"]["attack"] == "alie"][0]
    assert {r["method"] for r in attack["rows"]} == {"grama_hdbscan", "grama_flame"}


def test_variants_are_separate_methods_and_missing_metrics_are_skipped():
    assert method_name(rec("grama", "central", 0, 0.9, variant="no_temporal")) == "grama_central+no_temporal"
    assert metric_value({"final": {}}, "final.f1_macro") is None
    assert metric_value({"final": {"f1_macro": 0.5}}, "final.f1_macro") == 0.5


def test_load_records_drops_runs_copied_between_profiles(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    r = rec("grama", "central", 0, 0.9)
    (a / "runs.jsonl").write_text(json.dumps(r) + "\n")
    (b / "runs.jsonl").write_text(json.dumps({**r, "copied_from": "a"}) + "\n" + json.dumps(rec("grama", "central", 1, 0.8)) + "\n")
    assert len(load_records([a, b, tmp_path / "missing"])) == 2
