"""Walidacja sekcji integrator konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_mapping,
    require_non_empty_string,
)
from brain_core.simulation.integrators import INTEGRATOR_REGISTRY


def validate_integrator_config(integrator: dict[str, Any]) -> dict[str, Any]:
    """Waliduje parametry integratora numerycznego symulacji.

    Parameters
    ----------
    integrator:
        Sekcja konfiguracji opisująca metodę całkowania oraz opcjonalne
        parametry oscylatora.

    Returns:
    -------
    dict[str, Any]
        Znormalizowana sekcja ``integrator`` z obsługiwaną metodą numeryczną.

    Raises:
    ------
    ConfigValidationError
        Gdy brakuje pola ``method``, metoda nie jest obsługiwana albo
        opcjonalna sekcja oscylatora nie jest obiektem.
    """
    if "method" not in integrator:
        raise ConfigValidationError("Brak pola integrator.method")
    method = require_non_empty_string(integrator["method"], "integrator.method")
    registry_entry = INTEGRATOR_REGISTRY.get(method)
    if registry_entry is None:
        supported_methods = ", ".join(sorted(INTEGRATOR_REGISTRY))
        raise ConfigValidationError(
            "integrator.method musi wskazywać jedną z metod: " f"{supported_methods}"
        )

    missing_parameters = tuple(
        parameter
        for parameter in registry_entry.required_parameters
        if parameter not in integrator
    )
    if missing_parameters:
        missing_paths = ", ".join(
            f"integrator.{parameter}" for parameter in missing_parameters
        )
        raise ConfigValidationError(
            "Brak wymaganych parametrów dla integrator.method="
            f"{method}: {missing_paths}"
        )

    integrator["method"] = registry_entry.technical_name
    if "oscillator" in integrator:
        integrator["oscillator"] = require_mapping(
            integrator["oscillator"], "integrator.oscillator"
        )
    return integrator
