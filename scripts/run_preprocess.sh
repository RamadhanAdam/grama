#!/usr/bin/env bash
# Validates raw data is in place, then runs the preprocessing pipeline.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== Checking data/raw/ against config/data.yaml =="
python -m grama.data.download --check

echo "== Preprocessing not yet wired to a CLI entrypoint =="
echo "See src/grama/data/preprocess.py and src/grama/data/graph_builder.py —"
echo "wire these into a script here once the real CIC-IoV2024 column layout is confirmed."
