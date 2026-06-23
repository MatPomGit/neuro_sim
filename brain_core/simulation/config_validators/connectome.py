"""Walidacja sekcji connectome konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_non_empty_string,
)


def validate_connectome_config(connectome: dict[str, Any]) -> dict[str, Any]:
    """Waliduje sekcję atlasu i macierzy connectome.

    Parameters
    ----------
    connectome:
        Sekcja konfiguracji opisująca atlas oraz opcjonalne ścieżki wag i
        długości włókien.

    Returns
    -------
    dict[str, Any]
        Znormalizowana sekcja ``connectome`` z niepustymi wartościami tekstowymi.

    Raises
    ------
    ConfigValidationError
        Gdy brakuje nazwy atlasu albo pola tekstowe nie są niepustymi napisami.
    """
    if "atlas" not in connectome:
        raise ConfigValidationError("Brak pola connectome.atlas")
    connectome["atlas"] = require_non_empty_string(
        connectome["atlas"], "connectome.atlas"
    )
    for text_field in ("weights", "fiber_lengths"):
        if text_field in connectome and connectome[text_field] is not None:
            connectome[text_field] = require_non_empty_string(
                connectome[text_field], f"connectome.{text_field}"
            )
    return connectome
