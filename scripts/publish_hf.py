"""Upload a profile's results and model weights to the Hugging Face Hub, with a model card.

    python3 scripts/publish_hf.py --profile full              # private repo <your username>/grama
    python3 scripts/publish_hf.py --profile full --public
    python3 scripts/publish_hf.py --profile full --dry-run    # only write results/full/README.md
    python3 scripts/publish_hf.py --profile road --path-in-repo road   # another dataset, in its own folder
    python3 scripts/publish_hf.py --profile full --card-only           # update the main card only

The card is written to results/<profile>/README.md. For the main profile (no --path-in-repo) it becomes
the repo's README; for another dataset it goes in that dataset's folder.
Needs `pip install huggingface_hub` and a login (`huggingface-cli login`, `hf auth login` or HF_TOKEN).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CARD = """---
license: mit
library_name: pytorch
tags:
- intrusion-detection
- can-bus
- automotive-security
- federated-learning
- graph-neural-network
- mamba
metrics:
- accuracy
- f1
---

# GraMa

Weights and results of GraMa, a federated intrusion detector for in-vehicle CAN traffic.

Each vehicle trains a local detector. The detector turns every window of CAN messages into a graph
of message IDs, encodes it with a graph attention network, and reads the sequence of windows with a
Mamba state-space model. Vehicles share only model updates. The server clusters the updates with
HDBSCAN in a learned latent space and leaves out those that fall outside the main cluster.

- Code: https://github.com/RamadhanAdam/grama
- How it works, with interactive figures: https://ramadhanadam.github.io/grama/explainer.html

## Files

| Path | Contents |
|---|---|
| `models/` | weights of every run without an attack at Dirichlet alpha {alpha} (PyTorch state dicts), named `<model>-<aggregator>-a{alpha}-clean-f0-s<seed>.pt` |
| `config/` | the model, data and federated settings used |
| `summary.md` | all tables and figures; the same content is under Results below |
| `tables/` | every table as CSV |
| `figures/` | figures as PNG and PDF |
| `runs.jsonl` | one record per training run ({runs} runs), with per-round metrics and the rejected updates |
| `dataset.json`, `profile.json` | data and experiment settings |

## Training

- Data: CIC-IoV2024 (Neto et al., 2024), the decimal CSVs. The dataset is not included here; the
  Canadian Institute for Cybersecurity provides it after a free registration.
- {nodes} CAN IDs. Windows of {window} messages with stride {stride}; one sequence is {seq_len}
  windows. {train} training and {test} test sequences.
- Split: each file is cut into blocks of {block_rows} rows, and every fifth block is held out for testing.
- Federated setting: {clients} clients, {per_round} per round, {rounds} rounds, {local_epochs} local
  epochs, Dirichlet alpha {alpha} unless a table says otherwise.
- Hardware: {device}.

## Using the weights

```python
import json, torch, yaml
from grama.models.classifier_head import GraMaLocalModel  # from the GitHub repo, with src/ on the path

cfg = yaml.safe_load(open("config/model.yaml"))
meta = json.load(open("dataset.json"))
gat = {{**cfg["gat_encoder"], "in_features": meta["in_features"]}}
head = {{**cfg["classifier_head"], "num_classes": len(meta["class_names"])}}
model = GraMaLocalModel(gat, cfg["mamba_block"], head, num_nodes=meta["num_nodes"])
model.load_state_dict(torch.load("models/grama-hdbscan-a{alpha}-clean-f0-s0.pt", map_location="cpu"))
model.eval()
```

The model takes `node_features` of shape (batch, {seq_len}, {nodes}, {feats}) and `adjacency` of shape
(batch, {seq_len}, {nodes}, {nodes}), and returns logits for {classes}. `grama.data` in the GitHub repo
builds these inputs from the CIC-IoV2024 CSVs.

## Limitations

- CIC-IoV2024 is an easy benchmark: the attack messages use IDs that never appear in normal
  traffic, so without attacks every method reaches a macro-F1 close to 1. The methods differ under
  poisoning and with skewed clients.
- With very skewed clients, the HDBSCAN defence can leave out honest clients whose updates look
  unusual, and then does worse than FedAvg. See the non-IID table.
- ALIE, an attack built to look like an honest update, lowers macro-F1 for every defence at 30–40%
  compromised clients, this one included.
- The results on ROAD and can-train-and-test, and every newer experiment, are in their own folders
  (see Folders by paper below).

## Folders by paper

The experiments serve two papers. The top level of this repo is the `full` profile on CIC-IoV2024; every
other profile is in its own folder, with its own card, tables, figures, per-run records and, where runs
without an attack exist, weights. Confidence intervals and paired tests are in the GitHub repo under
`results/stats/`.

**Paper 1: the defence against poisoned updates**

