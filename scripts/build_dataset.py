"""Build the processed dataset on its own (the experiment runner also does this).

    python scripts/build_dataset.py --profile quick
    python scripts/build_dataset.py --profile full --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from grama.experiments.runner import Experiment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default="quick", help="whose data settings to use")
    parser.add_argument("--force", action="store_true", help="rebuild even if the file exists")
    args = parser.parse_args()
    exp = Experiment(args.profile, root=ROOT, device="cpu")
    path = exp.prepare_data(force=args.force)
    print(f"Dataset: {path}")
    print(f"Sequences per class, train: {exp.meta['class_counts']['train']}")
    print(f"Sequences per class, test:  {exp.meta['class_counts']['test']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
