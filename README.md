# GraMa: Graph-Mamba Federated IDS for IoV

Implementation scaffold for the architecture described in
`Redesigning Federated Intrusion Detection for IoV: The GraMa (Graph-Mamba)
Architecture`. Replaces the 1D-CNN + BiGRU baseline (Mnkash et al., 2026)
with a Graph Attention Network (spatial, per-ECU topology) + Mamba Selective
State Space Model (temporal), and replaces heuristic AWI aggregation with
HDBSCAN latent-density clustering as an adversarial poisoning defense.

## Status

This is a working pipeline scaffold, validated end-to-end on synthetic data
(`make train-synthetic`). It is **not yet trained on real data** — CIC-IoV2024
requires manual request/download (see below) before real training can run.

| Component | Status |
|---|---|
| GAT spatial encoder (eq. 4-6) | Implemented, unit-tested |
| Mamba SSM block, CUDA + torch-fallback (eq. 7-10) | Implemented, unit-tested |
| HDBSCAN latent-density aggregator (eq. 11-15) | Implemented, unit-tested |
| Dirichlet Non-IID federated split | Implemented, unit-tested |
| Custom federated round loop | Implemented |
| Adversarial poisoning simulation (label-flip, magnitude) | Implemented |
| Real CIC-IoV2024 preprocessing | **Blocked on dataset access** — see below |
| CNN-BiGRU + AWI baseline (Mnkash et al.) | Not yet implemented — see `scripts/run_baseline_cnn_bigru.py` |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
make install          # CPU/dev install, pure-PyTorch Mamba fallback
# or, on a CUDA node (e.g. Kinesis Network A100):
make install-cuda
```

## Dataset: CIC-IoV2024

Publicly downloadable (no request form required):

1. Download: https://www.unb.ca/cic/datasets/iov-dataset-2024.html
2. Place the downloaded CSV(s) in `data/raw/`
3. Validate: `make data-check`

**Dataset notes:**
- Schema: `ID, DATA_0..DATA_7, label, category, specific_class` (no timestamp or DLC)
- Classes: benign, DoS, spoofing-GAS, spoofing-RPM, spoofing-SPEED, spoofing-STEERING_WHEEL (6 total)
- **Critical:** ~99.7% of 1.4M rows are exact duplicates (Stiawan et al., IJAIT 2024)
  - Deduplication is automatically applied during preprocessing
  - This prevents severe train/test data leakage
- **No ECU labels:** The dataset does not publish CAN ID → ECU mappings
  - Graph nodes are learned dynamically from data (see `src/grama/data/graph_builder.py`)

To validate the pipeline without waiting for dataset download, use synthetic data:

```bash
make train-synthetic
```

This runs end-to-end — client sampling, local GAT+Mamba training, HDBSCAN aggregation,
round history — on random tensors with correct shapes, so architecture bugs surface early.

## Repo layout

```
config/          data / model / federated hyperparameters (YAML)
src/grama/
  data/           preprocessing, ECU graph construction, dataset download/validation, Non-IID split
  models/         GAT encoder, Mamba block (CUDA + torch fallback), classifier head
  federated/      local client, HDBSCAN aggregator, round orchestration
  attacks/        label-flip / magnitude poisoning for adversarial eval
  eval/           accuracy/precision/recall/F1/ROC-AUC, latency+memory benchmarking
scripts/         CLI entrypoints
tests/           pytest unit tests (all run on CPU, no dataset required)
```

## Running tests

```bash
make test
```

All tests run on CPU with synthetic tensors — no dataset or GPU required.

## Key implementation notes / open TODOs

- **Graph node vocabulary** (`src/grama/data/graph_builder.py`) is now **data-driven**.
  CAN IDs are discovered dynamically from the dataset (no hardcoded ECU name vocabulary).
  This works around the fact that CICIoV2024 does not publish ECU-to-CAN-ID mappings.

- **Deduplication** is applied automatically in `src/grama/data/preprocess.py`
  before windowing. This is critical: without it, train/test sets will leak
  duplicated frames, inflating accuracy artificially.

- **Feature schema** (8 DATA bytes + frame_count + burst_flag = 10 features total)
  matches the real CICIoV2024 release (see `config/data.yaml`).

- **Mamba backend** auto-selects CUDA (`mamba-ssm`) when available, else
  falls back to a pure-PyTorch selective-scan implementation. Force one or
  the other via `config/model.yaml: mamba_block.backend`.

- **Baseline comparison** (Mnkash et al. CNN-BiGRU+AWI) is scaffolded but
  not implemented — needed for the Table 1 / Sec 6.2.1 comparison.
