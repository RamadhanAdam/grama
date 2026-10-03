"""Checks that CIC-IoV2024 is in data/raw and says what to do if it isn't.

The dataset (Neto et al., Internet of Things, 2024) is on the CIC site:
  https://www.unb.ca/cic/datasets/iov-dataset-2024.html
The download page asks for a name and email, then links the files. Put
CICIoV2024.tar.xz, or just the CSVs from its decimal/ folder, in data/raw/.
Any folder depth works, and archives are unpacked automatically. Only the
decimal CSVs are used.

    python -m grama.data.download          # check, print what's there
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from grama.data.build import class_index, find_csv_files, unpack_archives
from grama.utils.config import Config

DOWNLOAD_URL = "https://www.unb.ca/cic/datasets/iov-dataset-2024.html"
REQUIRED = ["ID"] + [f"DATA_{i}" for i in range(8)]


def check(raw_dir: Path, class_names: list[str], verbose: bool = True) -> bool:
    """True when every class has a readable CSV under raw_dir."""
    say = print if verbose else (lambda *a, **k: None)
    raw_dir.mkdir(parents=True, exist_ok=True)
    unpack_archives(raw_dir)
    files = find_csv_files(raw_dir)
    if not files:
        say(f"No CSV files in {raw_dir.resolve()}.\n")
        say("To get CIC-IoV2024:")
        say(f"  1. Open {DOWNLOAD_URL} and fill in the short form at the bottom.")
        say("  2. Download the six CSVs in its 'decimal' folder (or CICIoV2024.tar.xz,")
        say("     which also holds binary and hex versions and is much bigger).")
        say(f"  3. Put them in {raw_dir.resolve()} (any folder layout).")
        say("     The links only work in the browser you registered in, so download there,")
        say("     then drag the files into that folder in the JupyterHub file browser.")
        return False

    found: dict[int, Path] = {}
    ok = True
    for f in files:
        try:
            head = pd.read_csv(f, nrows=5)
        except Exception as e:  # noqa: BLE001 - report any parse error
            say(f"  {f.name}: can't read it ({e})")
            ok = False
            continue
        cols = {c.strip() for c in head.columns}
        missing = [c for c in REQUIRED if c not in cols]
        cls = class_index(f.stem, class_names)
        size = f.stat().st_size / 2**20
        if missing:
            say(f"  {f.name}: missing columns {missing}")
            ok = False
        elif cls is None:
            say(f"  {f.name} ({size:.0f} MB): class not in the name, rows will be labelled from their label columns")
        else:
            found[cls] = f
            say(f"  {f.name} ({size:.0f} MB) -> {class_names[cls]}")
    missing_classes = [c for i, c in enumerate(class_names) if i not in found]
    if missing_classes:
        say(f"\nNo file found for: {missing_classes}")
    return ok and not missing_classes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config/data.yaml")
    parser.add_argument("--check", action="store_true", help="kept for old commands; checking is the default")
    args = parser.parse_args()
    cfg = Config.from_yaml(args.config)
    ok = check(Path(cfg.dataset["raw_dir"]), cfg["classes"])
    print("\nData looks complete." if ok else "\nData not ready yet (see above).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
