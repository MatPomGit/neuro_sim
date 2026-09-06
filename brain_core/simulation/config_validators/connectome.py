"""Walidacja sekcji connectome konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_non_empty_string,
    require_positive_number,
)


def validate_connectome_config(connectome: dict[str, Any]) -> dict[str, Any]:
    """Waliduje sekcję atlasu, konektomu i parametrów propagacji.

    Parameters
    ----------
    connectome:
        Sekcja konfiguracji opisująca atlas, ścieżki wag i długości włókien oraz
        opcjonalną prędkość przewodzenia i wzmocnienie sprzężenia sieciowego.

    Returns
    -------
    dict[str, Any]
        Znormalizowana sekcja ``connectome``.

    Raises
    ------
    ConfigValidationError
        Gdy pola tekstowe są puste albo parametry propagacji nie są dodatnie.
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
    if "conduction_speed_m_s" in connectome:
        connectome["conduction_speed_m_s"] = require_positive_number(
            connectome["conduction_speed_m_s"],
            "connectome.conduction_speed_m_s",
        )
    if "coupling_gain" in connectome:
        connectome["coupling_gain"] = require_positive_number(
            connectome["coupling_gain"],
            "connectome.coupling_gain",
        )
    return connectome
