"""CIC-IoV2024 acquisition helper.

CIC-IoV2024 is NOT available via a direct, scriptable download — the Canadian
Institute for Cybersecurity (UNB) gates access behind a request form
(name, affiliation, and intended research use). There is no public API or
stable bulk-download URL to automate here without violating their access
terms.

Workflow:
  1. Request access: https://www.unb.ca/cic/datasets/iov-dataset-2024.html
  2. Once approved, download the released CSV(s) and place them under
     `data/raw/` (see config/data.yaml: dataset.raw_dir).
  3. Run this script to validate the files actually match what the rest of
     the pipeline expects (expected columns, non-empty, label values present)
     before wasting time debugging preprocessing on malformed input.

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

REQUEST_FORM_URL = "https://www.unb.ca/cic/datasets/iov-dataset-2024.html"


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
        logger.info("CIC-IoV2024 requires manual request + download. See:")
        logger.info("  %s", REQUEST_FORM_URL)
        logger.info("Place the downloaded CSV(s) in: %s", raw_dir.resolve())
        logger.info("Then re-run: python -m grama.data.download --check")
        return 0

    files = find_raw_files(raw_dir)
    if not files:
        logger.error("No CSV files found in %s.", raw_dir.resolve())
        logger.error("Request the dataset first: %s", REQUEST_FORM_URL)
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
