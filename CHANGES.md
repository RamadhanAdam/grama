# Changes

## October 2026: runs for two papers (the defence and the detector)

Defence paper (`make paper1-background`, about 740 runs, about 45 hours on one A100):
- New aggregation rules: FoolsGold, a simplified DeepSight (without the DDifs measure) and FreqFed.
- The defence can build its latent space with PCA or the raw updates (`latent_method`), and named variants
  (`hdbscan_pca`, `hdbscan_raw`, `hdbscan_no_rescale`, `hdbscan_no_normalize`, `hdbscan_no_standardize`,
  `hdbscan_last_layer`, `hdbscan_eps1/4/8`, `hdbscan_mcs2/5`) change one setting each, for the ablation and
  the settings grid.
- Attack `alie_noisy`: the colluders add their own noise to the shared ALIE vector, so they no longer send
  identical updates.
- Profiles `new_baselines`, `def_ablation`, `alie_duplicates`, `cic_adaptive_new`, `cic_seeds`, `def_grid`,
  `clients40`, `road_new_baselines`, `cantt1_new_baselines`. A poisoning section may give `seeds_by_fraction`
  (more seeds in the 30% and 40% cells).

Detector paper (`make paper2-background`, about 220 runs, about 27 hours on one A100):
- Baselines `gcn_ids` (graph convolution on the last window), `gcn_gru` (the same with a GRU over the windows)
  and `transformer_ids` (frames of a window, then the windows of a sequence), and the ablation variant `one_head`.
- Profiles `det_road_central` (ten seeds), `det_road_ablation`, `det_road_fedavg`, `det_cantt1`-`det_cantt4`,
  `det_cic`.

Both:
- `scripts/stats.py`: mean with a 95% bootstrap interval, the difference to a reference method with a paired
  bootstrap interval, Wilcoxon and paired t-test, Holm correction (`make stats-paper1`, `make stats-paper2`).
- `scripts/run_queue.sh`: runs profiles in order, writes `results/queue_NAME.status`, goes on after a failure,
  resumes where it stopped. `make queue-status` shows the last lines.
- The runner keeps one copy of each data view on the GPU for all models that read it; the report names, colours
  and detection tables cover the new rules.

## October 2026: adaptive attack and more seeds

- Adaptive attack (`adaptive`): the attackers train like targeted flipping, then all send
  mean(honest) + gamma * (mean(attackers) - mean(honest)), with gamma the largest scale the
  aggregation rule still accepts. They find it by bisection on an exact copy of the rule (same
  settings and random state), so this is the strongest attacker the code simulates. Rules that
  reject no client get the maximum (`adaptive_max_scale`, 10). The scale sent each round is saved
  in the run's history, and the report has a table of it.
- Profiles `cic_adaptive` and `cantt1_adaptive` (20% and 40%, FedAvg, norm clipping, FLAME,
  HDBSCAN, two seeds). `reuse_runs_from` copies their clean reference runs from `full` and `cantt1`.
- `road` and `cantt1` main comparison: five seeds instead of three.
- `make extra-background` runs all of it.

## October 2026: two more datasets

- Readers for ROAD and can-train-and-test, taking the files straight from the zips. ROAD frames are
  labelled from the injection intervals, IDs and payloads in its metadata; the four accelerator
  captures have none and are left out.
- Each dataset keeps its own split (ROAD by recording, can-train-and-test by its folders). Extra
  test sets (ROAD masquerades; unknown car, unknown attacks) are scored in every run and reported in
  an "Other test sets" table, with the share of frames whose CAN ID training never saw.
- Profiles `road` and `cantt1`-`cantt4`; `make road`, `make cantt`, `make others-background`;
  `make check-data SOURCE=...`.
- CAN IDs seen fewer than `min_id_count` times in training go to the "other" node (default 1, so
  CIC-IoV2024 builds are unchanged; 20 for the new datasets, where fuzzing sends hundreds of IDs once).
- The CIC reader no longer looks inside the other datasets' folders.

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
