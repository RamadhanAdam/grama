"""reuse_runs_from: a profile copies the runs it shares with another one instead of training them."""
import json

from grama.experiments.runner import Experiment, RunSpec

CLEAN = RunSpec("grama", "hdbscan", 0.5, None, 0.0, 0)


def setup(tmp_path, simulation=None, data_file=None):
    exp = Experiment("smoke", device="cpu", results_dir=tmp_path / "results" / "mine")
    exp.data_cfg["dataset"]["processed_dir"] = str(tmp_path / "processed")
    exp.profile["data_overrides"] = {"max_rows_per_class": None, "synthetic_rows_per_class": 1500}
    exp.profile["reuse_runs_from"] = ["other"]
    exp.prepare_data()
    src = tmp_path / "results" / "other"
    src.mkdir(parents=True)
    (src / "profile.json").write_text(json.dumps({"simulation": simulation or dict(exp.sim)}))
    rec = {"run_id": CLEAN.run_id, "data_file": data_file or exp.data_path.name, "final": {}}
    (src / "runs.jsonl").write_text(json.dumps(rec) + "\n")
    return exp


def test_shared_runs_are_copied_once(tmp_path):
    exp = setup(tmp_path)
    assert exp.reuse_runs([CLEAN]) == 1
    assert exp.done_ids() == {CLEAN.run_id}
    copied = json.loads(exp.runs_path.read_text())
    assert copied["copied_from"] == "other" and copied["profile"] == "smoke"
    assert exp.reuse_runs([CLEAN]) == 0       # already there


def test_runs_with_another_setting_or_data_file_are_not_copied(tmp_path):
    assert setup(tmp_path / "a", simulation={"num_clients": 99}).reuse_runs([CLEAN]) == 0
    assert setup(tmp_path / "b", data_file="cic_iov2024_other.pt").reuse_runs([CLEAN]) == 0
