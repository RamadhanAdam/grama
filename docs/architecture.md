# Architecture reference

Which file implements which part of the concept note, for checking the code against the paper.

| Concept note | Equations | Code |
|---|---|---|
| Sec 3.2: preprocessing, min-max scaling, sliding windows | eq. 3 | `src/grama/data/build.py` (`window_stream`, `build_from_streams`) |
| Sec 4.1 Phase 1: traffic as a graph of CAN IDs | | `src/grama/data/build.py` (node features), `src/grama/data/dataset.py` (edges) |
| Sec 4.1 Phase 2 / Sec 5.1: GAT spatial encoder | eq. 4-6 | `src/grama/models/gat_encoder.py` |
| Sec 4.1 Phase 3 / Sec 5.2: Mamba temporal encoder | eq. 7-10 | `src/grama/models/mamba_block.py` |
| Full local model | | `src/grama/models/classifier_head.py` (`GraMaLocalModel`) |
| Sec 4.1 Phase 4: local training, Δw sent to the server | | `src/grama/federated/client.py` |
| Sec 4.1 Phase 5 / Sec 5.3: latent density defence and aggregation | eq. 11-15 | `src/grama/federated/aggregator.py` |
| Round loop | | `src/grama/federated/server.py` |
| Sec 6.1: metrics | | `src/grama/eval/metrics.py` |
| Sec 6.1 / 8.1: latency, size, communication | | `src/grama/eval/latency_bench.py` |
| Sec 6.2.1: baseline comparison (Mnkash et al.) | eq. 1-2 | `src/grama/models/baseline.py`, `src/grama/federated/robust.py` |
| Sec 6.2.2: non-IID heterogeneity | | `src/grama/data/federated_split.py` |
| Sec 6.2.3: poisoning | | `src/grama/federated/client.py` (attacks), `src/grama/attacks/poisoning.py` |
| All experiments | | `src/grama/experiments/runner.py`, `report.py`, `config/experiments.yaml` |

## Data flow

```
CIC-IoV2024 CSVs (data/raw/)
  -> build.py: one stream per file -> cap -> time split -> vocabulary + scaling (train only)
               -> windows of W frames -> node features (N x 10) -> sequences of L windows
  -> data/processed/cic_iov2024_<hash>.pt
  -> dataset.py: batches of (node features, adjacency, label); edges built on the fly
  -> per round, per sampled client (client.py): local training of GraMaLocalModel
       node features + CAN-ID embedding
       -> GAT (2 layers, residual)              eq. 4-6
       -> attention pooling -> one token per window
       -> Mamba over the L tokens               eq. 7-10
       -> classifier head on the last state
     -> Δw_k (scaled up if the client does magnitude poisoning)
  -> aggregator.py: centre and scale Δw -> phi -> latent -> HDBSCAN -> trust weights -> sum  eq. 11-15
  -> server.py: w_global += aggregated Δw; test metrics every few rounds
```

## Where the code goes beyond the note

See "Choices that differ from the concept note" in the README: transition edges, GAT
residuals, CAN-ID embeddings and attention pooling; `allow_single_cluster`, input scaling for
phi and a scaled latent for HDBSCAN. Each can be switched back in the configs, and the
ablation profile group measures the model-side ones.
