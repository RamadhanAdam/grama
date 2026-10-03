# GraMa

Federated intrusion detection for in-vehicle CAN traffic. Each vehicle trains a small model that
reads its CAN traffic as a graph of CAN IDs (a graph attention network) and follows that graph
over time (a Mamba state-space model). The server only ever sees model updates, and it clusters
them with HDBSCAN to keep poisoned vehicles out of the global model.

This repository holds the code and the experiments for the paper. It replaces the 1D-CNN + BiGRU
detector of Mnkash et al. (2026) with GAT + Mamba, and their adaptive weighting (AWI) with
latent-density aggregation, as laid out in my concept note *Redesigning Federated Intrusion
Detection for IoV: The GraMa (Graph-Mamba) Architecture*.

**Status:** the code is complete and tested (unit tests, plus full runs on synthetic CAN traffic).
Results on CIC-IoV2024 come from running the `quick` and `full` profiles below on a GPU.

## Running it on JupyterHub

In a JupyterHub terminal, once:

```bash
git clone https://github.com/RamadhanAdam/grama.git
cd grama
```

Then:

1. Get the data. Fill in the form at http://cicresearch.ca/IOTDataset/CICIoV2024/ (linked from
   https://www.unb.ca/cic/datasets/iov-dataset-2024.html). The download links only work in the
   browser you registered in, so download there: the six CSVs in the `decimal` folder are all you
   need (`CICIoV2024.tar.xz` also works, but it holds the binary and hex versions too and is much
   bigger). Drag them into `grama/data/raw/` in the JupyterHub file browser. Any folder layout
   works, and archives are unpacked for you.
2. Open `GraMa.ipynb`, set `PROFILE` in the first code cell, and Run All.
3. The last cell shows the tables and figures. Everything is also saved under `results/<profile>/`.

To get the latest code later, run `git pull` inside `grama/`. Finished runs are kept.

If the data isn't there yet, the notebook says so and runs the `smoke` profile on synthetic data
instead, so you can see the whole thing work. Those numbers are not results.

## Profiles

| Profile | Data | Setting | Runs | Time |
|---|---|---|---|---|
| `smoke` | synthetic CAN traffic | 8 clients, 6 per round, 6 rounds | 19 | ~5-10 min on a CPU |
| `quick` | CIC-IoV2024, benign capped at 150K rows | 10 clients, 5 per round, 15 rounds, 1 seed | 49 | ~30-60 min on a GPU |
| `full` | CIC-IoV2024, benign capped at 400K rows | 20 clients, 10 per round, 50 rounds, 3 seeds | 183 | several hours on a GPU |

Profiles live in `config/experiments.yaml`; change them there. Every finished run is appended
to `results/<profile>/runs.jsonl` straight away, and runs already in that file are skipped. If
the kernel dies or the server shuts down, start again and it carries on where it stopped.

For `full`, use a terminal rather than the notebook so a closed browser tab can't stop it:

```bash
make full-background
```

```bash
tail -f results/full.log
```

## From a terminal

```bash
make setup
```

```bash
make check-data
```

```bash
make quick
```

