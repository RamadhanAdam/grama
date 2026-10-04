"""Turns results/<profile>/runs.jsonl into tables, figures and summary.md.

    python -m grama.experiments.report results/quick

Tables go to tables/ as CSV (for the paper) and into summary.md as Markdown.
Figures go to figures/ as PNG (to look at) and PDF (to put in LaTeX).
Values are mean ± standard deviation over seeds; with one seed, just the mean.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

MODEL_LABEL = {"grama": "GraMa", "cnn_bigru": "CNN-BiGRU"}
AGG_LABEL = {"hdbscan": "HDBSCAN (ours)", "fedavg": "FedAvg", "median": "Median",
             "trimmed_mean": "Trimmed mean", "krum": "Multi-Krum", "norm_clip": "Norm clipping",
             "flame": "FLAME", "central": "centralised"}
ATTACK_LABEL = {"label_flip": "Label flipping", "targeted_flip": "Targeted flipping (attack -> benign)",
                "magnitude_poison": "Magnitude poisoning", "alie": "ALIE (crafted to look honest)"}
METRIC_LABEL = {"accuracy": "Accuracy", "precision_macro": "Macro-P", "recall_macro": "Macro-R",
                "f1_macro": "Macro-F1", "roc_auc": "ROC-AUC", "detection_rate": "Detection rate",
                "false_alarm_rate": "False alarm rate"}
VARIANT_LABEL = {
    "": "GraMa (full)",
    "no_residual": "without residual connections in the GAT",
    "no_id_embedding": "without CAN-ID embeddings",
    "mean_pool": "mean pooling instead of attention pooling",
    "cooccurrence_edges": "co-occurrence edges instead of transition edges",
    "transition_edges": "transition edges instead of co-occurrence edges",
    "gru_instead_of_mamba": "GRU instead of Mamba",
    "no_temporal": "no temporal model (last window only)",
}
DATA_LABEL = {"road": "ROAD", "can_train_test": "can-train-and-test"}
TEST_LABEL = {"masquerade": "Masquerade attacks only",
              "unknown_vehicle": "Unknown car, known attacks",
              "unknown_attack": "Known car, unknown attacks",
              "unknown_vehicle_and_attack": "Unknown car, unknown attacks"}
# Okabe-Ito colours (readable in colour-blind vision and in greyscale print).
COLORS = {"hdbscan": "#000000", "fedavg": "#E69F00", "median": "#56B4E9", "trimmed_mean": "#009E73",
          "krum": "#D55E00", "norm_clip": "#0072B2", "flame": "#CC79A7", "central": "#777777"}
MARKERS = {"hdbscan": "o", "fedavg": "s", "median": "^", "trimmed_mean": "v", "krum": "D",
           "norm_clip": "X", "flame": "P", "central": "x"}


def method_label(model: str, agg: str) -> str:
    if agg == "central":
        return f"{MODEL_LABEL[model]}, centralised"
    return f"{MODEL_LABEL[model]} + {AGG_LABEL.get(agg, agg)}"


def load_runs(results_dir: Path) -> list[dict]:
    path = results_dir / "runs.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _vals(runs, key):
    return [r["final"].get(key) for r in runs if r["final"].get(key) is not None]


def mean_std(values, digits=4) -> str:
    values = [v for v in values if v is not None]
    if not values:
        return "–"
    if len(values) == 1:
        return f"{values[0]:.{digits}f}"
    return f"{np.mean(values):.{digits}f} ± {np.std(values):.{digits}f}"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def select(runs, **kw):
    out = []
    for r in runs:
        if all((r.get(k) == v) if not callable(v) else v(r.get(k)) for k, v in kw.items()):
            out.append(r)
    return out


def _plot_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "serif", "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
        "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": "#dddddd", "grid.linewidth": 0.6, "figure.dpi": 110, "savefig.dpi": 220,
        "savefig.bbox": "tight",
    })
    return plt


def _save(fig, fig_dir: Path, name: str) -> str:
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_dir / f"{name}.png")
    fig.savefig(fig_dir / f"{name}.pdf")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return f"figures/{name}.png"


def make_report(results_dir: str | Path) -> Path:
    results_dir = Path(results_dir)
    all_runs = load_runs(results_dir)
    if not all_runs:
        raise FileNotFoundError(f"No runs in {results_dir / 'runs.jsonl'} yet.")
    data = json.loads((results_dir / "dataset.json").read_text())
    # Only runs on the current dataset build; older builds (e.g. another split) stay in the file but out of the tables.
    if any("data_file" in r for r in all_runs):
        all_runs = [r for r in all_runs if r.get("data_file") == data["data_file"]]
        if not all_runs:
            raise FileNotFoundError(f"No runs on the current dataset {data['data_file']} yet.")
    runs = [r for r in all_runs if not r.get("variant")]       # full model only
    ablation_runs = [r for r in all_runs if r.get("variant")]
    profile = json.loads((results_dir / "profile.json").read_text())
    eff_path = results_dir / "efficiency.json"
    eff = json.loads(eff_path.read_text()) if eff_path.exists() else None
    tables, fig_dir = results_dir / "tables", results_dir / "figures"
    alpha0 = profile["alpha"]
    class_names = data["class_names"]
    plt = _plot_style()

    out = []
    synthetic = data["source"] == "synthetic"
    out.append(f"# GraMa results: `{profile['profile']}` profile\n")
    out.append(f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} from {len(all_runs)} runs.\n")
    if synthetic:
        out.append("> **Synthetic data.** This profile only checks that the code runs end to end. "
                   "Don't report these numbers.\n")
    sim = profile["simulation"]
    out.append(
        f"- Data: {DATA_LABEL.get(data['source'], data['source'])} (`{data['data_file']}`), "
        f"{data['num_nodes']} CAN-ID nodes, "
        f"windows of {data['window_size']} frames (stride {data['stride']}), sequences of "
        f"{data['seq_len']} windows, edges: {data['edge_mode']}"
        + (f", attack frames injected into benign traffic at ratio {data['injection']['attack_ratio']}"
           if data.get("injection") else "") + ".")
    out.append(f"- Federated setting: {sim['num_clients']} clients, {sim['clients_per_round']} per round, "
               f"{sim['num_rounds']} rounds, {sim['local_epochs']} local epoch(s), batch {sim['local_batch_size']}, "
               f"lr {sim['local_lr']}, Dirichlet alpha {alpha0} unless stated.")
    out.append(f"- Hardware: {data['device']}.")
    seeds = sorted({r["seed"] for r in all_runs})
    out.append(f"- Seeds: {seeds}. Cells are mean ± std over seeds where there is more than one.\n")

    header = ["Split"] + class_names
    rows = [[s] + [str(c) for c in data["class_counts"][s]] for s in data["class_counts"]]
    out.append("Sequences per class:\n\n" + md_table(header, rows) + "\n")

    figures = []

    # ---------------------------------------------------------------- 1. main
    clean0 = select(runs, attack=None, alpha=alpha0)
    methods = []
    for m in profile.get("main_methods", []):
        model, agg = m
        rs = select(clean0, model=model, aggregator=agg)
        if rs:
            methods.append((model, agg, rs))
    if methods:
        keys = list(METRIC_LABEL)
        header = ["Method"] + [METRIC_LABEL[k] for k in keys] + ["Params", "Train time (s)"]
        rows = []
        for model, agg, rs in methods:
            rows.append([method_label(model, agg)] + [mean_std(_vals(rs, k)) for k in keys]
                        + [f"{rs[0]['params']:,}", f"{np.mean([r['train_seconds'] for r in rs]):.0f}"])
        write_csv(tables / "main.csv", header, rows)
        out.append("## 1. Main comparison, no attack (Sec 6.2.1)\n\n" + md_table(header, rows) + "\n")
        out.append("Detection rate = attack sequences flagged as any attack; false alarm rate = benign "
                   "sequences flagged as an attack.\n")

        extra = data.get("extra_tests") or []
        if extra:
            keys = ("f1_macro", "detection_rate", "false_alarm_rate")
            header = ["Method"] + [f"{TEST_LABEL.get(t, t)}: {METRIC_LABEL[k]}" for t in extra for k in keys]
            rows = []
            for model, agg, rs in methods:
                row = [method_label(model, agg)]
                for t in extra:
                    for k in keys:
                        row.append(mean_std([r.get("tests", {}).get(t, {}).get(k) for r in rs]))
                rows.append(row)
            write_csv(tables / "other_tests.csv", header, rows)
            share = data.get("other_node_share") or {}
            unseen = ", ".join(f"{TEST_LABEL.get(t, t).lower()} {share[t]:.0%}" for t in extra if t in share)
            out.append("### Other test sets\n\nThe same models, tested on the extra sets. Macro scores are "
                       "averaged over the classes each set contains."
                       + (f" Frames with a CAN ID training never saw: test {share.get('test', 0):.0%}, {unseen}."
                          if share else "") + "\n\n" + md_table(header, rows) + "\n")

        header = ["Method"] + class_names
        rows = []
        for model, agg, rs in methods:
            per = np.array([r["final"]["f1_per_class"] for r in rs])
            rows.append([method_label(model, agg)] + [f"{v:.4f}" for v in per.mean(0)])
        write_csv(tables / "per_class_f1.csv", header, rows)
        out.append("### Per-class F1\n\n" + md_table(header, rows) + "\n")

        # convergence
        fig, ax = plt.subplots(figsize=(4.2, 2.8))
        for model, agg, rs in methods:
            if agg == "central":
                ax.axhline(np.mean(_vals(rs, "f1_macro")), color=COLORS["central"], ls="--", lw=1,
                           label=method_label(model, agg))
                continue
            curves = {}
            for r in rs:
                for h in r["history"]:
                    if h.get("f1_macro") is not None:
                        curves.setdefault(h["round"], []).append(h["f1_macro"])
            xs = sorted(curves)
            ys = [np.mean(curves[x]) for x in xs]
            ls = "-" if model == "grama" else ":"
            ax.plot(xs, ys, ls, color=COLORS.get(agg, "#444444"), marker=MARKERS.get(agg, "."),
                    ms=3, lw=1.2, label=method_label(model, agg))
        ax.set_xlabel("Communication round")
        ax.set_ylabel("Test macro-F1")
        ax.legend(frameon=False)
        figures.append(("Test macro-F1 per round, no attack", _save(fig, fig_dir, "convergence")))

        # confusion matrix of the first method (GraMa + HDBSCAN when present)
        model, agg, rs = methods[0]
        cm = np.array(rs[0]["final"]["confusion_matrix"], dtype=float)
        cmn = cm / cm.sum(1, keepdims=True).clip(min=1)
        fig, ax = plt.subplots(figsize=(4.0, 3.4))
        ax.imshow(cmn, cmap="Greys", vmin=0, vmax=1)
        ax.grid(False)
        short = [c.replace("spoofing-", "") for c in class_names]
        ax.set_xticks(range(len(short)), short, rotation=40, ha="right")
        ax.set_yticks(range(len(short)), short)
        for i in range(len(short)):
            for j in range(len(short)):
                if cm[i, j] > 0:
                    ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if cmn[i, j] > 0.5 else "black")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"{method_label(model, agg)}, seed {rs[0]['seed']}")
        figures.append(("Confusion matrix (row-normalised)", _save(fig, fig_dir, "confusion_matrix")))

        # client label distribution
        counts = np.array(rs[0]["client_label_counts"], dtype=float)
        if counts.shape[0] > 1:
            props = counts / counts.sum(1, keepdims=True).clip(min=1)
            fig, ax = plt.subplots(figsize=(4.6, 2.6))
            bottom = np.zeros(len(props))
            greys = plt.cm.Greys(np.linspace(0.15, 0.9, len(class_names)))
            for c in range(len(class_names)):
                ax.bar(range(len(props)), props[:, c], bottom=bottom, color=greys[c], width=0.85,
                       label=short[c], edgecolor="white", linewidth=0.3)
                bottom += props[:, c]
            ax.set_xlabel("Client")
            ax.set_ylabel("Share of local data")
            ax.set_title(f"Client label mix, Dirichlet alpha = {alpha0}")
            ax.legend(frameon=False, ncol=3, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.22))
            ax.grid(False)
            figures.append(("Label mix per client", _save(fig, fig_dir, "client_distribution")))

    # ---------------------------------------------------------------- 2. non-IID
    noniid = profile.get("noniid")
    if noniid:
        header = ["Dirichlet alpha"] + [f"{AGG_LABEL[a]} macro-F1" for a in noniid["aggregators"]] \
                 + [f"{AGG_LABEL[a]} accuracy" for a in noniid["aggregators"]]
        rows = []
        for alpha in noniid["alphas"]:
            row = [f"{alpha:g}"]
            for key in ("f1_macro", "accuracy"):
                for agg in noniid["aggregators"]:
                    rs = select(runs, model="grama", aggregator=agg, attack=None, alpha=float(alpha))
                    row.append(mean_std(_vals(rs, key)))
            rows.append(row)
        write_csv(tables / "noniid.csv", header, rows)
        out.append("## 2. Non-IID data (Sec 6.2.2)\n\nGraMa, no attack. Lower alpha means more skewed "
                   "clients; alpha = 100 is close to IID.\n\n" + md_table(header, rows) + "\n")

        fig, ax = plt.subplots(figsize=(4.0, 2.7))
        for agg in noniid["aggregators"]:
            xs, ys, es = [], [], []
            for alpha in noniid["alphas"]:
                v = _vals(select(runs, model="grama", aggregator=agg, attack=None, alpha=float(alpha)), "f1_macro")
                if v:
                    xs.append(alpha)
                    ys.append(np.mean(v))
                    es.append(np.std(v))
            if xs:
                ax.errorbar(xs, ys, yerr=es, color=COLORS[agg], marker=MARKERS[agg], ms=4, lw=1.2,
                            capsize=2, label=f"GraMa + {AGG_LABEL[agg]}")
        ax.set_xscale("log")
        ax.set_xlabel("Dirichlet alpha (log scale; lower = more skewed)")
        ax.set_ylabel("Test macro-F1")
        ax.legend(frameon=False)
        figures.append(("Macro-F1 against data skew", _save(fig, fig_dir, "noniid")))

    # ---------------------------------------------------------------- 3. poisoning
    pois = profile.get("poisoning")
    if pois:
        fractions = [0.0] + [float(f) for f in pois["fractions"]]
        out.append("## 3. Poisoning (Sec 6.2.3)\n\nGraMa, Dirichlet alpha "
                   f"{alpha0}. Columns are the share of compromised clients; 0 is the clean run.\n")
        fig, axes = plt.subplots(1, len(pois["attacks"]), figsize=(3.2 * len(pois["attacks"]), 2.7),
                                 squeeze=False, sharey=True)
        for ai, attack in enumerate(pois["attacks"]):
            for key in ("f1_macro", "detection_rate"):
                header = ["Aggregator"] + [f"{int(round(f * 100))}%" for f in fractions]
                rows = []
                for agg in pois["aggregators"]:
                    row = [AGG_LABEL[agg]]
                    for f in fractions:
                        att = None if f == 0 else attack
                        row.append(mean_std(_vals(select(runs, model="grama", aggregator=agg, alpha=alpha0,
                                                         attack=att, fraction=f), key)))
                    rows.append(row)
                write_csv(tables / f"poisoning_{attack}_{key}.csv", header, rows)
                out.append(f"### {ATTACK_LABEL[attack]}: {METRIC_LABEL[key]}\n\n"
                           + md_table(header, rows) + "\n")
            ax = axes[0][ai]
            for agg in pois["aggregators"]:
                ys = []
                for f in fractions:
                    v = _vals(select(runs, model="grama", aggregator=agg, alpha=alpha0,
                                     attack=None if f == 0 else attack, fraction=f), "f1_macro")
                    ys.append(np.mean(v) if v else np.nan)
                ax.plot([f * 100 for f in fractions], ys, color=COLORS[agg], marker=MARKERS[agg], ms=4,
                        lw=1.2, label=AGG_LABEL[agg])
            ax.set_title(ATTACK_LABEL[attack].split(" (")[0])
            ax.set_xlabel("Compromised clients (%)")
            ax.set_xticks([round(f * 100) for f in fractions])
            if ai == 0:
                ax.set_ylabel("Test macro-F1")
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, frameon=False, loc="upper center", ncol=len(labels),
                   bbox_to_anchor=(0.5, -0.07))
        figures.append(("Macro-F1 under poisoning", _save(fig, fig_dir, "poisoning")))

        # defence quality for the rules that name clients
        detecting = [a for a in pois["aggregators"] if a in ("hdbscan", "krum", "flame")]
        if detecting:
            header = ["Attack", "Aggregator"] + [f"{int(round(f * 100))}% TPR / FPR" for f in fractions[1:]]
            rows = []
            fig, axes = plt.subplots(1, len(pois["attacks"]), figsize=(3.2 * len(pois["attacks"]), 2.7),
                                     squeeze=False, sharey=True)
            for ai, attack in enumerate(pois["attacks"]):
                ax = axes[0][ai]
                for agg in detecting:
                    row = [ATTACK_LABEL[attack].split(" (")[0], AGG_LABEL[agg]]
                    tprs, fprs = [], []
                    for f in fractions[1:]:
                        rs = select(runs, model="grama", aggregator=agg, alpha=alpha0, attack=attack, fraction=f)
                        t = [r["defence"]["tpr"] for r in rs if r["defence"]["tpr"] is not None]
                        p = [r["defence"]["fpr"] for r in rs if r["defence"]["fpr"] is not None]
                        tprs.append(np.mean(t) if t else np.nan)
                        fprs.append(np.mean(p) if p else np.nan)
                        row.append(f"{tprs[-1]:.2f} / {fprs[-1]:.2f}" if t else "–")
                    rows.append(row)
                    xs = [f * 100 for f in fractions[1:]]
                    ax.plot(xs, tprs, color=COLORS[agg], marker=MARKERS[agg], ms=4, lw=1.2,
                            label=f"{AGG_LABEL[agg]} TPR")
                    ax.plot(xs, fprs, color=COLORS[agg], marker=MARKERS[agg], ms=4, lw=1.0, ls="--",
                            mfc="white", label=f"{AGG_LABEL[agg]} FPR")
                ax.set_title(ATTACK_LABEL[attack].split(" (")[0])
                ax.set_xlabel("Compromised clients (%)")
                ax.set_xticks([round(f * 100) for f in fractions[1:]])
                ax.set_xlim(0, max(f * 100 for f in fractions) + 5)
                ax.set_ylim(-0.03, 1.03)
                if ai == 0:
                    ax.set_ylabel("Rate")
            handles, labels = axes[0][0].get_legend_handles_labels()
            fig.legend(handles, labels, frameon=False, loc="upper center", ncol=len(labels),
                       bbox_to_anchor=(0.5, -0.07), fontsize=7)
            figures.append(("How often compromised (TPR) and honest (FPR) updates were rejected",
                            _save(fig, fig_dir, "defence_rates")))
            write_csv(tables / "defence_rates.csv", header, rows)
            out.append("### Rejected updates\n\nTPR: share of compromised clients' updates rejected. "
                       "FPR: share of honest clients' updates rejected. Median, trimmed mean and norm clipping "
                       "reject no client as a whole, so they are not listed.\n\n"
                       + md_table(header, rows) + "\n")

    # ---------------------------------------------------------------- 4. ablation
    abl = profile.get("ablation")
    if abl and ablation_runs:
        agg = abl.get("aggregator", "fedavg")
        full = select(runs, model="grama", aggregator=agg, attack=None, alpha=alpha0)
        full_f1 = np.mean(_vals(full, "f1_macro")) if full else None
        header = ["Variant", "Macro-F1", "Change in macro-F1", "Accuracy", "Detection rate",
                  "False alarm rate", "Params"]
        rows = []
        for variant in [""] + list(abl["variants"]):
            rs = full if not variant else select(ablation_runs, variant=variant)
            if not rs:
                continue
            f1 = _vals(rs, "f1_macro")
            change = f"{np.mean(f1) - full_f1:+.4f}" if variant and full_f1 is not None and f1 else "–"
            rows.append([VARIANT_LABEL.get(variant, variant), mean_std(f1), change,
                         mean_std(_vals(rs, "accuracy")), mean_std(_vals(rs, "detection_rate")),
                         mean_std(_vals(rs, "false_alarm_rate")), f"{rs[0]['params']:,}"])
        write_csv(tables / "ablation.csv", header, rows)
        out.append(f"## 4. Ablation\n\nGraMa + {AGG_LABEL[agg]}, no attack, alpha {alpha0}. "
                   f"Default edges: {profile.get('edge_mode', 'transition')}. Each row changes one thing.\n\n"
                   + md_table(header, rows) + "\n")

    # ---------------------------------------------------------------- 5. efficiency
    if eff:
        header = ["Model", "Params", "Size (KB)", "Upload per client per round (KB)",
                  "CPU latency, 1 thread (ms/sequence)", "GPU latency (ms/sequence)", "Throughput (sequences/s)"]
        rows = []
        for name, e in eff.items():
            tput = e.get("gpu_sequences_per_second") or e.get("cpu_sequences_per_second")
            rows.append([name, f"{e['params']:,}", f"{e['size_kb']:.1f}", f"{e['upload_per_round_kb']:.1f}",
                         f"{e['cpu_1thread_ms_per_sequence']:.2f}",
                         f"{e['gpu_ms_per_sequence']:.2f}" if e.get("gpu_ms_per_sequence") else "–",
                         f"{tput:,.0f}" if tput else "–"])
        write_csv(tables / "efficiency.csv", header, rows)
        frames = next(iter(eff.values()))["sequence_covers_frames"]
        out.append("## 5. Efficiency (Sec 6.1, 8.1)\n\nOne sequence covers "
                   f"{frames} CAN frames. Latency is for one sequence at a time; throughput is for batches "
                   "of 256 on the run's device.\n\n" + md_table(header, rows) + "\n")

    # ---------------------------------------------------------------- figures
    if figures:
        out.append("## Figures\n\nPNG to look at, PDF with the same name for LaTeX.\n")
        for caption, path in figures:
            out.append(f"**{caption}**\n\n![{caption}]({path})\n")

    out.append("## Notes\n")
    if data.get("split_note"):
        out.append(f"- Split: {data['split_note']}.")
    elif data.get("split", "blocks") == "temporal":
        out.append("- Split: the last 20% of every file tests. On CIC-IoV2024 this puts frames in the test set "
                   "that never occur in training (the RPM and SPEED files end on CAN ID 513 with new payloads).")
    else:
        out.append(f"- Split: every fifth block of {data.get('block_rows', 1000)} rows in each file tests, the rest "
                   "trains; windows never cross a block boundary.")
    out.append("- The CNN-BiGRU baseline is our implementation of that model family on the same "
               "sequences, trained with FedAvg; the original adaptive weighting (AWI) is not reproduced.")
    out.append("- The centralised row trains one model on all the training data with the same number "
               "of passes over the data as a federated run. It is a reference, not a federated method.")
    summary = results_dir / "summary.md"
    summary.write_text("\n".join(out) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", help="e.g. results/quick")
    args = parser.parse_args()
    path = make_report(args.results_dir)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
