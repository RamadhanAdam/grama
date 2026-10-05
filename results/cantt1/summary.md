# GraMa results: `cantt1` profile

Generated 2026-10-05 03:53 from 51 runs.

- Data: can-train-and-test (`cantt_set_01_b0e5a072.pt`), 53 CAN-ID nodes, windows of 64 frames (stride 32), sequences of 8 windows, edges: transition.
- Federated setting: 20 clients, 10 per round, 30 rounds, 2 local epoch(s), batch 64, lr 0.001, Dirichlet alpha 0.5 unless stated.
- Hardware: NVIDIA A100 80GB PCIe (79 GB).
- Seeds: [0, 1, 2]. Cells are mean ± std over seeds where there is more than one.

Sequences per class:

| Split | benign | attack |
|---|---|---|
| train | 9059 | 2543 |
| test | 3852 | 2635 |
| unknown_vehicle | 5673 | 1868 |
| unknown_attack | 7449 | 3324 |
| unknown_vehicle_and_attack | 7824 | 1881 |

## 1. Main comparison, no attack (Sec 6.2.1)

| Method | Accuracy | Macro-P | Macro-R | Macro-F1 | ROC-AUC | Detection rate | False alarm rate | Params | Train time (s) |
|---|---|---|---|---|---|---|---|---|---|
| GraMa + HDBSCAN (ours) | 0.9217 ± 0.0138 | 0.9415 ± 0.0089 | 0.9038 ± 0.0170 | 0.9156 ± 0.0156 | 0.9814 ± 0.0049 | 0.8083 ± 0.0342 | 0.0008 ± 0.0007 | 78,255 | 206 |
| GraMa + FedAvg | 0.9157 ± 0.0169 | 0.9380 ± 0.0110 | 0.8962 ± 0.0207 | 0.9087 ± 0.0191 | 0.9836 ± 0.0038 | 0.7927 ± 0.0414 | 0.0002 ± 0.0001 | 78,255 | 161 |
| CNN-BiGRU + FedAvg | 0.9417 ± 0.0377 | 0.9566 ± 0.0265 | 0.9283 ± 0.0465 | 0.9370 ± 0.0414 | 0.9957 ± 0.0018 | 0.8572 ± 0.0934 | 0.0005 ± 0.0004 | 38,899 | 31 |
| CNN-BiGRU + HDBSCAN (ours) | 0.9354 ± 0.0366 | 0.9520 ± 0.0258 | 0.9207 ± 0.0452 | 0.9302 ± 0.0402 | 0.9936 ± 0.0040 | 0.8424 ± 0.0907 | 0.0010 ± 0.0004 | 38,899 | 61 |
| GraMa, centralised | 0.9627 ± 0.0096 | 0.9703 ± 0.0072 | 0.9542 ± 0.0118 | 0.9607 ± 0.0103 | 0.9869 ± 0.0017 | 0.9090 ± 0.0233 | 0.0006 ± 0.0003 | 78,255 | 114 |

Detection rate = attack sequences flagged as any attack; false alarm rate = benign sequences flagged as an attack.

### Other test sets

The same models, tested on the extra sets. Macro scores are averaged over the classes each set contains. Frames with a CAN ID training never saw: test 0%, unknown car, known attacks 61%, known car, unknown attacks 0%, unknown car, unknown attacks 29%.

| Method | Unknown car, known attacks: Macro-F1 | Unknown car, known attacks: Detection rate | Unknown car, known attacks: False alarm rate | Known car, unknown attacks: Macro-F1 | Known car, unknown attacks: Detection rate | Known car, unknown attacks: False alarm rate | Unknown car, unknown attacks: Macro-F1 | Unknown car, unknown attacks: Detection rate | Unknown car, unknown attacks: False alarm rate |
|---|---|---|---|---|---|---|---|---|---|
| GraMa + HDBSCAN (ours) | 0.3527 ± 0.1090 | 0.3337 ± 0.4712 | 0.3335 ± 0.4713 | 0.4140 ± 0.0057 | 0.0049 ± 0.0053 | 0.0000 ± 0.0000 | 0.4081 ± 0.1758 | 0.4058 ± 0.4206 | 0.3569 ± 0.4552 |
| GraMa + FedAvg | 0.2760 ± 0.1084 | 0.6656 ± 0.4706 | 0.6660 ± 0.4709 | 0.4119 ± 0.0039 | 0.0029 ± 0.0037 | 0.0000 ± 0.0000 | 0.4476 ± 0.2319 | 0.4916 ± 0.4070 | 0.3527 ± 0.4583 |
| CNN-BiGRU + FedAvg | 0.3524 ± 0.1088 | 0.3333 ± 0.4714 | 0.3333 ± 0.4714 | 0.4351 ± 0.0305 | 0.0259 ± 0.0302 | 0.0000 ± 0.0001 | 0.5571 ± 0.0740 | 0.3498 ± 0.2431 | 0.1847 ± 0.2391 |
| CNN-BiGRU + HDBSCAN (ours) | 0.3531 ± 0.1093 | 0.3344 ± 0.4706 | 0.3348 ± 0.4704 | 0.4277 ± 0.0244 | 0.0184 ± 0.0239 | 0.0000 ± 0.0000 | 0.5355 ± 0.1049 | 0.3814 ± 0.2394 | 0.2456 ± 0.3076 |
| GraMa, centralised | 0.2010 ± 0.0034 | 0.9996 ± 0.0005 | 0.9978 ± 0.0032 | 0.4535 ± 0.0503 | 0.0456 ± 0.0523 | 0.0003 ± 0.0002 | 0.4899 ± 0.2374 | 0.5003 ± 0.3615 | 0.3339 ± 0.4710 |