| Folder | What it answers |
|---|---|
| (top level) | the main grid on CIC-IoV2024: seven aggregation rules, four attacks, 10 to 40% of clients compromised |
| `cic_seeds/` | the same grid with at least three seeds in every cell, five at 30 and 40% |
| `new_baselines/` | FoolsGold, DeepSight (simplified) and FreqFed on the same grid |
| `def_ablation/` | what each part of the defence adds (autoencoder, PCA or raw updates; rescaling; last layer only) |
| `def_grid/` | how sensitive the defence is to its two clustering settings |
| `alie_duplicates/` | ALIE with noise added, to check the defence does not rely on identical colluding updates |
| `clients40/` | 40 clients, 20 per round |
| `cic_adaptive/`, `cic_adaptive_new/` | the adaptive attack, which knows the defence, against every aggregation rule |
| `road/`, `road_new_baselines/` | ROAD (Verma et al., 2024): poisoning, and the three newer baselines |
| `cantt1/`, `cantt1_adaptive/`, `cantt1_new_baselines/` | can-train-and-test set 1 (Lampe and Meng, 2024): poisoning, the adaptive attack, the newer baselines |

**Paper 2: the detector**

| Folder | What it answers |
|---|---|
| `det_road_central/` | ROAD, centralised: GraMa against CNN-BiGRU, a GCN, a GCN with a GRU and a Transformer, ten seeds |
| `det_road_fedavg/` | the same five models trained federated with FedAvg |
| `det_road_ablation/` | what each part of GraMa adds: the full model against eight variants |
| `det_cantt1/` … `det_cantt4/` | can-train-and-test sets 1 to 4, centralised, also scored on an unknown car and unknown attacks |
| `det_cic/` | CIC-IoV2024, a sanity check |
| `cantt2/` … `cantt4/` | the earlier federated comparison on sets 2 to 4, without attacks |

## Citation

Two papers are in preparation, one on the defence and one on the detector. Until they are published,
please cite the GitHub repository.
The dataset:

> E. C. P. Neto, H. Taslimasa, S. Dadkhah, S. Iqbal, P. Xiong, T. Rahman and A. A. Ghorbani.
> CICIoV2024: Advancing realistic IDS approaches against DoS and spoofing attack in IoV CAN bus.
> *Internet of Things* 26 (2024) 101209.

## Results

{results}
"""


DATASET_NAME = {"road": "ROAD (Verma et al., 2024)",
                "can_train_test": "can-train-and-test (Lampe and Meng, 2024)",
                "real": "CIC-IoV2024 (Neto et al., 2024)"}

SUB_CARD = """# GraMa: `{profile}` on {dataset}

{what} of the `{profile}` profile, part of {paper}. {about}

The main card, one folder up, describes the model, the defence and the CIC-IoV2024 results; the code
is at https://github.com/RamadhanAdam/grama.

- {nodes} CAN IDs. Windows of {window} messages with stride {stride}; one sequence is {seq_len} windows.
- Classes: {classes}.
- Split: {split}.
- {setting}
- Hardware: {device}.

| Path | Contents |
|---|---|
{rows}

## Results

