"""Walidacja sekcji brain_profile konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_non_empty_string,
)


def validate_brain_profile_config(brain_profile: dict[str, Any]) -> dict[str, Any]:
    """Waliduje bazowy profil mózgu niezależny od profilu klinicznego.

    Parameters
    ----------
    brain_profile:
        Sekcja konfiguracji identyfikująca bazowy profil mózgu i opcjonalny
        opis metadanych.

    Returns:
    -------
    dict[str, Any]
        Znormalizowana sekcja ``brain_profile`` z niepustym identyfikatorem.

    Raises:
    ------
    ConfigValidationError
        Gdy brakuje pola ``id`` albo wartości tekstowe są puste lub mają
        niepoprawny typ.
    """
    if "id" not in brain_profile:
        raise ConfigValidationError("Brak pola brain_profile.id")
    brain_profile["id"] = require_non_empty_string(
        brain_profile["id"], "brain_profile.id"
    )
    if "description" in brain_profile:
        brain_profile["description"] = require_non_empty_string(
            brain_profile["description"], "brain_profile.description"
        )
    return brain_profile
