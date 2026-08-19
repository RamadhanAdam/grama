# Architecture Reference

Maps concept-note sections/equations to their code implementation, for
cross-checking correctness during review.

| Concept note | Equation(s) | Implementation |
|---|---|---|
| Sec 3.2: preprocessing, sliding windows | eq. 3 | `src/grama/data/preprocess.py` |
| Sec 4.1 Phase 1: graph modeling | — | `src/grama/data/graph_builder.py` |
| Sec 4.1 Phase 2 / Sec 5.1: GAT spatial encoder | eq. 4–6 | `src/grama/models/gat_encoder.py` |
| Sec 4.1 Phase 3 / Sec 5.2: Mamba temporal encoder | eq. 7–10 | `src/grama/models/mamba_block.py` |
| Sec 4.1 Phase 4: local optimization, Δw dispatch | — | `src/grama/federated/client.py` |
| Sec 4.1 Phase 5 / Sec 5.3: latent density defense & aggregation | eq. 11–15 | `src/grama/federated/aggregator.py` |
| Sec 6.2.2: Non-IID heterogeneity testing | — | `src/grama/data/federated_split.py` |
| Sec 6.2.3: adversarial poisoning simulations | — | `src/grama/attacks/poisoning.py` |
| Sec 6.1: evaluation metrics | — | `src/grama/eval/metrics.py` |
| Sec 6.1 / Sec 8.1: edge latency & memory | — | `src/grama/eval/latency_bench.py` |
| Sec 2 / Table 1: baseline comparison (Mnkash et al.) | eq. 1–2 | not yet implemented — `scripts/run_baseline_cnn_bigru.py` |

## Data flow (matches Fig. 1)

```
CAN frames (data/raw/)
  -> preprocess.py: min-max scale, sliding windows
  -> graph_builder.py: window -> ECU graph (node_features, adjacency)
  -> [per client, per round] client.py: local GraMaLocalModel training
       classifier_head.GraMaLocalModel:
         gat_encoder.SpatialTopologicalGAT   (per-window graph -> pooled token)
         mamba_block.MambaBlock               (token sequence -> h_W)
         classifier_head.ClassifierHead        (h_W -> class logits)
  -> Δw_k dispatched to server
  -> aggregator.py: phi(Δw_k) -> HDBSCAN -> trust weights -> weighted sum
  -> server.py: w_global updated, next round
```

## Known simplifications vs. the concept note

- The GAT uses dense adjacency + masked attention rather than a sparse
  graph library (`torch_geometric`/`dgl`), since ECU graphs here are small
  (single/low-double-digit node counts). Revisit if node counts grow.
- The autoencoder `phi` (eq. 11) is retrained fresh each aggregation round
  rather than warm-started — simple and correct, but means early-round
  latent embeddings are less stable. A warm-start option is a reasonable
  follow-up once round counts get large.
- `graph_builder.py`'s CAN-ID→ECU mapping is illustrative and must be
  replaced with the real dataset's arbitration ID space before training on
  real data.
