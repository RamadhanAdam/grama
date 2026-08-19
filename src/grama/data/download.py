"""CIC-IoV2024 acquisition helper.

CIC-IoV2024 is publicly downloadable from:
  https://www.unb.ca/cic/datasets/iov-dataset-2024.html

The dataset is directly accessible as CSV files (no request form required, contrary
to earlier assumptions). Column schema:
  ID, DATA_0, DATA_1, ..., DATA_7, label, category, specific_class

This script validates that downloaded CSVs match the expected schema before
preprocessing, catching malformed input early.

Workflow:
  1. Download CSVs from https://www.unb.ca/cic/datasets/iov-dataset-2024.html
  2. Place them in `data/raw/` (see config/data.yaml: dataset.raw_dir)
  3. Run: python -m grama.data.download --check

Usage:
    python -m grama.data.download --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from grama.utils.config import Config
from grama.utils.logging import get_logger

logger = get_logger(__name__)

DOWNLOAD_URL = "https://www.unb.ca/cic/datasets/iov-dataset-2024.html"


def find_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(raw_dir.glob("*.csv"))


def validate_file(path: Path, expected_columns: list[str]) -> tuple[bool, str]:
    try:
        df = pd.read_csv(path, nrows=5)
    except Exception as e:  # noqa: BLE001 - surface any parse error to the user
        return False, f"could not parse as CSV: {e}"

    cols_lower = {c.strip().lower() for c in df.columns}
    expected_lower = {c.lower() for c in expected_columns}
    missing = expected_lower - cols_lower
    if missing:
        return False, f"missing expected columns: {sorted(missing)} (found: {sorted(cols_lower)})"

    if df.empty:
        return False, "file parsed but contains no rows"

    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate files already placed in data/raw/")
    parser.add_argument("--config", default="config/data.yaml")
    args = parser.parse_args()

    cfg = Config.from_yaml(args.config)
    raw_dir = Path(cfg.dataset["raw_dir"])
    expected_columns = cfg.dataset["expected_columns"]

    if not args.check:
        logger.info("CIC-IoV2024 is publicly downloadable:")
        logger.info("  %s", DOWNLOAD_URL)
        logger.info("Place the downloaded CSV(s) in: %s", raw_dir.resolve())
        logger.info("Then re-run: python -m grama.data.download --check")
        return 0

    files = find_raw_files(raw_dir)
    if not files:
        logger.error("No CSV files found in %s.", raw_dir.resolve())
        logger.error("Download the dataset from: %s", DOWNLOAD_URL)
        return 1

    all_ok = True
    for f in files:
        ok, msg = validate_file(f, expected_columns)
        level = logger.info if ok else logger.error
        level("%s: %s", f.name, msg)
        all_ok &= ok

    if all_ok:
        logger.info("All %d file(s) look valid. Ready for preprocessing.", len(files))
        return 0
    logger.error("One or more files failed validation. Check column names against config/data.yaml.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
