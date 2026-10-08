"""Confidence intervals and paired tests over the saved runs.

Each run is one seed. For every condition (dataset, attack, share of compromised clients, Dirichlet alpha)
the methods are compared with a reference method, paired on the seed:

  mean and a 95% percentile bootstrap interval of each method's metric,
  the mean difference to the reference with a 95% paired bootstrap interval,
  a two-sided Wilcoxon signed-rank test and a paired t-test on the differences,
  Holm's correction of the Wilcoxon p-values across the methods of one condition.

With n paired seeds the smallest two-sided Wilcoxon p-value is 2 / 2^n (0.0625 at n = 5, 0.002 at n = 10), so five
seeds can never reach p < 0.05 with that test; the tables print the floor. The paired bootstrap interval is the
more useful number at small n.

    python scripts/stats.py results/det_road_central --metric final.f1_macro --reference grama_central
    python scripts/stats.py results/full results/new_baselines --metric final.f1_macro --reference grama_hdbscan
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

CONDITION_KEYS = ("data_source", "attack", "fraction", "alpha")


def load_records(dirs) -> list[dict]:
    """All runs of the given result folders, one record per (data file, run id)."""
    seen, out = set(), []
    for d in dirs:
        path = Path(d) / "runs.jsonl" if Path(d).is_dir() else Path(d)
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            key = (rec.get("data_file"), rec["run_id"])
            if key not in seen:
                seen.add(key)
                out.append(rec)
    return out


def method_name(rec: dict) -> str:
    base = f"{rec['model']}_{rec['aggregator']}"
    return f"{base}+{rec['variant']}" if rec.get("variant") else base


def metric_value(rec: dict, path: str):
    """'final.f1_macro', 'tests.masquerade.f1_macro', 'defence.tpr', ... -> float or None."""
    cur = rec
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return float(cur) if isinstance(cur, (int, float)) else None


def bootstrap_ci(values, n_boot: int = 10000, level: float = 0.95, seed: int = 0) -> tuple[float, float, float]:
    """Mean and percentile bootstrap interval of the mean."""
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return math.nan, math.nan, math.nan
    if len(v) == 1:
        return float(v[0]), math.nan, math.nan
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n_boot, len(v)))].mean(axis=1)
    lo, hi = np.percentile(means, [50 * (1 - level), 100 - 50 * (1 - level)])
    return float(v.mean()), float(lo), float(hi)


def paired_tests(a, b, n_boot: int = 10000, seed: int = 0) -> dict:
    """a - b over paired seeds: mean difference, its bootstrap interval, Wilcoxon and paired t p-values."""
    from scipy import stats

    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n = len(d)
    mean, lo, hi = bootstrap_ci(d, n_boot=n_boot, seed=seed)
    wilcoxon_p = ttest_p = math.nan
    if n >= 2:
        if np.allclose(d, 0.0):
            wilcoxon_p = ttest_p = 1.0
        else:
            wilcoxon_p = float(stats.wilcoxon(d).pvalue)
            ttest_p = float(stats.ttest_rel(a, b).pvalue)
    return {"n": n, "mean_diff": mean, "ci_lo": lo, "ci_hi": hi, "wilcoxon_p": wilcoxon_p, "ttest_p": ttest_p,
            "min_wilcoxon_p": 2.0 / 2 ** n if n else math.nan}


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (NaN stays NaN)."""
    idx = [i for i, p in enumerate(pvalues) if not math.isnan(p)]
    order = sorted(idx, key=lambda i: pvalues[i])
    adjusted = [math.nan] * len(pvalues)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(order) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def compare(records: list[dict], metric: str, reference: str, n_boot: int = 10000) -> list[dict]:
    """One entry per condition: the reference and every other method, paired on the seed."""
    groups: dict[tuple, dict[str, dict[int, float]]] = {}
    for rec in records:
        value = metric_value(rec, metric)
        if value is None:
            continue
        cond = tuple(rec.get(k) for k in CONDITION_KEYS)
        groups.setdefault(cond, {}).setdefault(method_name(rec), {})[rec["seed"]] = value
    out = []
    for cond, methods in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        if reference not in methods:
            continue
        ref = methods[reference]
        rows = []
        for name, by_seed in sorted(methods.items()):
            mean, lo, hi = bootstrap_ci(list(by_seed.values()), n_boot=n_boot)
            row = {"method": name, "n": len(by_seed), "mean": mean, "ci_lo": lo, "ci_hi": hi}
            if name != reference:
                seeds = sorted(set(by_seed) & set(ref))
                if len(seeds) >= 2:
                    row["vs_reference"] = paired_tests([by_seed[s] for s in seeds], [ref[s] for s in seeds],
                                                       n_boot=n_boot)
            rows.append(row)
        adjusted = holm([r["vs_reference"]["wilcoxon_p"] if "vs_reference" in r else math.nan for r in rows])
        for r, p in zip(rows, adjusted):
            if "vs_reference" in r:
                r["vs_reference"]["wilcoxon_p_holm"] = p
        out.append({"condition": dict(zip(CONDITION_KEYS, cond)), "reference": reference, "rows": rows})
    return out


def _fmt(x, digits=3):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def _p(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return "<0.001" if x < 0.001 else f"{x:.3f}"


def to_markdown(results: list[dict], metric: str) -> str:
    lines = [f"# {metric}: mean with 95% bootstrap interval, difference to the reference, paired tests\n",
             "Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon "
             "p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the "
             "interval of the difference.\n"]
    for res in results:
        c = res["condition"]
        label = ", ".join(f"{k} {v}" for k, v in c.items() if v not in (None, 0.0) or k == "data_source")
        lines += [f"## {label}  (reference: {res['reference']})\n",
                  "| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |",
                  "|---|---|---|---|---|---|---|"]
        for r in res["rows"]:
            mean = f"{_fmt(r['mean'])} [{_fmt(r['ci_lo'])}, {_fmt(r['ci_hi'])}]" if not math.isnan(r["ci_lo"]) \
                else _fmt(r["mean"])
            v = r.get("vs_reference")
            if v:
                holm_p = v["wilcoxon_p_holm"]
                star = "*" if not math.isnan(holm_p) and holm_p < 0.05 else ""
                lines.append(f"| {r['method']} | {r['n']} | {mean} | {_fmt(v['mean_diff'])} "
                             f"[{_fmt(v['ci_lo'])}, {_fmt(v['ci_hi'])}] | {_p(v['wilcoxon_p'])} | "
                             f"{_p(holm_p)}{star} | {_p(v['ttest_p'])} |")
            else:
                lines.append(f"| {r['method']} (reference) | {r['n']} | {mean} | | | | |")
        lines.append("")
    return "\n".join(lines)
