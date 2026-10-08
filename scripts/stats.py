"""Confidence intervals and paired tests over saved runs (see grama.experiments.stats).

    python scripts/stats.py results/det_road_central --metric final.f1_macro --reference grama_central
    python scripts/stats.py results/full results/new_baselines results/def_ablation \\
        --metric final.f1_macro --reference grama_hdbscan --out results/stats/defence_f1

Methods are named <model>_<aggregator>, with +<variant> for an ablation variant (grama_central+no_temporal).
--out writes <out>.md and <out>.json; without it the table is printed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from grama.experiments.stats import compare, load_records, to_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("results", nargs="+", help="result folders (results/<profile>) or runs.jsonl files")
    parser.add_argument("--metric", nargs="+", default=["final.f1_macro"],
                        help="path into a run record: final.f1_macro, tests.masquerade.f1_macro, defence.tpr, ...")
    parser.add_argument("--reference", required=True, help="method every other method is compared with")
    parser.add_argument("--boot", type=int, default=10000, help="bootstrap resamples")
    parser.add_argument("--out", default=None, help="write <out>.md and <out>.json instead of printing")
    args = parser.parse_args()

    records = load_records(args.results)
    if not records:
        print("No runs found in", ", ".join(args.results))
        return 1
    parts, everything = [], {}
    for metric in args.metric:
        results = compare(records, metric, args.reference, n_boot=args.boot)
        if not results:
            print(f"No condition has the reference {args.reference!r} for {metric}.")
            continue
        parts.append(to_markdown(results, metric))
        everything[metric] = results
    text = "\n\n".join(parts)
    if args.out and everything:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".md").write_text(text + "\n")
        out.with_suffix(".json").write_text(json.dumps(everything, indent=1))
        print(f"Wrote {out.with_suffix('.md')} and {out.with_suffix('.json')}")
    else:
        print(text)
    return 0 if everything else 1


if __name__ == "__main__":
    sys.exit(main())