{results}
"""


# Which paper each profile belongs to (the folders on the main card).
PAPER_1 = {"full", "cic_seeds", "new_baselines", "def_ablation", "def_grid", "alie_duplicates", "clients40",
           "cic_adaptive", "cic_adaptive_new", "road", "road_new_baselines", "cantt1", "cantt1_adaptive",
           "cantt1_new_baselines"}
PAPER_NAME = {1: "paper 1 (the defence against poisoned updates)", 2: "paper 2 (the detector)"}


def paper_of(profile: str) -> str:
    return PAPER_NAME[1 if profile in PAPER_1 else 2]


def results_section(summary: str) -> str:
    """summary.md without its title, one heading level down, without references to the concept note."""
    lines = summary.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    text = "\n".join(lines).strip()
    text = re.sub(r"\s*\(Sec [^)]*\)", "", text)
    return re.sub(r"^(#{2,5}) ", r"#\1 ", text, flags=re.M)


def make_card(out: Path) -> str:
    dataset = json.loads((out / "dataset.json").read_text())
    profile = json.loads((out / "profile.json").read_text())
    sim = profile["simulation"]
    counts = dataset["class_counts"]
    runs = sum(1 for line in (out / "runs.jsonl").read_text().splitlines() if line.strip())
    return CARD.format(
        alpha=f"{profile['alpha']:g}",
        runs=runs,
        nodes=dataset["num_nodes"],
        feats=dataset["in_features"],
        window=dataset["window_size"],
        stride=dataset["stride"],
        seq_len=dataset["seq_len"],
        train=f"{sum(counts['train']):,}",
        test=f"{sum(counts['test']):,}",
        block_rows=f"{dataset.get('block_rows') or 1000:,}",
        clients=sim["num_clients"],
        per_round=sim["clients_per_round"],
        rounds=sim["num_rounds"],
        local_epochs=sim["local_epochs"],
        device=dataset["device"],
        classes=", ".join(dataset["class_names"]),
        results=results_section((out / "summary.md").read_text()),
    )


def make_sub_card(out: Path) -> str:
    """Card for a dataset other than the main one, uploaded into that dataset's folder."""
    dataset = json.loads((out / "dataset.json").read_text())
    profile = json.loads((out / "profile.json").read_text())
    sim = profile["simulation"]
    records = [json.loads(line) for line in (out / "runs.jsonl").read_text().splitlines() if line.strip()]
    runs = len(records)
    has_weights = any((out / "models").glob("*.pt"))
    if {r["aggregator"] for r in records} == {"central"}:
        setting = "Training: centralised, one model on all the training data."
    else:
        setting = (f"Federated setting: {sim['num_clients']} clients, {sim['clients_per_round']} per round, "
                   f"{sim['num_rounds']} rounds, {sim['local_epochs']} local epochs, Dirichlet alpha "
                   f"{profile['alpha']:g} unless a table says otherwise.")
    rows = ([f"| `models/` | weights of every run without an attack at Dirichlet alpha {profile['alpha']:g} |"]
            if has_weights else [])
    rows += ["| `summary.md` | all tables and figures; the same content is under Results below |",
             "| `tables/`, `figures/` | tables as CSV, figures as PNG and PDF |",
             f"| `runs.jsonl` | one record per training run ({runs} runs) |"]
    return SUB_CARD.format(
        what="Weights and results" if has_weights else "Results", rows="\n".join(rows),
        dataset=DATASET_NAME.get(dataset["source"], dataset["source"]),
        nodes=dataset["num_nodes"], window=dataset["window_size"], stride=dataset["stride"],
        seq_len=dataset["seq_len"], classes=", ".join(dataset["class_names"]),
        split=dataset.get("split_note", dataset.get("split", "")), setting=setting,
        profile=out.name, paper=paper_of(out.name), about=" ".join(str(profile.get("about", "")).split()),
        device=dataset["device"], runs=runs,
        results=results_section((out / "summary.md").read_text()),
    )


def files_to_upload(out: Path) -> list[tuple[str, Path]]:
    """(path in the repo, local file): everything in the results folder, plus config/*.yaml."""
    files = [(p.relative_to(out).as_posix(), p) for p in sorted(out.rglob("*"))
             if p.is_file() and not any(part.startswith(".") for part in p.relative_to(out).parts)]
    files += [(f"config/{p.name}", p) for p in sorted((ROOT / "config").glob("*.yaml"))]
    return files


def upload(out: Path, files: list[tuple[str, Path]], repo_id: str | None, private: bool) -> None:
    try:
        from huggingface_hub import CommitOperationAdd, HfApi
    except ImportError:
        sys.exit("huggingface_hub is not installed: pip install huggingface_hub")
    api = HfApi()
    if repo_id is None:
        try:
            repo_id = f"{api.whoami()['name']}/grama"
        except Exception:
            sys.exit("Not logged in to Hugging Face: run `huggingface-cli login` (or `hf auth login`)")
    api.create_repo(repo_id, repo_type="model", private=private, exist_ok=True)
    ops = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(path)) for name, path in files]
    api.create_commit(repo_id=repo_id, repo_type="model", operations=ops,
                      commit_message=f"Results and weights of the {out.name} profile")
    visibility = "private" if api.repo_info(repo_id).private else "public"
    print(f"Uploaded {len(ops)} files to https://huggingface.co/{repo_id} ({visibility})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default="full")
    parser.add_argument("--repo", default=None, help="user/name on the Hub (default: <your username>/grama)")
    parser.add_argument("--public", action="store_true", help="create the repo as public (default: private)")
    parser.add_argument("--dry-run", action="store_true", help="write the card and list the files, upload nothing")
    parser.add_argument("--path-in-repo", default="",
                        help="folder in the repo for this profile, e.g. road (default: the repo's top level)")
    parser.add_argument("--card-only", action="store_true", help="upload only the card (README.md)")
    args = parser.parse_args()

    out = ROOT / "results" / args.profile
    if not (out / "summary.md").exists():
        sys.exit(f"No results in {out}; run the profile first (make {args.profile})")
    prefix = args.path_in_repo.strip("/")
    (out / "README.md").write_text(make_sub_card(out) if prefix else make_card(out))
    files = [("README.md", out / "README.md")] if args.card_only else files_to_upload(out)
    if prefix:
        files = [(f"{prefix}/{name}", path) for name, path in files if not name.startswith("config/")]
    print(f"Wrote {out / 'README.md'}; {len(files)} files to upload")
    if args.dry_run:
        for name, _ in files:
            print("  " + name)
        return
    upload(out, files, args.repo, private=not args.public)


if __name__ == "__main__":
    main()
