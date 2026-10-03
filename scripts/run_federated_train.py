"""Train one federated run and print its test metrics.

    python scripts/run_federated_train.py --profile smoke
    python scripts/run_federated_train.py --profile quick --aggregator krum --attack label_flip --fraction 0.2

Uses the data and federated settings of the chosen profile. For the paper
results use scripts/run_experiments.py, which runs and saves every setting.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from grama.experiments.runner import Experiment, RunSpec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default="smoke")
    parser.add_argument("--model", default="grama", choices=["grama", "cnn_bigru"])
    parser.add_argument("--aggregator", default="hdbscan",
                        choices=["hdbscan", "fedavg", "median", "trimmed_mean", "krum", "central"])
    parser.add_argument("--alpha", type=float, default=None, help="Dirichlet alpha (default: config)")
    parser.add_argument("--attack", default=None, choices=["label_flip", "targeted_flip", "magnitude_poison"])
    parser.add_argument("--fraction", type=float, default=0.2, help="share of compromised clients")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    exp = Experiment(args.profile, root=ROOT, device=args.device,
                     results_dir=ROOT / "results" / f"{args.profile}_single")
    exp.prepare_data()
    alpha = args.alpha if args.alpha is not None else float(exp.sim["non_iid_alpha"])
    spec = RunSpec(args.model, args.aggregator, alpha, args.attack,
                   args.fraction if args.attack else 0.0, args.seed)
    record = exp.run_one(spec)
    for h in record["history"]:
        f1 = h.get("f1_macro")
        print(f"round {h['round']:3d}  loss {h['loss']:.4f}  rejected {h['num_rejected']}/{h['num_malicious']} malicious"
              + (f"  test macro-F1 {f1:.4f}" if f1 is not None else ""))
    final = {k: v for k, v in record["final"].items() if not isinstance(v, list)}
    print(json.dumps({"run": spec.run_id, "final": final, "defence": record["defence"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
