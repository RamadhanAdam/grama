"""Runs the experiments of a profile (config/experiments.yaml) and saves every run.

    from grama.experiments.runner import Experiment
    exp = Experiment("quick")
    exp.prepare_data()
    exp.run_all()        # skips runs already in results/quick/runs.jsonl
    exp.efficiency()

Four experiment groups, the first three matching Sec 6.2 of the concept note:
  main       clean training: GraMa vs the CNN-BiGRU baseline, HDBSCAN vs
             FedAvg, plus centralised training as an upper bound (6.2.1)
  noniid     GraMa under different Dirichlet alphas (6.2.2)
  poisoning  attack x share of compromised clients x aggregation rule (6.2.3)
  ablation   GraMa with one part removed or swapped at a time
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch

from grama.attacks.poisoning import select_compromised_clients
from grama.data.build import build_dataset
from grama.data.dataset import dataset_from_payload, load_processed
from grama.data.federated_split import client_label_distribution, dirichlet_partition
from grama.eval.latency_bench import benchmark_inference, count_parameters, model_size_kb, throughput
from grama.eval.metrics import evaluate
from grama.federated.client import LocalClient
from grama.federated.robust import FedAvgAggregator, make_aggregator
from grama.federated.server import FederatedServer
from grama.models.baseline import CNNBiGRUBaseline
from grama.models.classifier_head import GraMaLocalModel
from grama.utils.config import Config
from grama.utils.device import describe_device, pick_device
from grama.utils.logging import get_logger
from grama.utils.seed import set_seed

logger = get_logger("grama.experiments")

MODELS = {"grama": "graph", "cnn_bigru": "frames"}   # model -> dataset view

# Ablation variants: what each one changes in config/model.yaml, or the edge type.
VARIANTS = {
    "no_residual": {"gat_encoder": {"residual": False}},
    "no_id_embedding": {"gat_encoder": {"node_embedding_dim": 0}},
    "mean_pool": {"gat_encoder": {"pooling": "mean"}},
    "cooccurrence_edges": {"edge_mode": "cooccurrence"},
    "transition_edges": {"edge_mode": "transition"},
    "gru_instead_of_mamba": {"mamba_block": {"temporal": "gru"}},
    "no_temporal": {"mamba_block": {"temporal": "none"}},
}
SCALAR_KEYS = ("accuracy", "precision_macro", "recall_macro", "f1_macro", "roc_auc",
               "detection_rate", "false_alarm_rate")


@dataclass(frozen=True)
class RunSpec:
    model: str             # grama | cnn_bigru
    aggregator: str        # hdbscan | fedavg | median | trimmed_mean | krum | central
    alpha: float
    attack: str | None
    fraction: float
    seed: int
    variant: str = ""      # ablation variant, "" = the full model

    @property
    def run_id(self) -> str:
        base = (f"{self.model}-{self.aggregator}-a{self.alpha:g}-"
                f"{self.attack or 'clean'}-f{self.fraction:g}-s{self.seed}")
        return f"{base}-{self.variant}" if self.variant else base


def parse_method(method: str) -> tuple[str, str]:
    for model in sorted(MODELS, key=len, reverse=True):
        if method.startswith(model + "_"):
            return model, method[len(model) + 1:]
    raise ValueError(f"Can't read method {method!r}; expected <model>_<aggregator>, model in {list(MODELS)}")


def _clean(v):
    """Make a value JSON-safe (NaN -> None)."""
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


class Experiment:
    def __init__(self, profile: str, root: str | Path = ".", device: str | None = None,
                 results_dir: str | Path | None = None):
        self.root = Path(root)
        cfg_dir = self.root / "config"
        self.data_cfg = Config.from_yaml(cfg_dir / "data.yaml")
        self.model_cfg = Config.from_yaml(cfg_dir / "model.yaml")
        self.fed_cfg = Config.from_yaml(cfg_dir / "federated.yaml")
        profiles = Config.from_yaml(cfg_dir / "experiments.yaml")["profiles"]
        if profile not in profiles:
            raise KeyError(f"Unknown profile {profile!r}; choose from {list(profiles)}")
        self.profile_name = profile
        self.profile = profiles[profile]
        self.sim = {**self.fed_cfg["simulation"], **self.profile.get("federated", {})}
        self.device = device or pick_device()
        self.out_dir = Path(results_dir) if results_dir else self.root / "results" / profile
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "models").mkdir(exist_ok=True)
        self.runs_path = self.out_dir / "runs.jsonl"
        self.meta = None
        self._write_profile()

    def _write_profile(self) -> None:
        """Settings the report needs, next to the results."""
        p = self.profile
        info = {
            "profile": self.profile_name,
            "about": p.get("about", ""),
            "alpha": float(self.sim["non_iid_alpha"]),
            "simulation": dict(self.sim),
            "main_methods": [list(parse_method(m)) for m in p.get("main", {}).get("methods", [])],
            "noniid": dict(p["noniid"]) if "noniid" in p else None,
            "poisoning": dict(p["poisoning"]) if "poisoning" in p else None,
            "ablation": dict(p["ablation"]) if "ablation" in p else None,
            "edge_mode": self.data_cfg["build"]["edge_mode"],
        }
        (self.out_dir / "profile.json").write_text(json.dumps(info, indent=2))

    # ------------------------------------------------------------------ data

    def prepare_data(self, force: bool = False) -> Path:
        """Build (or reuse) the processed dataset for this profile and load it."""
        data_cfg = dict(self.data_cfg)
        data_cfg["dataset"] = dict(data_cfg["dataset"])
        for key in ("raw_dir", "processed_dir"):
            data_cfg["dataset"][key] = str(self.root / data_cfg["dataset"][key])
        for source in ("road", "can_train_test"):
            if source in data_cfg:
                data_cfg[source] = {**data_cfg[source], "raw_dir": str(self.root / data_cfg[source]["raw_dir"])}
        path = build_dataset(data_cfg, source=self.profile["data"],
                             overrides=self.profile.get("data_overrides") or {}, force=force)
        payload = load_processed(path)
        self.meta = payload["meta"]
        self.data_path = path
        self.train, self.test = {}, {}
        # Extra test sets (ROAD's masquerade set, can-train-and-test's unknown car and attacks).
        self.extra = {name: {} for name in self.meta.get("extra_tests", [])}
        for model, view in MODELS.items():
            self.train[model] = dataset_from_payload(payload, "train", view=view)
            self.test[model] = dataset_from_payload(payload, "test", view=view)
            for name in self.extra:
                self.extra[name][model] = dataset_from_payload(payload, name, view=view)
            if self.device.startswith("cuda"):
                for ds in (self.train[model], self.test[model], *(e[model] for e in self.extra.values())):
                    ds.to(self.device)
        info = {
            "profile": self.profile_name,
            "data_file": path.name,
            "device": describe_device(self.device),
            **{k: self.meta[k] for k in ("source", "class_names", "num_nodes", "in_features",
                                          "window_size", "stride", "seq_len", "seq_stride",
                                          "edge_mode", "class_counts", "injection")},
            "split": self.meta.get("split", "temporal"),
            "block_rows": self.meta.get("block_rows"),
            **{k: self.meta[k] for k in ("extra_tests", "split_note", "other_node_share") if k in self.meta},
        }
        (self.out_dir / "dataset.json").write_text(json.dumps(info, indent=2))
        logger.info("Data: %s | %d nodes | train %d / test %d sequences | device %s",
                    path.name, self.meta["num_nodes"], len(self.train["grama"]),
                    len(self.test["grama"]), info["device"])
        return path

    # ------------------------------------------------------------------ models

    def model_factory(self, model: str, mamba_backend: str | None = None, variant: str = ""):
        meta, cfg = self.meta, self.model_cfg
        if model == "grama":
            change = VARIANTS.get(variant, {}) if variant else {}
            if variant and variant not in VARIANTS:
                raise ValueError(f"Unknown variant {variant!r}; choose from {list(VARIANTS)}")
            gat = {**cfg["gat_encoder"], "in_features": meta["in_features"], **change.get("gat_encoder", {})}
            mamba = {**cfg["mamba_block"], **change.get("mamba_block", {}),
                     **({"backend": mamba_backend} if mamba_backend else {})}
            head = {**cfg["classifier_head"], "num_classes": meta["num_classes"]}
            return lambda: GraMaLocalModel(gat, mamba, head, num_nodes=meta["num_nodes"])
        if model == "cnn_bigru":
            b = dict(cfg.get("baseline", {}))
            return lambda: CNNBiGRUBaseline(meta["num_nodes"], meta["num_classes"], **b)
        raise ValueError(f"Unknown model {model!r}")

    # ------------------------------------------------------------------ plan

    def plan(self, only: list[str] | None = None) -> list[RunSpec]:
        """All runs of the profile, without duplicates (main runs double as alpha/attack baselines)."""
        p, alpha0 = self.profile, float(self.sim["non_iid_alpha"])
        seeds = p.get("seeds", [0])
        specs: list[RunSpec] = []

        def add(spec):
            if spec not in specs:
                specs.append(spec)

        groups = only or ["main", "noniid", "poisoning", "ablation"]
        if "main" in groups and "main" in p:
            for seed in p["main"].get("seeds", seeds):
                for method in p["main"]["methods"]:
                    model, agg = parse_method(method)
                    add(RunSpec(model, agg, alpha0, None, 0.0, seed))
        if "noniid" in groups and "noniid" in p:
            for seed in p["noniid"].get("seeds", seeds):
                for agg in p["noniid"]["aggregators"]:
                    for alpha in p["noniid"]["alphas"]:
                        add(RunSpec("grama", agg, float(alpha), None, 0.0, seed))
        if "poisoning" in groups and "poisoning" in p:
            for seed in p["poisoning"].get("seeds", seeds):
                for agg in p["poisoning"]["aggregators"]:
                    add(RunSpec("grama", agg, alpha0, None, 0.0, seed))  # 0% compromised reference
                    for attack in p["poisoning"]["attacks"]:
                        for frac in p["poisoning"]["fractions"]:
                            add(RunSpec("grama", agg, alpha0, attack, float(frac), seed))
        if "ablation" in groups and "ablation" in p:
            agg = p["ablation"].get("aggregator", "fedavg")
            for seed in p["ablation"].get("seeds", seeds):
                add(RunSpec("grama", agg, alpha0, None, 0.0, seed))  # the full model
                for variant in p["ablation"]["variants"]:
                    add(RunSpec("grama", agg, alpha0, None, 0.0, seed, variant))
        return specs

    def done_ids(self) -> set[str]:
        """Runs already finished on the current dataset file (runs on an older build don't count)."""
        if not self.runs_path.exists():
            return set()
        current = self.data_path.name if self.meta is not None else None
        ids = set()
        for line in self.runs_path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                if current is None or rec.get("data_file") == current:
                    ids.add(rec["run_id"])
        return ids

    # ------------------------------------------------------------------ one run

    def class_weights(self) -> torch.Tensor | None:
        if self.sim.get("class_weighting", "none") != "balanced":
            return None
        counts = torch.bincount(self.train["grama"].labels.cpu(), minlength=self.meta["num_classes"]).float()
        w = counts.sum() / (len(counts) * counts.clamp(min=1))
        return w / w.mean()

    def run_one(self, spec: RunSpec) -> dict:
        if self.meta is None:
            self.prepare_data()
        set_seed(spec.seed)
        sim, C = self.sim, self.meta["num_classes"]
        train_ds, test_ds = self.train[spec.model], self.test[spec.model]
        edge_mode = VARIANTS.get(spec.variant, {}).get("edge_mode")
        if edge_mode and spec.model == "grama":
            train_ds, test_ds = train_ds.with_view(edge_mode=edge_mode), test_ds.with_view(edge_mode=edge_mode)
        labels = train_ds.labels.cpu().numpy()
        central = spec.aggregator == "central"

        if central:
            parts = [np.arange(len(labels))]
        else:
            parts = dirichlet_partition(labels, sim["num_clients"], spec.alpha, seed=spec.seed)
        client_ids = [cid for cid, idx in enumerate(parts) if len(idx) > 0]
        compromised = (select_compromised_clients(client_ids, spec.fraction, seed=spec.seed)
                       if spec.attack else set())

        weights = self.class_weights()
        clients = [
            LocalClient(
                client_id=cid, dataset=train_ds, indices=parts[cid],
                batch_size=sim["local_batch_size"], lr=sim["local_lr"], device=self.device,
                attack=spec.attack if cid in compromised else None, num_classes=C,
                poison_scale=self.fed_cfg["adversarial_eval"]["magnitude_poison_scale"],
                class_weights=weights, seed=spec.seed,
            )
            for cid in client_ids
        ]

        factory = self.model_factory(spec.model, variant=spec.variant)
        eval_batch = 1024 if self.device.startswith("cuda") else 256

        def eval_fn(state):
            model = factory()
            model.load_state_dict(state)
            m = evaluate(model, test_ds, C, self.device, eval_batch)
            return {k: m.get(k) for k in SCALAR_KEYS}

        if central:
            aggregator = FedAvgAggregator()
            # Same number of passes over the data as the federated runs get.
            rounds = max(1, round(sim["num_rounds"] * sim["local_epochs"] * sim["clients_per_round"]
                                  / sim["num_clients"]))
            per_round, local_epochs = 1, 1
            eval_every = max(1, rounds // 10)
        else:
            aggregator = make_aggregator(spec.aggregator, self.fed_cfg, self.device, seed=spec.seed)
            if spec.aggregator == "hdbscan" and sim["clients_per_round"] < 5:
                logger.warning("HDBSCAN with %d clients per round often finds no cluster at all; "
                               "use 5 or more.", sim["clients_per_round"])
            rounds, per_round, local_epochs = sim["num_rounds"], sim["clients_per_round"], sim["local_epochs"]
            eval_every = self.profile.get("eval_every", 1)

        adv = self.fed_cfg["adversarial_eval"]
        server = FederatedServer(
            model_factory=factory, clients=clients, aggregator=aggregator,
            clients_per_round=per_round, local_epochs=local_epochs, seed=spec.seed,
            eval_fn=eval_fn, eval_every=eval_every,
            adaptive_max_scale=adv.get("adaptive_max_scale", 10.0),
            adaptive_steps=adv.get("adaptive_search_steps", 7),
        )
        start = time.perf_counter()
        history = server.run(rounds)
        train_seconds = time.perf_counter() - start

        model = factory()
        model.load_state_dict(server.global_state)
        final = evaluate(model, test_ds, C, self.device, eval_batch, detailed=True)
        tests = {}
        for name, views in self.extra.items():
            ds = views[spec.model]
            if edge_mode and spec.model == "grama":
                ds = ds.with_view(edge_mode=edge_mode)
            tests[name] = evaluate(model, ds, C, self.device, eval_batch, detailed=True, present_only=True)

        if spec.attack is None and not spec.variant and spec.alpha == float(self.sim["non_iid_alpha"]):
            torch.save(server.global_state, self.out_dir / "models" / f"{spec.run_id}.pt")

        record = {
            "run_id": spec.run_id,
            **asdict(spec),
            "profile": self.profile_name,
            "data_source": self.meta["source"],
            "data_file": self.data_path.name,
            "num_clients": len(client_ids),
            "compromised": sorted(compromised),
            "rounds": rounds,
            "params": count_parameters(model),
            "train_seconds": train_seconds,
            "final": final,
            **({"tests": tests} if tests else {}),
            "defence": self._defence_stats(history, aggregator),
            "history": [
                {"round": h.round_num, "loss": h.avg_local_loss, "seconds": h.seconds,
                 "num_rejected": len(h.rejected_clients), "num_malicious": len(h.malicious_clients),
                 **({"attack_scale": h.attack_scale} if h.attack_scale is not None else {}),
                 **(h.metrics or {})}
                for h in history
            ],
            "client_label_counts": client_label_distribution(labels, parts).tolist(),
        }
        return _clean(record)

    @staticmethod
    def _defence_stats(history, aggregator) -> dict:
        """How well the rule told compromised clients apart, over all rounds."""
        tp = fp = tn = fn = 0
        no_cluster = 0
        for h in history:
            mal, rej = set(h.malicious_clients), set(h.rejected_clients)
            honest = set(h.participating_clients) - mal
            tp += len(mal & rej)
            fn += len(mal - rej)
            fp += len(honest & rej)
            tn += len(honest - rej)
            if getattr(h.aggregation, "benign_cluster_id", 0) is None and aggregator.name == "hdbscan":
                no_cluster += 1
        detects = getattr(aggregator, "detects_clients", False)
        return {
            "detects_clients": detects,
            "tpr": tp / (tp + fn) if detects and (tp + fn) else None,
            "fpr": fp / (fp + tn) if detects and (fp + tn) else None,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "rounds_without_cluster": no_cluster,
        }

    # ------------------------------------------------------------------ all runs

    def run_all(self, only: list[str] | None = None, progress: bool = True) -> list[dict]:
        if self.meta is None:
            self.prepare_data()
        specs = self.plan(only)
        done = self.done_ids()
        todo = [s for s in specs if s.run_id not in done]
        logger.info("Profile %s: %d runs planned, %d already done, %d to go",
                    self.profile_name, len(specs), len(specs) - len(todo), len(todo))
        bar = None
        if progress:
            try:
                import ipywidgets  # noqa: F401  (tqdm.auto needs it for the notebook bar)
                from tqdm.auto import tqdm
            except ImportError:
                from tqdm import tqdm
            bar = tqdm(total=len(todo), desc=f"{self.profile_name} runs", unit="run")
        results = []
        for spec in todo:
            record = self.run_one(spec)
            with self.runs_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
            results.append(record)
            fin = record["final"]
            logger.info("%-48s acc %.4f  macro-F1 %.4f  (%.0fs)", spec.run_id,
                        fin["accuracy"], fin["f1_macro"], record["train_seconds"])
            if bar:
                bar.update(1)
        if bar:
            bar.close()
        return results

    # ------------------------------------------------------------------ efficiency

    def efficiency(self) -> dict:
        """Parameters, size, latency and throughput of GraMa and the baseline (Sec 6.1, 8.1)."""
        if self.meta is None:
            self.prepare_data()
        out = {}
        for model_name, label in (("grama", "GraMa"), ("cnn_bigru", "CNN-BiGRU")):
            ds = self.test[model_name]
            one = tuple(t.cpu() for t in ds.get_batch(torch.tensor([0]))[:-1])
            n = min(256, len(ds))
            batch = tuple(t.cpu() for t in ds.get_batch(torch.arange(n))[:-1])

            cpu_model = self.model_factory(model_name, mamba_backend="torch")()
            threads = torch.get_num_threads()
            torch.set_num_threads(1)
            try:
                cpu_lat = benchmark_inference(cpu_model, one, device="cpu", num_runs=30)
            finally:
                torch.set_num_threads(threads)
            entry = {
                "params": count_parameters(cpu_model),
                "size_kb": model_size_kb(cpu_model),
                "upload_per_round_kb": model_size_kb(cpu_model),   # one Δw per client per round
                "cpu_1thread_ms_per_sequence": cpu_lat.mean_ms_per_sequence,
                "cpu_1thread_p95_ms": cpu_lat.p95_ms_per_sequence,
                "sequence_covers_frames": self.meta["window_size"] + (self.meta["seq_len"] - 1) * self.meta["stride"],
            }
            if self.device.startswith("cuda"):
                gpu_model = self.model_factory(model_name)()
                gpu_lat = benchmark_inference(gpu_model, one, device=self.device)
                entry["gpu_ms_per_sequence"] = gpu_lat.mean_ms_per_sequence
                entry["gpu_peak_memory_mb"] = gpu_lat.peak_memory_mb
                entry["gpu_sequences_per_second"] = throughput(gpu_model, batch, device=self.device)
            else:
                entry["cpu_sequences_per_second"] = throughput(cpu_model, batch, device="cpu")
            out[label] = entry
        (self.out_dir / "efficiency.json").write_text(json.dumps(_clean(out), indent=2))
        return out
