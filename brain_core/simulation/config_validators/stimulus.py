"""Walidacja sekcji stimulus konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_non_empty_string,
)


def validate_stimulus_config(stimulus: dict[str, Any]) -> dict[str, Any]:
    """Waliduje wymaganą sekcję bodźców eksperymentalnych."""
    for text_field in ("scenario", "source"):
        if text_field not in stimulus:
            raise ConfigValidationError(f"Brak pola stimulus.{text_field}")
        stimulus[text_field] = require_non_empty_string(
            stimulus[text_field], f"stimulus.{text_field}"
        )
    return stimulus
