# GraMa results: `road` profile

Generated 2026-10-05 01:03 from 51 runs.

- Data: ROAD (`road_0bc0ca64.pt`), 107 CAN-ID nodes, windows of 64 frames (stride 32), sequences of 8 windows, edges: transition.
- Federated setting: 20 clients, 10 per round, 30 rounds, 2 local epoch(s), batch 64, lr 0.001, Dirichlet alpha 0.5 unless stated.
- Hardware: NVIDIA A100 80GB PCIe (79 GB).
- Seeds: [0, 1, 2]. Cells are mean ± std over seeds where there is more than one.

Sequences per class:

| Split | benign | fuzzing | correlated_signal | max_speedometer | max_coolant_temp | reverse_light |
|---|---|---|---|---|---|---|
| train | 15570 | 215 | 3225 | 4275 | 42 | 6662 |
| test | 4795 | 27 | 965 | 4659 | 42 | 3651 |
| masquerade | 1383 | 0 | 472 | 2282 | 21 | 1788 |

## 1. Main comparison, no attack (Sec 6.2.1)

| Method | Accuracy | Macro-P | Macro-R | Macro-F1 | ROC-AUC | Detection rate | False alarm rate | Params | Train time (s) |
|---|---|---|---|---|---|---|---|---|---|
| GraMa + HDBSCAN (ours) | 0.8485 ± 0.1124 | 0.7141 ± 0.1071 | 0.6806 ± 0.1127 | 0.6861 ± 0.1211 | 0.9774 ± 0.0154 | 0.8799 ± 0.0977 | 0.0054 ± 0.0028 | 78,819 | 544 |
| GraMa + FedAvg | 0.8250 ± 0.1015 | 0.6826 ± 0.1275 | 0.6615 ± 0.1427 | 0.6576 ± 0.1494 | 0.9624 ± 0.0165 | 0.9002 ± 0.0305 | 0.0132 ± 0.0172 | 78,819 | 598 |
| CNN-BiGRU + FedAvg | 0.5915 ± 0.1268 | 0.4412 ± 0.2084 | 0.4662 ± 0.1607 | 0.3959 ± 0.2011 | 0.8587 ± 0.0872 | 0.8256 ± 0.0389 | 0.0270 ± 0.0204 | 39,895 | 107 |
| CNN-BiGRU + HDBSCAN (ours) | 0.6446 ± 0.1803 | 0.4532 ± 0.2366 | 0.4383 ± 0.1913 | 0.4005 ± 0.2317 | 0.8560 ± 0.0947 | 0.8231 ± 0.1480 | 0.0252 ± 0.0320 | 39,895 | 155 |
| GraMa, centralised | 0.9887 ± 0.0046 | 0.9945 ± 0.0022 | 0.9282 ± 0.0389 | 0.9512 ± 0.0272 | 0.9987 ± 0.0012 | 0.9843 ± 0.0066 | 0.0010 ± 0.0002 | 78,819 | 632 |

Detection rate = attack sequences flagged as any attack; false alarm rate = benign sequences flagged as an attack.

### Other test sets

The same models, tested on the extra sets. Macro scores are averaged over the classes each set contains. Frames with a CAN ID training never saw: test 0%, masquerade attacks only 0%.

| Method | Masquerade attacks only: Macro-F1 | Masquerade attacks only: Detection rate | Masquerade attacks only: False alarm rate |
|---|---|---|---|
| GraMa + HDBSCAN (ours) | 0.6810 ± 0.1312 | 0.8879 ± 0.1013 | 0.0055 ± 0.0033 |
| GraMa + FedAvg | 0.6734 ± 0.1019 | 0.9094 ± 0.0302 | 0.0200 ± 0.0257 |
| CNN-BiGRU + FedAvg | 0.4163 ± 0.1406 | 0.8774 ± 0.0544 | 0.0381 ± 0.0257 |
| CNN-BiGRU + HDBSCAN (ours) | 0.4478 ± 0.2085 | 0.8974 ± 0.0705 | 0.0349 ± 0.0423 |
| GraMa, centralised | 0.9454 ± 0.0276 | 0.9835 ± 0.0066 | 0.0014 ± 0.0000 |

### Per-class F1

| Method | benign | fuzzing | correlated_signal | max_speedometer | max_coolant_temp | reverse_light |
|---|---|---|---|---|---|---|
| GraMa + HDBSCAN (ours) | 0.8989 | 0.9482 | 0.6111 | 0.8721 | 0.0000 | 0.7860 |
| GraMa + FedAvg | 0.9054 | 0.6422 | 0.8798 | 0.7721 | 0.0000 | 0.7459 |
| CNN-BiGRU + FedAvg | 0.8423 | 0.3330 | 0.3387 | 0.3547 | 0.0000 | 0.5067 |
| CNN-BiGRU + HDBSCAN (ours) | 0.8526 | 0.2484 | 0.3337 | 0.3482 | 0.0000 | 0.6202 |
| GraMa, centralised | 0.9845 | 0.9874 | 0.9979 | 0.9980 | 0.7578 | 0.9818 |

