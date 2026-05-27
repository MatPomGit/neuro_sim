from __future__ import annotations

"""Ładowanie i walidacja konfiguracji eksperymentów symulacyjnych."""

import json
from pathlib import Path
from typing import Any

import yaml

from .config_schema import ExperimentConfig, validate_config


def _parse_payload(payload: str, suffix: str = "") -> dict[str, Any]:
    """Parsuje payload konfiguracji YAML/JSON do słownika Python.

    Najpierw preferowany jest parser zgodny z rozszerzeniem pliku, a przy
    niepowodzeniu używany jest bezpieczny fallback.
    """
    if suffix.lower() == ".json":
        return json.loads(payload)
    try:
        parsed = yaml.safe_load(payload)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return json.loads(payload)


def load_config(path: str | Path) -> ExperimentConfig:
    """Wczytuje konfigurację z pliku i zwraca obiekt po walidacji."""
    config_path = Path(path)
    raw_config = _parse_payload(config_path.read_text(encoding="utf-8"), suffix=config_path.suffix)
    return validate_config(raw_config)


def load_config_from_string(payload: str, format_hint: str = "yaml") -> ExperimentConfig:
    """Wczytuje konfigurację z tekstu i zwraca obiekt po walidacji."""
    suffix = ".json" if format_hint.lower() == "json" else ".yaml"
    raw_config = _parse_payload(payload, suffix=suffix)
    return validate_config(raw_config)
