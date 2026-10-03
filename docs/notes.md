# Notes

Things I found while building the experiments, and where the code differs from the concept note.

## The dataset

| File | Rows | Distinct frames | CAN IDs |
|---|---|---|---|
| benign | 1,223,737 | 3,547 | 72 |
| DoS | 74,663 | 21 | 291 |
| spoofing-GAS | 9,991 | 2 | 513 |
| spoofing-RPM | 54,900 | 10 | 476, then 513 for the last 36% |
| spoofing-SPEED | 24,951 | 5 | 344, then 513 for the last 20% |
| spoofing-STEERING_WHEEL | 19,977 | 3 | 128 |

Each attack file is a few frames repeated in long runs, and none of the attack IDs appears in the
benign traffic. So a model that sees IDs can separate attack from benign almost perfectly, and the
clean results sit near the ceiling. The interesting results are under poisoning and non-IID data.

I don't remove duplicate rows. The attacks are mostly duplicates (spoofing-GAS has 9,991 rows and 2
distinct frames), so removing them would remove the attacks.

## Why not a time split

The RPM and SPEED files end on ID 513, which is the GAS ID, with payloads that don't occur earlier
in either file. If the last 20% of each file is the test set, those runs are only in the test set
and no model can learn them. On the `quick` profile every method, the centralised one included,
stopped at a macro-F1 of about 0.56, with RPM and SPEED wrong.

So each file is cut into blocks of 1,000 rows and every fifth block goes to test. Windows are built
inside a block, so none crosses from train to test. With this split the centralised model gets
1.000. The time split is still there (`build.split: temporal` in `config/data.yaml`).

## Changes from the concept note

Edges. The note joins two IDs when they appear in the same window. That makes a complete graph over
the active IDs, which only says which IDs were active. I join two IDs when a frame of one directly
follows a frame of the other. Co-occurrence edges are still an option and one of the ablation runs.

The graph encoder. With plain eq. 4-6 and mean pooling, GraMa stayed at chance on synthetic data
where a simple MLP got 0.98 F1. On a dense graph each node is averaged with all its neighbours and
the spoofed ID gets washed out. Each GAT layer now adds a linear map of the node's own input, each
ID has a learned 8-number embedding, and attention pooling picks which nodes make up the window
summary. All three can be turned off in `config/model.yaml`, and the ablation measures each.

HDBSCAN. scikit-learn's HDBSCAN won't return a single cluster by default. With no attackers the
honest updates are one cluster, so every update was labelled noise and the model never trained.
`allow_single_cluster` is now on.

The autoencoder (phi, eq. 11). The raw updates are around 1e-3 to 1e-5 per entry, and 10 Adam steps
left the autoencoder where it started, so HDBSCAN was clustering a random projection. The updates
are now centred across clients and scaled so the median update has entries around 1 (one scale per
round, so a large update still stands out), and phi trains for 200 steps.

Epsilon. phi is refitted every round, so the latent points are first scaled to their median spread,
and `cluster_selection_epsilon = 2.0` is in those units. On updates recorded from synthetic training,
rounds with attackers lost every magnitude-poisoned update and 1-2% of honest ones. Rounds with no
attacker still lost about a quarter of honest updates (cohorts of 5). A smaller epsilon catches
more label flippers and loses more honest updates, so a sweep over epsilon would be worth adding.

Mamba. Without `mamba-ssm` the block uses a plain PyTorch scan, which is fine for sequences of 8.
Its depthwise convolution is written as four shifted multiply-adds (same weights, same output),
because PyTorch's CPU backward for depthwise Conv1d took most of each training step.

## Compared with FLAME

FLAME (Nguyen et al., USENIX Security 2022) also uses HDBSCAN on client updates. It clusters the raw
updates by cosine distance, then clips the kept ones to the median norm and adds noise. GraMa's
defence clusters in phi's latent space and weights the kept clients by HDBSCAN membership, without
clipping or noise. FLAME runs as a baseline.

## The baseline

`src/grama/models/baseline.py` is my own CNN-BiGRU on the same sequences: a 1D CNN over the frames
of each window, a BiGRU over the windows, and attention pooling. It sees the raw frames. It is not a
copy of Mnkash et al.'s model, and their AWI aggregation is not reproduced, so it trains with FedAvg
(and HDBSCAN in the `full` profile).

## What to expect

On synthetic data, label flipping under non-IID data was hard for every distance-based rule:
HDBSCAN caught 5-30% of flipped updates depending on epsilon, and Multi-Krum did no better. Feeding
phi only the last layer (`phi_input: last_layer`, after Tolpegin et al., 2020) didn't help. Magnitude
poisoning was caught every time.
