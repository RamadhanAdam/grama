"""Numbers for the two papers, straight from the saved runs.

    python3 scripts/paper_tables.py paper1      # defence paper
    python3 scripts/paper_tables.py paper2      # detector paper

Each table is printed as Markdown: mean ± standard deviation over seeds, with n. The 95% bootstrap
intervals and the paired tests are in results/stats/ (make stats-paper1, make stats-paper2). Runs that
appear in several folders (copied reference runs) count once, as in the stats.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grama.experiments.stats import load_records, metric_value  # noqa: E402

RULE = {"fedavg": "FedAvg", "median": "Median", "trimmed_mean": "Trimmed mean", "krum": "Multi-Krum",
        "norm_clip": "Norm clipping", "flame": "FLAME", "foolsgold": "FoolsGold", "deepsight": "DeepSight",
        "freqfed": "FreqFed", "hdbscan": "Ours"}
RULES = list(RULE)
ATTACKS = ["label_flip", "targeted_flip", "magnitude_poison", "alie"]


def runs(*profiles: str) -> list[dict]:
    return load_records([ROOT / "results" / p for p in profiles])


def cell(recs, metric="final.f1_macro", digits=3) -> str:
    v = [x for x in (metric_value(r, metric) for r in recs) if x is not None]
    if not v:
        return "–"
    sd = statistics.stdev(v) if len(v) > 1 else 0.0
    return f"{statistics.mean(v):.{digits}f} ± {sd:.{digits}f} (n={len(v)})"


def pick(recs, **kw):
    return [r for r in recs if all(r.get(k) == v for k, v in kw.items())]


def table(title, header, rows):
    print(f"\n### {title}\n")
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join("---" for _ in header) + "|")
    for row in rows:
        print("| " + " | ".join(row) + " |")


def paper1():
    cic = runs("full", "cic_seeds", "new_baselines")
    clean = [r for r in cic if r["attack"] is None and r["alpha"] == 0.5 and not r.get("variant") and r["model"] == "grama"]
    table("CIC-IoV2024 without attack", ["Rule", "Macro-F1", "FPR"],
          [[RULE[a], cell(pick(clean, aggregator=a)), cell(pick(clean, aggregator=a), "defence.fpr")]
           for a in RULES])
    for frac in (0.1, 0.2, 0.3, 0.4):
        rows = []
        for a in RULES:
            rows.append([RULE[a]] + [cell(pick(cic, model="grama", aggregator=a, attack=t, fraction=frac, alpha=0.5))
                                     for t in ATTACKS])
        table(f"CIC-IoV2024, {int(frac * 100)}% compromised: macro-F1", ["Rule"] + ATTACKS, rows)
    for frac in (0.2, 0.3, 0.4):
        rows = []
        for a in ["krum", "flame", "foolsgold", "deepsight", "freqfed", "hdbscan"]:
            rs = pick(cic, model="grama", aggregator=a, fraction=frac, alpha=0.5)
            rows.append([RULE[a]] + [f"{cell(pick(rs, attack=t), 'defence.tpr', 2)} / {cell(pick(rs, attack=t), 'defence.fpr', 2)}"
                                     for t in ATTACKS])
        table(f"CIC-IoV2024, {int(frac * 100)}% compromised: TPR / FPR", ["Rule"] + ATTACKS, rows)

    abl = runs("def_ablation")
    names = {"hdbscan": "full defence", "hdbscan_pca": "PCA instead of the autoencoder",
             "hdbscan_raw": "HDBSCAN on the raw updates", "hdbscan_no_rescale": "neither rescaling step",
             "hdbscan_no_normalize": "no centring and rescaling of the updates",
             "hdbscan_no_standardize": "no rescaling of the latent points",
             "hdbscan_last_layer": "last layer only"}
    rows = []
    for a, n in names.items():
        rows.append([n] + [cell(pick(abl, aggregator=a, attack=t, fraction=f)) for t, f in
                           [(None, 0.0), ("targeted_flip", 0.2), ("targeted_flip", 0.4), ("alie", 0.2), ("alie", 0.4)]]
                    + [cell(pick(abl, aggregator=a, attack="targeted_flip", fraction=0.4), "defence.fpr", 2)])
    table("Defence ablation (CIC-IoV2024)", ["Variant", "clean", "TF 20", "TF 40", "ALIE 20", "ALIE 40", "FPR at TF 40"], rows)

    grid = runs("def_grid")
    rows = []
    for a in ["hdbscan_eps1", "hdbscan", "hdbscan_eps4", "hdbscan_eps8", "hdbscan_mcs2", "hdbscan_mcs5"]:
        rows.append([a] + [cell(pick(grid, aggregator=a, attack=t, fraction=f)) for t, f in
                           [(None, 0.0), ("targeted_flip", 0.2), ("targeted_flip", 0.4), ("alie", 0.2), ("alie", 0.4)]]
                    + [cell(pick(grid, aggregator=a, attack=None), "defence.fpr", 2)])
    table("Clustering settings (CIC-IoV2024)", ["Setting", "clean", "TF 20", "TF 40", "ALIE 20", "ALIE 40", "FPR clean"], rows)

    dup = runs("alie_duplicates")
    rows = []
    for a in ["fedavg", "norm_clip", "flame", "foolsgold", "hdbscan"]:
        rows.append([RULE[a]] + [cell(pick(dup, aggregator=a, attack=t, fraction=f)) for t, f in
                                 [("alie", 0.2), ("alie", 0.4), ("alie_noisy", 0.2), ("alie_noisy", 0.4)]]
                    + [cell(pick(dup, aggregator=a, attack="alie_noisy", fraction=0.4), "defence.tpr", 2)])
    table("ALIE with identical and with noisy colluding updates", ["Rule", "ALIE 20", "ALIE 40", "noisy 20", "noisy 40", "TPR noisy 40"], rows)

    c40 = runs("clients40")
    rows = []
    for a in ["fedavg", "norm_clip", "flame", "hdbscan"]:
        rows.append([RULE[a]] + [cell(pick(c40, aggregator=a, attack=t, fraction=f)) for t, f in
                                 [(None, 0.0), ("targeted_flip", 0.2), ("targeted_flip", 0.4), ("alie", 0.2), ("alie", 0.4)]]
                    + [cell(pick(c40, aggregator=a, attack="targeted_flip", fraction=0.4), "defence.fpr", 2)])
    table("40 clients, 20 per round", ["Rule", "clean", "TF 20", "TF 40", "ALIE 20", "ALIE 40", "FPR at TF 40"], rows)

    for name, profs in [("CIC-IoV2024", ("cic_adaptive", "cic_adaptive_new")), ("set 1", ("cantt1_adaptive",))]:
        ad = runs(*profs)
        rows = []
        for a in ["fedavg", "norm_clip", "flame", "foolsgold", "deepsight", "freqfed", "hdbscan"]:
            rs = pick(ad, aggregator=a, attack="adaptive")
            if not rs:
                continue
            row = [RULE[a]]
            for f in (0.2, 0.4):
                sub = pick(rs, fraction=f)
                g = [h["attack_scale"] for r in sub for h in r["history"] if h.get("attack_scale") is not None]
                row += [cell(sub), f"{statistics.mean(g):.2f}" if g else "–", cell(sub, "defence.fpr", 2)]
            rows.append(row)
        table(f"Adaptive attack, {name}", ["Rule", "F1 20", "gamma 20", "FPR 20", "F1 40", "gamma 40", "FPR 40"], rows)

    for name, profs in [("ROAD", ("road", "road_new_baselines")), ("can-train-and-test set 1", ("cantt1", "cantt1_new_baselines"))]:
        o = runs(*profs)
        rows = []
        for a in ["fedavg", "norm_clip", "flame", "foolsgold", "deepsight", "freqfed", "hdbscan"]:
            rows.append([RULE[a]] + [cell(pick(o, model="grama", aggregator=a, attack=t, fraction=f)) for t, f in
                                     [(None, 0.0), ("targeted_flip", 0.2), ("targeted_flip", 0.4), ("alie", 0.2), ("alie", 0.4)]]
                        + [cell(pick(o, model="grama", aggregator=a, attack="targeted_flip", fraction=0.4), "defence.fpr", 2)])
        table(f"{name}: macro-F1", ["Rule", "clean", "TF 20", "TF 40", "ALIE 20", "ALIE 40", "FPR at TF 40"], rows)


DETECTORS = {"grama": "GraMa", "cnn_bigru": "CNN-BiGRU", "transformer_ids": "Transformer",
             "gcn_ids": "GCN (last window)", "gcn_gru": "GCN + GRU"}


def paper2():
    tests = {"masquerade": "masquerade", "unknown_vehicle": "unknown car", "unknown_attack": "unknown attacks",
             "unknown_vehicle_and_attack": "unknown car and attacks"}
    for prof in ["det_road_central", "det_road_fedavg", "det_cantt1", "det_cantt2", "det_cantt3", "det_cantt4", "det_cic"]:
        rs = runs(prof)
        models = sorted({r["model"] for r in rs if not r.get("variant")}, key=lambda m: list(DETECTORS).index(m) if m in DETECTORS else 99)
        extra = sorted({t for r in rs for t in r.get("tests", {})})
        header = ["Model", "macro-F1", "detection", "false alarm"] + [tests.get(t, t) for t in extra] + ["params"]
        rows = []
        for m in models:
            sub = [r for r in rs if r["model"] == m and not r.get("variant")]
            rows.append([DETECTORS.get(m, m), cell(sub), cell(sub, "final.detection_rate"), cell(sub, "final.false_alarm_rate")]
                        + [cell(sub, f"tests.{t}.f1_macro") for t in extra] + [f"{sub[0].get('params', 0):,}"])
        table(prof, header, rows)
    for prof, test in [("det_road_central", None), ("det_road_central", "masquerade"), ("det_road_fedavg", None)]:
        rs = runs(prof)
        names = json.loads((ROOT / "results" / prof / "dataset.json").read_text())["class_names"]
        rows = []
        for m in DETECTORS:
            sub = [r for r in rs if r["model"] == m and not r.get("variant")]
            if not sub:
                continue
            per = [(r["tests"][test] if test else r["final"])["f1_per_class"] for r in sub]
            rows.append([DETECTORS[m]] + [f"{statistics.mean(p[i] for p in per):.3f}" for i in range(len(names))])
        table(f"{prof} per-class F1" + (f" ({test})" if test else ""), ["Model"] + names, rows)
    eff = json.loads((ROOT / "results" / "det_road_central" / "efficiency.json").read_text())
    table("cost (ROAD build)", ["Model", "params", "KB", "CPU ms", "GPU ms", "seq/s"],
          [[k, f"{v['params']:,}", f"{v['size_kb']:.1f}", f"{v['cpu_1thread_ms_per_sequence']:.2f}",
            f"{v.get('gpu_ms_per_sequence', 0):.2f}", f"{v.get('gpu_sequences_per_second', 0):,.0f}"] for k, v in eff.items()])
    rows = []
    for prof in ["det_road_central", "det_cantt1", "det_cantt2", "det_cantt3", "det_cantt4", "det_cic"]:
        d = json.loads((ROOT / "results" / prof / "dataset.json").read_text())
        rows.append([prof, str(d["num_nodes"]), str(d["class_counts"].get("train")), str(d["class_counts"].get("test")),
                     json.dumps(d.get("other_node_share", {}))])
    table("datasets", ["profile", "nodes", "train", "test", "unseen-ID share"], rows)
    rs = runs("det_road_ablation")
    variants = sorted({r.get("variant", "") for r in rs})
    rows = [[v or "full", cell([r for r in rs if r.get("variant", "") == v]),
             cell([r for r in rs if r.get("variant", "") == v], "tests.masquerade.f1_macro"),
             f"{[r for r in rs if r.get('variant', '') == v][0].get('params', 0):,}"] for v in variants]
    table("det_road_ablation", ["Variant", "macro-F1", "masquerade", "params"], rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paper", choices=["paper1", "paper2"])
    {"paper1": paper1, "paper2": paper2}[parser.parse_args().paper]()
