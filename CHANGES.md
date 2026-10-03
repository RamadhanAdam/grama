# Changes

## October 2026: runnable experiments

- One notebook (`GraMa.ipynb`) and `make` targets run everything: data check, dataset build,
  all experiments, tables and figures. Three profiles: smoke, quick, full.
- Dataset builder rewritten with numpy (bincount/cumsum instead of a per-row loop). Finds the CSVs
  at any depth, unpacks zips, stores windows once and builds sequences on the fly.
- Edges can be transitions (default) or co-occurrence, chosen per run without rebuilding.
- GAT: attention scores computed without the (B, H, N, N, 2F) pairwise tensor (same values);
  residual connections, CAN-ID embeddings and attention pooling added. All windows of a
  sequence go through the GAT in one batch.
- Mamba fallback: depthwise conv written as shifted multiply-adds (same output, much faster
  backward on CPU).
- Attacks wired into training: label flipping, targeted flipping, magnitude poisoning.
- Baseline aggregation rules added: FedAvg, median, trimmed mean, Multi-Krum.
- HDBSCAN defence fixed: `allow_single_cluster` (it used to reject every update when there were
  no attackers), phi now trains on centred, scaled updates, latent scaled before clustering.
- CNN-BiGRU baseline implemented.
- Metrics: detection rate and false alarm rate, per-class F1, confusion matrix, per-round curves,
  rejection rates of the defence; latency, size and throughput.
- Everything runs on the GPU when there is one, including the dataset.

## August 2026: schema corrections

Config and preprocessing matched to the released CIC-IoV2024 schema: columns `ID, DATA_0..7`,
six classes, no timestamp or DLC, CAN IDs learned from the data instead of a fixed ECU list.
