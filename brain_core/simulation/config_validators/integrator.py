"""Walidacja sekcji integrator konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_mapping,
    require_non_empty_string,
)


def validate_integrator_config(integrator: dict[str, Any]) -> dict[str, Any]:
    """Waliduje parametry integratora numerycznego symulacji.

    Parameters
    ----------
    integrator:
        Sekcja konfiguracji opisująca metodę całkowania oraz opcjonalne
        parametry oscylatora.

    Returns
    -------
    dict[str, Any]
        Znormalizowana sekcja ``integrator`` z obsługiwaną metodą numeryczną.

    Raises
    ------
    ConfigValidationError
        Gdy brakuje pola ``method``, metoda nie jest obsługiwana albo
        opcjonalna sekcja oscylatora nie jest obiektem.
    """
    if "method" not in integrator:
        raise ConfigValidationError("Brak pola integrator.method")
    method = require_non_empty_string(integrator["method"], "integrator.method")
    if method != "euler":
        raise ConfigValidationError("integrator.method aktualnie wspiera tylko 'euler'")
    integrator["method"] = method
    if "oscillator" in integrator:
        integrator["oscillator"] = require_mapping(
            integrator["oscillator"], "integrator.oscillator"
        )
    return integrator