`make help` lists the rest: `smoke`, `full`, `report` (rebuild tables and figures from saved runs),
`pack` (zip a profile's results to download), `test`.

## What gets measured

| Group | Question | Concept note |
|---|---|---|
| main | GraMa vs CNN-BiGRU, HDBSCAN vs FedAvg, and a centralised model as the ceiling | Sec 6.2.1 |
| noniid | How skewed client data (Dirichlet alpha 0.05 to 100) affects GraMa | Sec 6.2.2 |
| poisoning | Label flipping, targeted flipping (attacks labelled benign) and magnitude poisoning at 10-40% compromised clients, against FedAvg, median, trimmed mean, Multi-Krum and HDBSCAN | Sec 6.2.3 |
| ablation | GraMa with one part removed or swapped: no residuals, no CAN-ID embeddings, mean pooling, co-occurrence edges, GRU instead of Mamba, no temporal model | |
| efficiency | Parameters, model size (one upload), latency per sequence on one CPU thread and on the GPU, throughput | Sec 6.1, 8.1 |

Each run reports accuracy, macro precision/recall/F1, ROC-AUC, detection rate (attack sequences
flagged as an attack) and false alarm rate (benign sequences flagged), per-class F1, the confusion
matrix, and test macro-F1 per round. For HDBSCAN and Multi-Krum it also counts how many
compromised and honest updates were rejected.

Output in `results/<profile>/`:

```
summary.md          all tables and figures on one page
tables/*.csv        each table, for the paper
figures/*.pdf|png   convergence, non-IID, poisoning, rejection rates, confusion matrix, client label mix
runs.jsonl          one line per run, with per-round history
efficiency.json
models/             final global weights of the clean runs
```

## The data pipeline

CIC-IoV2024 has six classes: benign (1.22M frames), DoS, and spoofing of the gas, RPM, speed and
steering-wheel signals. Columns are the arbitration `ID` and eight payload bytes.
There is no timestamp and no DLC.

1. Each file is one stream of frames in bus order, labelled by its file name.
2. The benign file is capped (150K rows in `quick`, 400K in `full`) so it doesn't swamp the
   attacks.
3. Each file is split in time: the first 80% trains, the last 20% tests. No window or sequence
   crosses the split.
4. The CAN-ID vocabulary (the graph's nodes) and the byte scaling come from the training part only.
   IDs never seen in training share one "other" node.
5. Windows of 64 frames, step 32. Each node gets 10 features per window: its mean scaled payload
   bytes, its share of the window's frames, and a burst flag.
6. Sequences are 8 consecutive windows (288 frames). The label is that of the last window.

Exact duplicates are not removed. DoS and spoofing traffic is the same few frames repeated
(spoofing-GAS: 9,991 rows, 2 distinct), so de-duplication would delete the attacks themselves.
The time-based split is what keeps train and test apart.

In the released files each attack file holds attack frames only, which makes the task easier than
the road. `config/data.yaml` has an `injection` switch that interleaves attack frames with benign
traffic from the same split (30% attack frames by default), the way an injection looks on a real
bus. It is off by default; turning it on gives a harder second setting.

## Choices that differ from the concept note

I tested these on synthetic CAN traffic while building the pipeline. The ablation group measures
them again on the real data, so the paper can report the real effect.

- **Edges.** The note joins two IDs when they appear in the same window. That joins every active ID
  to every other one, so the graph is complete and its structure only says which IDs were active. The default is now
  *transition* edges: i and j are joined when a frame of j directly follows a frame of i on the bus,
  which is closer to "message propagation paths" and changes when frames are injected. Co-occurrence
  is still there (`build.edge_mode`) and is one of the ablation rows.
- **GAT residuals, CAN-ID embeddings, attention pooling.** On a dense graph, attention averages
  every node with all its neighbours, and the one ID being spoofed is washed out before pooling.
  With plain eq. 4-6 and mean pooling, GraMa stayed at chance on synthetic data where an MLP reached
  0.98 F1. Each layer now adds a linear map of the node's own input, each ID gets a learned
  8-dimensional embedding (the vocabulary is fixed per dataset), and a learned score decides which
  nodes make up the window token. All three can be switched off in `config/model.yaml`.
- **HDBSCAN needs `allow_single_cluster`.** With no attackers the honest updates form one cluster.
  scikit-learn's default refuses a single cluster and labels every point noise, which rejected
  every update and froze the global model. It is now on.
- **phi is trained properly.** Raw updates have entries around 1e-3 to 1e-5, and 10 Adam steps on
  them left the autoencoder at its random start (its reconstruction error was about 100 times the
  input variance), so HDBSCAN was clustering a random projection. Updates are now centred across
  clients and scaled to order-1 entries (one scale per round, so an oversized update still stands
  out), and phi trains for 200 steps.
- **Latent scaling and epsilon.** phi is refitted each round, so its latent scale means nothing.
  The latent points are scaled to their median spread and `cluster_selection_epsilon = 2.0` is in
  those units. On updates recorded from training on synthetic data, with attackers in the round it
  rejected every magnitude-poisoned update and 1-2% of honest ones. In rounds with no attacker at
  all it still dropped about a quarter of the honest updates (cohorts of 5). Epsilon 1.5 catches
  more label flippers and rejects more honest clients; a sweep over epsilon would make a good
  sensitivity figure.
- **Mamba.** Without `mamba-ssm` the block uses a pure-PyTorch scan, which is plenty for sequences
  of 8. The depthwise convolution inside it is written as four shifted multiply-adds, with the same
  weights and output, because PyTorch's CPU backward for depthwise Conv1d took most of each training
  step.

One thing to expect in the results: on synthetic data, label flipping under non-IID data was hard
for every distance-based rule (HDBSCAN caught 5-30% of flipped updates depending on epsilon, and
Multi-Krum did no better). A flipped client looks much like another unusual honest client. Feeding
phi only the last layer (`phi_input: last_layer`, after Tolpegin et al., 2020) did not help there.
Magnitude poisoning was caught every time. The real runs will show whether this holds on
CIC-IoV2024.

## Baseline

`src/grama/models/baseline.py` is my implementation of a CNN-BiGRU detector on the same sequences:
a 1D CNN over the frames of each window (ID embedding plus payload bytes), a BiGRU over the
windows, and attention pooling. It sees the raw frames, so it has at least as much information as
GraMa. It is not a line-by-line copy of Mnkash et al., and their AWI aggregation is not
reproduced; it trains with FedAvg (and HDBSCAN in the `full` profile).

## Layout

```
GraMa.ipynb              run everything from here
config/                  data, model, federated settings and the experiment profiles
src/grama/
  data/                  dataset builder (build.py), sequence dataset, data check, Dirichlet split
  models/                GAT encoder, Mamba block, GraMa model, CNN-BiGRU baseline
  federated/             client (with the attacks), server, HDBSCAN aggregator, baseline rules
  attacks/               poisoning helpers
  eval/                  metrics, latency
  experiments/           runner and report
scripts/                 run_experiments.py, build_dataset.py, run_federated_train.py (one run)
tests/                   unit tests and a small end-to-end test, all on CPU, no data needed
docs/architecture.md     which file implements which equation of the concept note
```

## Tests

```bash
make test
```

## License

MIT, see [LICENSE](LICENSE). If you use this code, please cite the paper once it's out; until then,
link to this repository.

## Data reference

E. C. P. Neto, H. Taslimasa, S. Dadkhah, S. Iqbal, P. Xiong, T. Rahman, A. A. Ghorbani.
CICIoV2024: Advancing realistic IDS approaches against DoS and spoofing attack in IoV CAN bus.
*Internet of Things* 26 (2024) 101209.
