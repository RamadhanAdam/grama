"""Checks that a dataset is in data/raw and says what to do if it isn't.

The dataset (Neto et al., Internet of Things, 2024) is on the CIC site:
  https://www.unb.ca/cic/datasets/iov-dataset-2024.html
The download page asks for a name and email, then links the files. Put
CICIoV2024.tar.xz, or just the CSVs from its decimal/ folder, in data/raw/.
Any folder depth works, and archives are unpacked automatically. Only the
decimal CSVs are used.

    python -m grama.data.download                         # CIC-IoV2024
    python -m grama.data.download --source road           # ROAD
    python -m grama.data.download --source can_train_test # can-train-and-test

ROAD and can-train-and-test are plain downloads (no form). Put the zip in
its folder (data/raw/road, data/raw/can-train-and-test) and leave it zipped:
the readers take the files straight from it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from grama.data.build import class_index, find_csv_files, other_dataset_dirs, unpack_archives
from grama.utils.config import Config

DOWNLOAD_URL = "https://www.unb.ca/cic/datasets/iov-dataset-2024.html"
OTHER_URLS = {
    "road": "https://zenodo.org/records/10462796/files/road.zip?download=1",
    "can_train_test": "https://ndownloader.figshare.com/files/43632393",
}
REQUIRED = ["ID"] + [f"DATA_{i}" for i in range(8)]


def check(raw_dir: Path, class_names: list[str], verbose: bool = True, exclude=None) -> bool:
    """True when every class has a readable CSV under raw_dir (outside the folders in exclude)."""
    say = print if verbose else (lambda *a, **k: None)
    raw_dir.mkdir(parents=True, exist_ok=True)
    unpack_archives(raw_dir, exclude=exclude)
    files = find_csv_files(raw_dir, exclude=exclude)
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


def check_other(source: str, section: dict, verbose: bool = True) -> bool:
    """ROAD or can-train-and-test: are the files there (zipped or not), and what do they hold?"""
    from grama.data.can_train_test import FOLDERS, cantt_files
    from grama.data.road import road_files

    say = print if verbose else (lambda *a, **k: None)
    raw_dir = Path(section["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    files = road_files(raw_dir) if source == "road" else cantt_files(raw_dir)
    names = files.names()
    if not names:
        say(f"No {section.get('name', source)} files in {raw_dir.resolve()}.\n")
        say("Download the zip into that folder and leave it zipped, for example:")
        say(f"  curl -L -o {raw_dir}/{'road.zip' if source == 'road' else 'can-train-and-test.zip'} "
            f"'{OTHER_URLS[source]}'")
        return False
    say(f"Reading from {files.where}")
    if source == "road":
        logs = [n for n in names if n.endswith(".log")]
        has_meta = any(n.endswith("attacks/capture_metadata.json") for n in names)
        say(f"  {sum('/ambient/' in f'/{n}' for n in logs)} ambient captures, "
            f"{sum('/attacks/' in f'/{n}' for n in logs)} attack captures, "
            f"attack metadata {'found' if has_meta else 'MISSING'}")
        return has_meta and len(logs) > 0
    ok = True
    for s in sorted({n.split("/")[-3] for n in names if n.split("/")[-3].startswith("set_")}):
        counts = [sum(f"/{s}/{folder}/" in f"/{n}" for n in names) for folder in FOLDERS.values()]
        say(f"  {s}: " + ", ".join(f"{k} {c} files" for k, c in zip(FOLDERS, counts)))
        ok &= all(counts)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config/data.yaml")
    parser.add_argument("--source", default="cic", choices=["cic", "road", "can_train_test"])
    parser.add_argument("--check", action="store_true", help="kept for old commands; checking is the default")
    args = parser.parse_args()
    cfg = Config.from_yaml(args.config)
    if args.source != "cic":
        ok = check_other(args.source, cfg[args.source])
        print("\nData looks complete." if ok else "\nData not ready yet (see above).")
        return 0 if ok else 1
    ok = check(Path(cfg.dataset["raw_dir"]), cfg["classes"], exclude=other_dataset_dirs(cfg))
    print("\nData looks complete." if ok else "\nData not ready yet (see above).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