## 3. Poisoning (Sec 6.2.3)

GraMa, Dirichlet alpha 0.5. Columns are the share of compromised clients; 0 is the clean run.

### Targeted flipping (attack -> benign): Macro-F1

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.6576 ± 0.1494 | 0.5116 ± 0.1452 | 0.1441 ± 0.0488 |
| Norm clipping | 0.7121 ± 0.0680 | 0.4378 ± 0.0488 | 0.0887 ± 0.0043 |
| FLAME | 0.7606 ± 0.0283 | 0.7801 ± 0.0037 | 0.1487 ± 0.0643 |
| HDBSCAN (ours) | 0.6861 ± 0.1211 | 0.6491 ± 0.0670 | 0.1256 ± 0.0410 |

### Targeted flipping (attack -> benign): Detection rate

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.9002 ± 0.0305 | 0.3953 ± 0.2913 | 0.0363 ± 0.0206 |
| Norm clipping | 0.8642 ± 0.0523 | 0.5957 ± 0.0081 | 0.0049 ± 0.0049 |
| FLAME | 0.9563 ± 0.0033 | 0.9648 ± 0.0105 | 0.3753 ± 0.3746 |
| HDBSCAN (ours) | 0.8799 ± 0.0977 | 0.9004 ± 0.0043 | 0.2862 ± 0.2825 |

### ALIE (crafted to look honest): Macro-F1

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.6576 ± 0.1494 | 0.6307 ± 0.1739 | 0.4815 ± 0.1859 |
| Norm clipping | 0.7121 ± 0.0680 | 0.7088 ± 0.0836 | 0.4298 ± 0.1395 |
| FLAME | 0.7606 ± 0.0283 | 0.6204 ± 0.1089 | 0.0844 ± 0.0054 |
| HDBSCAN (ours) | 0.6861 ± 0.1211 | 0.7543 ± 0.0302 | 0.0967 ± 0.0017 |

### ALIE (crafted to look honest): Detection rate

| Aggregator | 0% | 20% | 40% |
|---|---|---|---|
| FedAvg | 0.9002 ± 0.0305 | 0.7190 ± 0.2230 | 0.7810 ± 0.1417 |
| Norm clipping | 0.8642 ± 0.0523 | 0.8447 ± 0.1306 | 0.7608 ± 0.2151 |
| FLAME | 0.9563 ± 0.0033 | 0.7946 ± 0.1222 | 0.5638 ± 0.4361 |
| HDBSCAN (ours) | 0.8799 ± 0.0977 | 0.9021 ± 0.0502 | 0.5586 ± 0.4394 |

### Rejected updates

TPR: share of compromised clients' updates rejected. FPR: share of honest clients' updates rejected. Median, trimmed mean and norm clipping reject no client as a whole, so they are not listed.

| Attack | Aggregator | 20% TPR / FPR | 40% TPR / FPR |
|---|---|---|---|
| Targeted flipping | FLAME | 0.72 / 0.25 | 0.46 / 0.16 |
| Targeted flipping | HDBSCAN (ours) | 0.63 / 0.12 | 0.20 / 0.14 |
| ALIE | FLAME | 0.00 / 0.48 | 0.02 / 0.46 |
| ALIE | HDBSCAN (ours) | 0.00 / 0.34 | 0.02 / 0.51 |

## 5. Efficiency (Sec 6.1, 8.1)

One sequence covers 288 CAN frames. Latency is for one sequence at a time; throughput is for batches of 256 on the run's device.

| Model | Params | Size (KB) | Upload per client per round (KB) | CPU latency, 1 thread (ms/sequence) | GPU latency (ms/sequence) | Throughput (sequences/s) |
|---|---|---|---|---|---|---|
| GraMa | 78,819 | 307.9 | 307.9 | 6.21 | 3.73 | 4,663 |
| CNN-BiGRU | 39,895 | 155.8 | 155.8 | 1.55 | 0.92 | 43,435 |

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

- Split: by capture: attack instances 1-2 train, instance 3 tests (with its masquerade version); the coolant attack, recorded once, is cut in the middle of the injection; ambient captures are held out whole.
- The CNN-BiGRU baseline is our implementation of that model family on the same sequences, trained with FedAvg; the original adaptive weighting (AWI) is not reproduced.
- The centralised row trains one model on all the training data with the same number of passes over the data as a federated run. It is a reference, not a federated method.
