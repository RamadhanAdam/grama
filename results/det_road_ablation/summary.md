# GraMa results: `det_road_ablation` profile

Generated 2026-10-09 00:04 from 40 runs.

- Data: ROAD (`road_0bc0ca64.pt`), 107 CAN-ID nodes, windows of 64 frames (stride 32), sequences of 8 windows, edges: transition.
- Federated setting: 20 clients, 10 per round, 30 rounds, 2 local epoch(s), batch 64, lr 0.001, Dirichlet alpha 0.5 unless stated.
- Hardware: NVIDIA A100 80GB PCIe (79 GB).
- Seeds: [0, 1, 2, 3, 4]. Cells are mean ± std over seeds where there is more than one.

Sequences per class:

| Split | benign | fuzzing | correlated_signal | max_speedometer | max_coolant_temp | reverse_light |
|---|---|---|---|---|---|---|
| train | 15570 | 215 | 3225 | 4275 | 42 | 6662 |
| test | 4795 | 27 | 965 | 4659 | 42 | 3651 |
| masquerade | 1383 | 0 | 472 | 2282 | 21 | 1788 |

## 4. Ablation

GraMa + centralised, no attack, alpha 0.5. Default edges: transition. Each row changes one thing.

| Variant | Macro-F1 | Change in macro-F1 | Accuracy | Detection rate | False alarm rate | Params |
|---|---|---|---|---|---|---|
| GraMa (full) | 0.9495 ± 0.0387 | – | 0.9899 ± 0.0056 | 0.9860 ± 0.0083 | 0.0014 ± 0.0006 | 78,819 |
| without residual connections in the GAT | 0.9768 ± 0.0077 | +0.0272 | 0.9895 ± 0.0134 | 0.9891 ± 0.0159 | 0.0041 ± 0.0054 | 57,827 |
| without CAN-ID embeddings | 0.7727 ± 0.0190 | -0.1768 | 0.9342 ± 0.0208 | 0.9236 ± 0.0343 | 0.0356 ± 0.0153 | 73,867 |
| mean pooling instead of attention pooling | 0.9300 ± 0.0264 | -0.0196 | 0.9496 ± 0.0404 | 0.9397 ± 0.0530 | 0.0015 ± 0.0011 | 78,754 |
| co-occurrence edges instead of transition edges | 0.7569 ± 0.1504 | -0.1927 | 0.7933 ± 0.0449 | 0.7192 ± 0.0756 | 0.0577 ± 0.0388 | 78,819 |
| GRU instead of Mamba | 0.8095 ± 0.1061 | -0.1400 | 0.8857 ± 0.1099 | 0.8496 ± 0.1547 | 0.0075 ± 0.0075 | 70,783 |
| no temporal model (last window only) | 0.9643 ± 0.0257 | +0.0148 | 0.9735 ± 0.0233 | 0.9723 ± 0.0398 | 0.0232 ± 0.0259 | 45,823 |
| one attention head instead of four | 0.9724 ± 0.0181 | +0.0229 | 0.9822 ± 0.0271 | 0.9976 ± 0.0014 | 0.0058 ± 0.0072 | 46,947 |

## 5. Efficiency (Sec 6.1, 8.1)

One sequence covers 288 CAN frames. Latency is for one sequence at a time; throughput is for batches of 256 on the run's device.

| Model | Params | Size (KB) | Upload per client per round (KB) | CPU latency, 1 thread (ms/sequence) | GPU latency (ms/sequence) | Throughput (sequences/s) |
|---|---|---|---|---|---|---|
| GraMa | 78,819 | 307.9 | 307.9 | 6.18 | 3.57 | 1,938 |
| CNN-BiGRU | 39,895 | 155.8 | 155.8 | 1.45 | 0.89 | 273,834 |

## Notes

- Split: by capture: attack instances 1-2 train, instance 3 tests (with its masquerade version); the coolant attack, recorded once, is cut in the middle of the injection; ambient captures are held out whole.
- The CNN-BiGRU baseline is our implementation of that model family on the same sequences, trained with FedAvg; the original adaptive weighting (AWI) is not reproduced.
- The centralised row trains one model on all the training data with the same number of passes over the data as a federated run. It is a reference, not a federated method.
