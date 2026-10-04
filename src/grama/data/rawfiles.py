"""Reading a dataset straight from its zip, or from the folder it was unpacked into.

ROAD (road.zip, 557 MB) and can-train-and-test (1.5 GB, 7.5 GB unpacked)
are read without unpacking: pandas reads each member from the zip. If the
files are unpacked as well, the folder is used, which is faster. Files are
named by their path inside the dataset (e.g. "road/attacks/fuzzing_attack_1.log"),
the same either way, so the processed file's name doesn't depend on which
one was read.

Also the hex parsing both datasets need: CAN IDs like "5E1" and payloads like
"893FE00B0A000080", which can be shorter than 8 bytes.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def _skip(parts) -> bool:
    return any(p.startswith(".") or p == "__MACOSX" for p in parts)


class RawFiles:
    """The files under root whose names end with one of `suffixes`, from a folder or a zip."""

    def __init__(self, root: str | Path, suffixes: tuple[str, ...]):
        self.root = Path(root)
        self.suffixes = tuple(s.lower() for s in suffixes)
        self._zip: Path | None = None
        self._files: dict[str, tuple[int, Path | None]] = {}
        if not self.root.exists():
            return
        for p in sorted(self.root.rglob("*")):
            rel = p.relative_to(self.root).parts
            if p.is_file() and p.name.lower().endswith(self.suffixes) and not _skip(rel):
                self._files["/".join(rel)] = (p.stat().st_size, p)
        if self._files:
            return
        for z in sorted(self.root.rglob("*.zip")):
            with zipfile.ZipFile(z) as zf:
                found = {i.filename: (i.file_size, None) for i in zf.infolist()
                         if i.filename.lower().endswith(self.suffixes) and not _skip(i.filename.split("/"))}
            if found:
                self._zip, self._files = z, found
                return

    @property
    def where(self) -> str:
        return str(self._zip) if self._zip else str(self.root)

    def names(self) -> list[str]:
        return sorted(self._files)

    def signature(self) -> list[tuple[str, int]]:
        """(name, size) of every file, for the processed file's hash."""
        return [(n, self._files[n][0]) for n in self.names()]

    def read_bytes(self, name: str) -> bytes:
        path = self._files[name][1]
        if path is not None:
            return path.read_bytes()
        with zipfile.ZipFile(self._zip) as zf:
            return zf.read(name)

    def open(self, name: str):
        """A binary file object (pandas reads it like a path)."""
        return io.BytesIO(self.read_bytes(name))


def hex_ids(values: pd.Series) -> np.ndarray:
    """'5E1' -> 0x5E1. Parses each distinct ID once."""
    codes, uniques = pd.factorize(values.astype(str).str.strip())
    table = np.array([int(u, 16) for u in uniques], dtype=np.int64)
    return table[codes]


def hex_payloads(values: pd.Series) -> np.ndarray:
    """'893FE00B' -> (n, 8) uint8, shorter payloads padded with zero bytes."""
    s = values.fillna("").astype(str).str.strip().str.slice(0, 16).str.ljust(16, "0")
    return np.frombuffer(bytes.fromhex("".join(s.tolist())), dtype=np.uint8).reshape(-1, 8).copy()
