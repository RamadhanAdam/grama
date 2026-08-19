"""Main federated training entrypoint.

Until CIC-IoV2024 is downloaded and wired through preprocess.py /
graph_builder.py, run with --synthetic to validate the full pipeline
(client sampling, local training, HDBSCAN aggregation, round loop) on
random data with the right shapes. This is how you sanity-check the
architecture end-to-end without the dataset.

Usage:
    python scripts/run_federated_train.py --synthetic --rounds 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.utils.data import Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from grama.data.federated_split import dirichlet_partition
from grama.federated.aggregator import LatentDensityAggregator
from grama.federated.client import LocalClient
from grama.federated.server import FederatedServer
from grama.models.classifier_head import GraMaLocalModel
from grama.utils.config import Config
from grama.utils.logging import get_logger
from grama.utils.seed import set_seed

logger = get_logger(__name__)


class SyntheticWindowSequenceDataset(Dataset):
    """Random (node_features, adjacency, label) tuples with real GraMa shapes,
    for pipeline validation before the actual dataset is available."""

    def __init__(self, num_samples: int, seq_len: int, num_nodes: int, in_features: int, num_classes: int, seed: int):
        g = torch.Generator().manual_seed(seed)
        self.node_features = torch.rand(num_samples, seq_len, num_nodes, in_features, generator=g)
        # Random symmetric adjacency with self-loops, mimicking graph_builder.py's output shape.
        adj = (torch.rand(num_samples, seq_len, num_nodes, num_nodes, generator=g) > 0.6).float()
        adj = torch.maximum(adj, adj.transpose(-1, -2))
        for i in range(num_nodes):
            adj[..., i, i] = 1.0
        self.adjacency = adj
        self.labels = torch.randint(0, num_classes, (num_samples,), generator=g)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.node_features[idx], self.adjacency[idx], self.labels[idx]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", help="Use random data to validate the pipeline")
    parser.add_argument("--rounds", type=int, default=None, help="Override config/federated.yaml num_rounds")
    parser.add_argument("--model-config", default="config/model.yaml")
    parser.add_argument("--federated-config", default="config/federated.yaml")
    parser.add_argument("--seq-len", type=int, default=8, help="Windows per sequence (synthetic mode only)")
    args = parser.parse_args()

    if not args.synthetic:
        logger.error("Real-data mode not wired yet — preprocessing depends on the actual CIC-IoV2024 "
                      "column layout (see src/grama/data/download.py). Run with --synthetic for now.")
        return 1

    model_cfg = Config.from_yaml(args.model_config)
    fed_cfg = Config.from_yaml(args.federated_config)
    set_seed(42)

    num_nodes = len(model_cfg.graph["ecu_nodes"])
    in_features = model_cfg.gat_encoder["in_features"]
    num_classes = model_cfg.classifier_head["num_classes"]
    num_clients = fed_cfg.simulation["num_clients"]

    logger.info("Building synthetic dataset: %d clients, %d ECU nodes, seq_len=%d", num_clients, num_nodes, args.seq_len)

    full_dataset = SyntheticWindowSequenceDataset(
        num_samples=num_clients * 40,
        seq_len=args.seq_len,
        num_nodes=num_nodes,
        in_features=in_features,
        num_classes=num_classes,
        seed=42,
    )

    client_indices = dirichlet_partition(
        labels=full_dataset.labels.numpy(),
        num_clients=num_clients,
        alpha=fed_cfg.simulation["non_iid_alpha"],
        seed=42,
    )

    def model_factory():
        return GraMaLocalModel(model_cfg.gat_encoder, model_cfg.mamba_block, model_cfg.classifier_head)

    clients = []
    for cid, idxs in enumerate(client_indices):
        if len(idxs) == 0:
            continue
        subset = torch.utils.data.Subset(full_dataset, idxs.tolist())
        clients.append(LocalClient(
            client_id=cid,
            dataset=subset,
            batch_size=fed_cfg.simulation["local_batch_size"],
            lr=fed_cfg.simulation["local_lr"],
        ))

    aggregator = LatentDensityAggregator(**fed_cfg.aggregator["hdbscan"] | {
        "latent_dim": fed_cfg.aggregator["latent_dim"],
        "autoencoder_hidden": fed_cfg.aggregator["autoencoder_hidden"],
        "autoencoder_epochs": fed_cfg.aggregator["autoencoder_epochs"],
    })

    server = FederatedServer(
        model_factory=model_factory,
        clients=clients,
        aggregator=aggregator,
        clients_per_round=fed_cfg.simulation["clients_per_round"],
        local_epochs=fed_cfg.simulation["local_epochs"],
    )

    num_rounds = args.rounds or fed_cfg.simulation["num_rounds"]
    logger.info("Starting federated training: %d rounds, %d/%d clients per round", num_rounds, server.clients_per_round, len(clients))
    history = server.run(num_rounds)

    for record in history:
        logger.info(
            "round %d done | avg_local_loss=%.4f | benign_cluster=%s | rejected=%d",
            record.round_num,
            record.avg_local_loss,
            record.aggregation.benign_cluster_id,
            sum(1 for w in record.aggregation.trust_weights.values() if w == 0.0),
        )

    logger.info("Done. This validated the pipeline end-to-end on synthetic data — swap in real CIC-IoV2024 tensors next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
