"""Run a profile end to end: build data, train every run, benchmark, write the report.

    python scripts/run_experiments.py --profile smoke
    python scripts/run_experiments.py --profile quick
    python scripts/run_experiments.py --profile full --only main noniid

Finished runs are kept in results/<profile>/runs.jsonl and skipped next
time, so after a crash or a closed laptop just run the same command again.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from grama.experiments.report import make_report  # noqa: E402
from grama.experiments.runner import Experiment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default="quick", help="smoke | quick | full (config/experiments.yaml)")
    parser.add_argument("--only", nargs="*", choices=["main", "noniid", "poisoning", "ablation"],
                        help="run only these experiment groups")
    parser.add_argument("--device", default=None, help="cuda | cpu (default: cuda if available)")
    parser.add_argument("--rebuild-data", action="store_true", help="rebuild the processed dataset")
    parser.add_argument("--no-progress", action="store_true", help="no progress bar (for log files)")
    args = parser.parse_args()

    start = time.time()
    exp = Experiment(args.profile, root=ROOT, device=args.device)
    exp.prepare_data(force=args.rebuild_data)
    exp.run_all(only=args.only, progress=not args.no_progress)
    exp.efficiency()
    summary = make_report(exp.out_dir)
    print(f"\nDone in {(time.time() - start) / 60:.1f} min. Results: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
