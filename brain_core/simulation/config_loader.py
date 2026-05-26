from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from .config_schema import ExperimentConfig, validate_config


def _parse_payload(payload: str, suffix: str = "") -> Dict[str, Any]:
    if suffix.lower() == ".json":
        return json.loads(payload)
    try:
        return yaml.safe_load(payload)
    except Exception:
        return json.loads(payload)


def load_config(path: str | Path) -> ExperimentConfig:
    p = Path(path)
    raw = _parse_payload(p.read_text(encoding="utf-8"), suffix=p.suffix)
    return validate_config(raw)


def load_config_from_string(payload: str, format_hint: str = "yaml") -> ExperimentConfig:
    suffix = ".json" if format_hint.lower() == "json" else ".yaml"
    raw = _parse_payload(payload, suffix=suffix)
    return validate_config(raw)
