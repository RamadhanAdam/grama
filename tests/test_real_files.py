"""The real-data path on fake files laid out like the CIC-IoV2024 download."""
import zipfile

import numpy as np
import pandas as pd

from grama.data.build import build_dataset, find_csv_files, synthetic_streams, unpack_archives
from grama.data.download import check

CLASSES = ["benign", "DoS", "spoofing-GAS", "spoofing-RPM", "spoofing-SPEED", "spoofing-STEERING_WHEEL"]
FILE_NAMES = ["benign", "DoS", "spoofing-GAS", "spoofing-RPM", "spoofing-SPEED", "spoofing-STEERING_WHEEL"]


def _write_fake_release(raw, rows=900):
    """A zip with decimal/ and hexadecimal/ folders, like the CIC download."""
    streams = synthetic_streams(CLASSES, rows_per_class=rows, seed=3)
    zpath = raw / "CICIoV2024.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for s, name in zip(streams, FILE_NAMES):
            df = pd.DataFrame({"ID": s.ids, **{f"DATA_{i}": s.payload[:, i] for i in range(8)}})
            df["label"] = "BENIGN" if s.class_idx == 0 else "ATTACK"
            df["category"] = name.split("-")[0].upper()
            df["specific_class"] = name.split("-")[-1].upper()
            zf.writestr(f"CICIoV2024/decimal/decimal_{name}.csv", df.to_csv(index=False))
            hexdf = df.copy()
            hexdf["ID"] = [format(v, "x") for v in df["ID"]]
            zf.writestr(f"CICIoV2024/hexadecimal/hexadecimal_{name}.csv", hexdf.to_csv(index=False))
    return zpath


def test_zip_is_unpacked_and_only_decimal_files_are_used(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_fake_release(raw)
    unpack_archives(raw)
    files = find_csv_files(raw)
    assert len(files) == 6
    assert all("decimal_" in f.name and "hexadecimal" not in f.name for f in files)
    assert check(raw, CLASSES, verbose=False)


def test_build_from_fake_release(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_fake_release(raw)
    cfg = {
        "dataset": {"raw_dir": str(raw), "processed_dir": str(tmp_path / "processed")},
        "classes": CLASSES,
        "build": dict(window_size=16, stride=8, seq_len=4, seq_stride=2, test_fraction=0.2, max_nodes=64,
                      edge_mode="transition", min_attack_frames=1, max_rows_per_class={"benign": 600},
                      injection={"enabled": True, "attack_ratio": 0.3}),
    }
    path = build_dataset(cfg, source="real")
    assert path.exists() and path.name.startswith("cic_iov2024_")
    assert build_dataset(cfg, source="real") == path        # second call reuses the file

    import torch
    payload = torch.load(path, weights_only=False)
    counts = np.array(payload["meta"]["class_counts"]["train"])
    assert (counts > 0).all()
    assert payload["meta"]["injection"]["attack_ratio"] == 0.3


def test_check_explains_missing_data(tmp_path, capsys):
    assert not check(tmp_path / "raw", CLASSES)
    assert "iov-dataset-2024" in capsys.readouterr().out
