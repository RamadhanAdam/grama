"""Figures for the two papers, drawn from the saved runs.

    python3 scripts/paper_figures.py OUT_DIR             # defence paper (paper 1)
    python3 scripts/paper_figures.py OUT_DIR --paper 2   # detector paper (paper 2)

Writes PDF and PNG files into OUT_DIR:
  p1_poisoning      macro-F1 against the share of compromised clients, every rule, four attacks
  p1_seeds40        every seed's macro-F1 at 40% compromised, by rule and attack
  p1_tradeoff       honest updates rejected against macro-F1 at 40%, for the rules that reject updates
  p1_ablation       the defence with one part changed, and its clustering settings (targeted flipping, 40%)
  p2_road           every seed's macro-F1 on ROAD, on its test set and its masquerade set, by detector
  p2_cantt          macro-F1 on the four sets of can-train-and-test, by detector
  p2_ablation       GraMa on ROAD with one part changed
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grama.experiments.report import _plot_style  # noqa: E402
from grama.experiments.stats import load_records  # noqa: E402

RULES = ["fedavg", "median", "trimmed_mean", "krum", "norm_clip", "flame", "foolsgold", "deepsight", "freqfed", "hdbscan"]
LABEL = {"fedavg": "FedAvg", "median": "Median", "trimmed_mean": "Trimmed mean", "krum": "Multi-Krum",
         "norm_clip": "Norm clipping", "flame": "FLAME", "foolsgold": "FoolsGold", "deepsight": "DeepSight",
         "freqfed": "FreqFed", "hdbscan": "Ours"}
# Okabe-Ito and Tol colours, readable in colour-blind vision; ours in black.
COLOR = {"fedavg": "#E69F00", "median": "#56B4E9", "trimmed_mean": "#009E73", "krum": "#D55E00",
         "norm_clip": "#0072B2", "flame": "#CC79A7", "foolsgold": "#882255", "deepsight": "#117733",
         "freqfed": "#332288", "hdbscan": "#000000"}
MARKER = {"fedavg": "s", "median": "^", "trimmed_mean": "v", "krum": "D", "norm_clip": "X", "flame": "P",
          "foolsgold": "*", "deepsight": "h", "freqfed": "<", "hdbscan": "o"}
ATTACKS = [("label_flip", "Label flipping"), ("targeted_flip", "Targeted flipping"),
           ("magnitude_poison", "Magnitude poisoning"), ("alie", "ALIE")]


def f1(r):
    return r["final"]["f1_macro"]


def cic():
    recs = load_records([ROOT / "results" / p for p in ("full", "cic_seeds", "new_baselines")])
    return [r for r in recs if r["model"] == "grama" and r["alpha"] == 0.5 and not r.get("variant")]


def save(fig, out: Path, name: str):
    fig.savefig(out / f"{name}.pdf")
    fig.savefig(out / f"{name}.png")


def poisoning(plt, recs, out):
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.15), sharey=True)
    for ax, (atk, title) in zip(axes, ATTACKS):
        for rule in RULES:
            xs, ys = [], []
            for frac in (0.0, 0.1, 0.2, 0.3, 0.4):
                rs = [r for r in recs if r["aggregator"] == rule and r["fraction"] == frac
                      and r["attack"] == (None if frac == 0 else atk)]
                if rs:
                    xs.append(frac * 100)
                    ys.append(statistics.mean(f1(r) for r in rs))
            ours = rule == "hdbscan"
            ax.plot(xs, ys, color=COLOR[rule], marker=MARKER[rule], ms=3.2 if not ours else 3.8,
                    lw=1.8 if ours else 0.9, alpha=1.0 if ours else 0.85, zorder=3 if ours else 2, label=LABEL[rule])
        ax.set_title(title)
        ax.set_xticks([0, 10, 20, 30, 40])
        ax.set_xlabel("Compromised (%)")
        ax.set_ylim(-0.03, 1.04)
    axes[0].set_ylabel("Macro-F1")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.1), fontsize=7)
    save(fig, out, "p1_poisoning")
    plt.close(fig)


def seeds40(plt, recs, out):
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.6), sharey=True)
    for ax, (atk, title) in zip(axes, ATTACKS):
        for y, rule in enumerate(RULES):
            vals = sorted(f1(r) for r in recs if r["aggregator"] == rule and r["attack"] == atk and r["fraction"] == 0.4)
            ax.scatter(vals, [y] * len(vals), s=13 if rule == "hdbscan" else 10, color=COLOR[rule],
                       marker=MARKER[rule], alpha=0.85, zorder=3, linewidths=0)
            if vals:
                ax.plot([min(vals), max(vals)], [y, y], color=COLOR[rule], lw=0.7, alpha=0.5, zorder=2)
        ax.set_title(title)
        ax.set_xlim(-0.03, 1.04)
        ax.set_xlabel("Macro-F1")
    axes[0].set_yticks(range(len(RULES)))
    axes[0].set_yticklabels([LABEL[r] for r in RULES])
    save(fig, out, "p1_seeds40")
    plt.close(fig)


def tradeoff(plt, recs, out):
    rules = ["krum", "flame", "foolsgold", "deepsight", "freqfed", "hdbscan"]
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 1.85), sharey=True)
    for ax, (atk, title) in zip(axes, [("targeted_flip", "Targeted flipping"), ("label_flip", "Label flipping")]):
        for rule in rules:
            rs = [r for r in recs if r["aggregator"] == rule and r["attack"] == atk and r["fraction"] == 0.4
                  and r["defence"]["fpr"] is not None]
            if not rs:
                continue
            ax.scatter([statistics.mean(r["defence"]["fpr"] for r in rs)], [statistics.mean(f1(r) for r in rs)],
                       s=26 if rule == "hdbscan" else 18, color=COLOR[rule], marker=MARKER[rule], zorder=3,
                       label=LABEL[rule])
        ax.set_title(title, fontsize=8)
        ax.set_xlabel("Honest updates rejected", fontsize=7.5)
        ax.set_xlim(-0.02, 0.8)
        ax.set_ylim(-0.03, 1.04)
    axes[0].set_ylabel("Macro-F1", fontsize=7.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.04), fontsize=6.5)
    save(fig, out, "p1_tradeoff")
    plt.close(fig)


def ablation(plt, out):
    abl = load_records([ROOT / "results" / "def_ablation", ROOT / "results" / "def_grid"])
    rows = [("hdbscan", "Full defence"), ("hdbscan_no_standardize", "No latent rescaling"),
            ("hdbscan_pca", "PCA, not the autoencoder"), ("hdbscan_no_normalize", "No update rescaling"),
            ("hdbscan_no_rescale", "Neither rescaling"), ("hdbscan_raw", "Raw updates, no projection"),
            ("hdbscan_last_layer", "Last layer only"), (None, ""),
            ("hdbscan_eps1", r"$\epsilon$ = 1"), ("hdbscan_eps4", r"$\epsilon$ = 4"), ("hdbscan_eps8", r"$\epsilon$ = 8"),
            ("hdbscan_mcs2", "Min. cluster 2"), ("hdbscan_mcs5", "Min. cluster 5")]
    fig, ax = plt.subplots(figsize=(3.45, 2.6))
    labels = []
    for y, (agg, lab) in enumerate(rows):
        labels.append(lab)
        if agg is None:
            continue
        vals = [f1(r) for r in abl if r["aggregator"] == agg and r["attack"] == "targeted_flip" and r["fraction"] == 0.4]
        m = statistics.mean(vals)
        ax.barh(y, m, color="#000000" if agg == "hdbscan" else "#9AA0A6", height=0.62, zorder=2)
        ax.scatter(vals, [y] * len(vals), s=7, color="#D93025", zorder=3, linewidths=0)
    ticks = [y for y, (agg, _) in enumerate(rows) if agg is not None]
    ax.set_yticks(ticks)
    ax.set_yticklabels([labels[y] for y in ticks], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.04)
    ax.set_xlabel("Macro-F1, targeted flipping, 40% compromised", fontsize=7.5)
    save(fig, out, "p1_ablation")
    plt.close(fig)


DET = ["grama", "transformer_ids", "cnn_bigru", "gcn_gru", "gcn_ids"]
DET_LABEL = {"grama": "GraMa", "cnn_bigru": "CNN-BiGRU", "transformer_ids": "Transformer",
             "gcn_ids": "GCN (last window)", "gcn_gru": "GCN + GRU"}
DET_COLOR = {"grama": "#000000", "cnn_bigru": "#E69F00", "transformer_ids": "#0072B2", "gcn_ids": "#009E73",
             "gcn_gru": "#CC79A7"}


def road(plt, out):
    recs = load_records([ROOT / "results" / "det_road_central"])
    fed = load_records([ROOT / "results" / "det_road_fedavg"])
    panels = [("Test set, centralised", recs, None), ("Masquerade set, centralised", recs, "masquerade"),
              ("Test set, FedAvg", fed, None)]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 1.9), sharey=True)
    for ax, (title, rs, test) in zip(axes, panels):
        for y, m in enumerate(DET):
            vals = [(r["tests"][test] if test else r["final"])["f1_macro"] for r in rs if r["model"] == m and not r.get("variant")]
            ax.scatter(vals, [y] * len(vals), s=12, color=DET_COLOR[m], alpha=0.85, linewidths=0, zorder=3)
            if vals:
                ax.plot([statistics.mean(vals)] * 2, [y - 0.3, y + 0.3], color=DET_COLOR[m], lw=1.6, zorder=4)
        ax.set_title(title)
        ax.set_xlim(0, 1.02)
        ax.set_xlabel("Macro-F1")
    axes[0].set_yticks(range(len(DET)))
    axes[0].set_yticklabels([DET_LABEL[m] for m in DET])
    axes[0].invert_yaxis()
    save(fig, out, "p2_road")
    plt.close(fig)


def cantt(plt, out):
    fig, ax = plt.subplots(figsize=(3.45, 1.95))
    width = 0.16
    for k in range(4):
        rs = load_records([ROOT / "results" / f"det_cantt{k + 1}"])
        for j, m in enumerate(DET):
            vals = [r["final"]["f1_macro"] for r in rs if r["model"] == m]
            x = k + (j - 2) * width
            ax.bar(x, statistics.mean(vals), width * 0.9, color=DET_COLOR[m], label=DET_LABEL[m] if k == 0 else None, zorder=2)
            ax.scatter([x] * len(vals), vals, s=3, color="#5F6368", zorder=3, linewidths=0)
    ax.set_xticks(range(4))
    ax.set_xticklabels([f"Set {k + 1}" for k in range(4)])
    ax.set_ylim(0.4, 1.01)
    ax.set_ylabel("Macro-F1")
    fig.legend(loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=6.5)
    save(fig, out, "p2_cantt")
    plt.close(fig)


def detector_ablation(plt, out):
    rs = load_records([ROOT / "results" / "det_road_ablation", ROOT / "results" / "det_road_central"])
    rows = [("", "Full model"), ("no_residual", "No residual"), ("one_head", "One attention head"),
            ("no_temporal", "No temporal model"), ("mean_pool", "Mean pooling"),
            ("gru_instead_of_mamba", "GRU in place of Mamba"), ("no_id_embedding", "No identifier embedding"),
            ("cooccurrence_edges", "Co-occurrence edges")]
    fig, ax = plt.subplots(figsize=(3.45, 2.0))
    for y, (v, lab) in enumerate(rows):
        vals = [r["final"]["f1_macro"] for r in rs if r["model"] == "grama" and r["aggregator"] == "central"
                and (r.get("variant") or "") == v and r["seed"] < 5]
        ax.barh(y, statistics.mean(vals), color="#000000" if not v else "#9AA0A6", height=0.62, zorder=2)
        ax.scatter(vals, [y] * len(vals), s=7, color="#D93025", zorder=3, linewidths=0)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([lab for _, lab in rows], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("Macro-F1 on ROAD (centralised, five seeds)", fontsize=7.5)
    save(fig, out, "p2_ablation")
    plt.close(fig)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paper = 2 if "--paper" in sys.argv and sys.argv[sys.argv.index("--paper") + 1] == "2" else 1
    args = [a for a in args if a != "2"] if paper == 2 else args
    out = Path(args[0]) if args else ROOT / "results" / "paper_figures"
    out.mkdir(parents=True, exist_ok=True)
    plt = _plot_style()
    if paper == 1:
        recs = cic()
        poisoning(plt, recs, out)
        seeds40(plt, recs, out)
        tradeoff(plt, recs, out)
        ablation(plt, out)
    else:
        road(plt, out)
        cantt(plt, out)
        detector_ablation(plt, out)
    print("wrote figures to", out)


if __name__ == "__main__":
    main()
