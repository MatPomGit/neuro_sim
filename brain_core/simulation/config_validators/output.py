"""Walidacja sekcji output konfiguracji symulacji."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_bool,
    require_non_empty_string,
)


def validate_output_config(output: dict[str, Any]) -> dict[str, Any]:
    """Waliduje i normalizuje parametry zapisu artefaktów eksperymentu."""
    if "save_results" not in output:
        raise ConfigValidationError("Brak pola output.save_results")
    output["save_results"] = require_bool(output["save_results"], "output.save_results")
    if "label" not in output:
        raise ConfigValidationError("Brak pola output.label")
    output["label"] = require_non_empty_string(output["label"], "output.label")
    output_dir = output.get("output_dir", "outputs")
    output["output_dir"] = str(
        Path(require_non_empty_string(output_dir, "output.output_dir"))
    )
    return output
