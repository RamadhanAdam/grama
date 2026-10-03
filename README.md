# GraMa

Federated intrusion detection for in-vehicle CAN traffic.

Each car trains a small detector on its own traffic. The detector turns every window of CAN
messages into a graph of message IDs, reads it with a graph attention network, and follows the
windows over time with a Mamba model. Cars send only model updates to a server, and the server
clusters those updates with HDBSCAN to leave out cars that look poisoned.

This repository has the code and experiments for my paper on GraMa, which replaces the CNN-BiGRU
detector and AWI aggregation of Mnkash et al. (2026). For a visual walk-through, see
[How GraMa works](https://ramadhanadam.github.io/grama/explainer.html).

## Running it

On JupyterHub, or any machine with a GPU:

```bash
git clone https://github.com/RamadhanAdam/grama.git
cd grama
python3 -m pip install -r requirements.txt
```

Put the data in `data/raw/` (see below). Then open `GraMa.ipynb` and run all cells, or start a
profile from the terminal:

```bash
nohup python3 scripts/run_experiments.py --profile full --no-progress > full.log 2>&1 &
```

Results go to `results/<profile>/`: `summary.md`, the tables as CSV and the figures as PDF and
PNG. Each finished run is saved straight away, so if the job stops, run the same command again
and it carries on.

| Profile | What it is | Runs | Time |
|---|---|---|---|
| `smoke` | synthetic CAN traffic, to check that everything works | 19 | about 5 min on a CPU |
| `quick` | real data, short runs | 77 | about 1.5 h on an A100 |
| `full` | the paper setting | 291 | about 12 h on an A100 |

The profiles are in `config/experiments.yaml`.

## Data

CIC-IoV2024 (Neto et al., 2024), from the
[CIC website](https://www.unb.ca/cic/datasets/iov-dataset-2024.html). The download asks for a
short form, and the links only work in the browser you registered in. I use the six CSVs in the
`decimal` folder. Put them, or the whole `.tar.xz`, in `data/raw/` and check them with:

```bash
PYTHONPATH=src python3 -m grama.data.download
```

Train and test come from interleaved blocks of 1,000 messages in each file; every fifth block is
for testing. A plain time split doesn't work on this dataset. [docs/notes.md](docs/notes.md) explains why,
along with the other places where the code differs from the concept note.

## Experiments

- Main: GraMa against a CNN-BiGRU detector, with and without the HDBSCAN defence, and a
  centralised model for reference
- Non-IID data: Dirichlet alpha from 0.05 to 100
- Poisoning: label flipping, targeted flipping, magnitude poisoning and ALIE, with 10 to 40% of
  cars hacked, against FedAvg, median, trimmed mean, Multi-Krum, norm clipping, FLAME and HDBSCAN
- Ablation: parts of GraMa removed or swapped one at a time
- Efficiency: model size, latency and throughput

## Layout

```
GraMa.ipynb    runs everything
config/        settings and experiment profiles
src/grama/     data, models, federated learning, attacks, evaluation, experiment runner
scripts/       command-line entry points
tests/         unit tests (CPU only, no data needed)
docs/          explainer.html, notes.md, architecture.md
```

Run the tests with `python3 -m pytest`.

## License

MIT. The dataset is from E. C. P. Neto, H. Taslimasa, S. Dadkhah, S. Iqbal, P. Xiong, T. Rahman
and A. A. Ghorbani, "CICIoV2024: Advancing realistic IDS approaches against DoS and spoofing attack
in IoV CAN bus", Internet of Things 26 (2024) 101209.
