"""End to end on tiny synthetic data: build, train every kind of run, report."""
import json

from grama.experiments.report import make_report
from grama.experiments.runner import Experiment, RunSpec


def test_tiny_profile_end_to_end(tmp_path):
    exp = Experiment("smoke", device="cpu", results_dir=tmp_path / "results")
    exp.data_cfg["dataset"]["processed_dir"] = str(tmp_path / "processed")
    exp.profile["data_overrides"] = {"max_rows_per_class": None, "synthetic_rows_per_class": 1500}
    exp.sim.update(num_clients=4, clients_per_round=3, num_rounds=2, local_epochs=1)
    exp.prepare_data()

    specs = [
        RunSpec("grama", "hdbscan", 0.5, None, 0.0, 0),
        RunSpec("cnn_bigru", "fedavg", 0.5, None, 0.0, 0),
        RunSpec("grama", "krum", 0.5, "magnitude_poison", 0.25, 0),
        RunSpec("grama", "central", 0.5, None, 0.0, 0),
        RunSpec("grama", "fedavg", 0.5, None, 0.0, 0, "no_temporal"),
        RunSpec("grama", "central", 0.5, None, 0.0, 0, "one_head"),
        RunSpec("gcn_ids", "fedavg", 0.5, None, 0.0, 0),
        RunSpec("gcn_gru", "central", 0.5, None, 0.0, 0),
        RunSpec("transformer_ids", "fedavg", 0.5, None, 0.0, 0),
    ]
    with exp.runs_path.open("w") as f:
        for spec in specs:
            rec = exp.run_one(spec)
            assert rec["final"]["accuracy"] is not None
            assert len(rec["final"]["confusion_matrix"]) == 6
            f.write(json.dumps(rec) + "\n")
    assert exp.done_ids() == {s.run_id for s in specs}

    exp.efficiency()
    summary = make_report(exp.out_dir).read_text()
    assert "Main comparison" in summary and "Efficiency" in summary
    assert "Transformer" in summary and "GCN" in summary
    assert (exp.out_dir / "figures" / "convergence.png").exists()


def test_runs_on_another_dataset_build_are_not_resumed(tmp_path):
    exp = Experiment("smoke", device="cpu", results_dir=tmp_path / "results")
    exp.data_cfg["dataset"]["processed_dir"] = str(tmp_path / "processed")
    exp.profile["data_overrides"] = {"max_rows_per_class": None, "synthetic_rows_per_class": 1500}
    exp.prepare_data()
    old = {"run_id": "grama-fedavg-a0.5-clean-f0-s0", "data_file": "cic_iov2024_oldsplit.pt"}
    exp.runs_path.write_text(json.dumps(old) + "\n")
    assert exp.done_ids() == set()
