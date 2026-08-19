"""YAML config loading with a small dict->attribute convenience wrapper."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class Config(dict):
    """Dict subclass that also supports attribute access, recursively.

    Example:
        cfg = Config.from_yaml("config/model.yaml")
        cfg.gat_encoder.hidden_features  # same as cfg["gat_encoder"]["hidden_features"]
    """

    def __getattr__(self, key: str) -> Any:
        try:
            value = self[key]
        except KeyError as e:
            raise AttributeError(key) from e
        if isinstance(value, dict) and not isinstance(value, Config):
            value = Config(value)
            self[key] = value
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        path = Path(path)
        with path.open("r") as f:
            raw = yaml.safe_load(f) or {}
        return cls(raw)