### Per-class F1

| Method | benign | attack |
|---|---|---|
| GraMa + HDBSCAN (ours) | 0.9382 | 0.8931 |
| GraMa + FedAvg | 0.9339 | 0.8836 |
| CNN-BiGRU + FedAvg | 0.9541 | 0.9200 |
| CNN-BiGRU + HDBSCAN (ours) | 0.9492 | 0.9112 |
| GraMa, centralised | 0.9696 | 0.9518 |

## 3. Poisoning (Sec 6.2.3)

GraMa, Dirichlet alpha 0.5. Columns are the share of compromised clients; 0 is the clean run.

### Targeted flipping (attack -> benign): Macro-F1

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.9087 ± 0.0191 | 0.3933 ± 0.0084 | 0.3726 ± 0.0000 |
| Norm clipping | 0.9064 ± 0.0340 | 0.7053 ± 0.1928 | 0.5505 ± 0.1725 |
| FLAME | 0.8945 ± 0.0608 | 0.7903 ± 0.1136 | 0.7347 ± 0.1487 |
| HDBSCAN (ours) | 0.9156 ± 0.0156 | 0.8770 ± 0.0348 | 0.8932 ± 0.0464 |

### Targeted flipping (attack -> benign): Detection rate

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.7927 ± 0.0414 | 0.0194 ± 0.0080 | 0.0000 ± 0.0000 |
| Norm clipping | 0.7888 ± 0.0738 | 0.4564 ± 0.3125 | 0.2207 ± 0.2157 |
| FLAME | 0.7672 ± 0.1304 | 0.5721 ± 0.2093 | 0.4860 ± 0.2518 |
| HDBSCAN (ours) | 0.8083 ± 0.0342 | 0.7268 ± 0.0732 | 0.8175 ± 0.1548 |

### ALIE (crafted to look honest): Macro-F1

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.9087 ± 0.0191 | 0.9145 ± 0.0322 | 0.9034 ± 0.0091 |
| Norm clipping | 0.9064 ± 0.0340 | 0.9095 ± 0.0310 | 0.9008 ± 0.0021 |
| FLAME | 0.8945 ± 0.0608 | 0.9329 ± 0.0391 | 0.6216 ± 0.2682 |
| HDBSCAN (ours) | 0.9156 ± 0.0156 | 0.9211 ± 0.0280 | 0.6560 ± 0.2295 |

### ALIE (crafted to look honest): Detection rate

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.7927 ± 0.0414 | 0.8061 ± 0.0706 | 0.7992 ± 0.0349 |
| Norm clipping | 0.7888 ± 0.0738 | 0.7953 ± 0.0677 | 0.7867 ± 0.0011 |
| FLAME | 0.7672 ± 0.1304 | 0.8539 ± 0.0937 | 0.8732 ± 0.1146 |
| HDBSCAN (ours) | 0.8083 ± 0.0342 | 0.8207 ± 0.0620 | 0.4137 ± 0.3552 |

### Rejected updates

TPR: share of compromised clients' updates rejected. FPR: share of honest clients' updates rejected. Median, trimmed mean and norm clipping reject no client as a whole, so they are not listed.

| Attack | Aggregator | 20% TPR / FPR | 40% TPR / FPR |
|---|---|---|---|
| Targeted flipping | FLAME | 0.54 / 0.26 | 0.39 / 0.26 |
| Targeted flipping | HDBSCAN (ours) | 0.53 / 0.09 | 0.37 / 0.03 |
| ALIE | FLAME | 0.00 / 0.45 | 0.00 / 0.48 |
| ALIE | HDBSCAN (ours) | 0.00 / 0.32 | 0.04 / 0.46 |

## 5. Efficiency (Sec 6.1, 8.1)

One sequence covers 288 CAN frames. Latency is for one sequence at a time; throughput is for batches of 256 on the run's device.

| Model | Params | Size (KB) | Upload per client per round (KB) | CPU latency, 1 thread (ms/sequence) | GPU latency (ms/sequence) | Throughput (sequences/s) |
|---|---|---|---|---|---|---|
| GraMa | 78,255 | 305.7 | 305.7 | 3.12 | 6.78 | 24,707 |
| CNN-BiGRU | 38,899 | 151.9 | 151.9 | 1.21 | 4.35 | 330,846 |

## Figures

PNG to look at, PDF with the same name for LaTeX.

**Test macro-F1 per round, no attack**

![Test macro-F1 per round, no attack](figures/convergence.png)

**Confusion matrix (row-normalised)**

![Confusion matrix (row-normalised)](figures/confusion_matrix.png)

**Label mix per client**

![Label mix per client](figures/client_distribution.png)

**Macro-F1 under poisoning**

![Macro-F1 under poisoning](figures/poisoning.png)

**How often compromised (TPR) and honest (FPR) updates were rejected**

![How often compromised (TPR) and honest (FPR) updates were rejected](figures/defence_rates.png)

## Notes

- Split: the dataset's own folders for set_01: train_01 trains, test_01 (known car, known attacks) tests, test_02-04 are the extra test sets.
- The CNN-BiGRU baseline is our implementation of that model family on the same sequences, trained with FedAvg; the original adaptive weighting (AWI) is not reproduced.
- The centralised row trains one model on all the training data with the same number of passes over the data as a federated run. It is a reference, not a federated method.
