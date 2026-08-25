import tempfile
from pathlib import Path

import torch
from torch.utils.data import Dataset

from grama.federated.aggregator import LatentDensityAggregator
from grama.federated.client import LocalClient
from grama.federated.server import FederatedServer


class TinyDataset(Dataset):
    """Minimal (node_features, adjacency, label) dataset matching GraMaLocalModel's
    expected shapes, small enough for a fast checkpoint round-trip test."""

    def __init__(self, n: int, num_nodes: int, in_features: int, num_classes: int, seed: int):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.rand(n, num_nodes, in_features, generator=g)
        adj = (torch.rand(n, num_nodes, num_nodes, generator=g) > 0.5).float()
        for i in range(num_nodes):
            adj[:, i, i] = 1.0
        self.adj = adj
        self.y = torch.randint(0, num_classes, (n,), generator=g)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.x[idx], self.adj[idx], self.y[idx]


class TinyModel(torch.nn.Module):
    """Stand-in local model: flattens node features and classifies, avoiding
    a dependency on the full GAT+Mamba stack for a checkpoint-mechanics test."""

    def __init__(self, num_nodes: int, in_features: int, num_classes: int):
        super().__init__()
        self.linear = torch.nn.Linear(num_nodes * in_features, num_classes)

    def forward(self, x, adjacency):
        return self.linear(x.flatten(start_dim=1))


def make_server(num_nodes=4, in_features=3, num_classes=2, num_clients=6):
    def model_factory():
        return TinyModel(num_nodes, in_features, num_classes)

    clients = [
        LocalClient(
            client_id=cid,
            dataset=TinyDataset(20, num_nodes, in_features, num_classes, seed=cid),
            batch_size=5,
            lr=1e-2,
        )
        for cid in range(num_clients)
    ]
    aggregator = LatentDensityAggregator(
        latent_dim=2, autoencoder_hidden=8, autoencoder_epochs=3,
        min_cluster_size=2, min_samples=1,
    )
    return FederatedServer(
        model_factory=model_factory,
        clients=clients,
        aggregator=aggregator,
        clients_per_round=3,
        local_epochs=1,
        seed=7,
    )


def test_checkpoint_round_trip_restores_weights_and_round_num():
    server = make_server()
    server.run(num_rounds=2)
    assert server.last_round_num == 2

    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "latest.pt")
        server.save_checkpoint(path)

        fresh = make_server()
        prior_summaries = fresh.load_checkpoint(path)

        assert fresh.last_round_num == 2
        assert len(prior_summaries) == 2
        for k, v in server.global_state.items():
            assert torch.allclose(v, fresh.global_state[k])


def test_resumed_run_continues_round_numbering_without_repeating():
    server = make_server()
    server.run(num_rounds=2)

    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "latest.pt")
        server.save_checkpoint(path)

        resumed = make_server()
        resumed.load_checkpoint(path)
        new_history = resumed.run(num_rounds=2)  # "2 additional rounds" after resume

        assert resumed.last_round_num == 4
        assert [r.round_num for r in new_history] == [3, 4]


def test_run_with_checkpoint_dir_writes_latest_and_history_log():
    server = make_server()
    with tempfile.TemporaryDirectory() as d:
        server.run(num_rounds=3, checkpoint_dir=d, checkpoint_every=2)

        assert (Path(d) / "latest.pt").exists()
        history_lines = (Path(d) / "history.jsonl").read_text().strip().splitlines()
        assert len(history_lines) == 3  # one line per round, regardless of checkpoint_every

        # latest.pt should reflect round 3 (the final round), even though
        # checkpoint_every=2 would otherwise only land on round 2.
        fresh = make_server()
        fresh.load_checkpoint(str(Path(d) / "latest.pt"))
        assert fresh.last_round_num == 3


def test_atomic_write_leaves_no_tmp_files_behind():
    server = make_server()
    server.run(num_rounds=1)
    with tempfile.TemporaryDirectory() as d:
        server.save_checkpoint(str(Path(d) / "latest.pt"))
        leftovers = [p for p in Path(d).iterdir() if p.name.startswith(".ckpt_tmp_")]
        assert leftovers == []
