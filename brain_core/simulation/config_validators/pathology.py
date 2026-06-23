"""Walidacja sekcji pathology konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_bool,
    require_list,
    require_mapping,
    require_non_empty_string,
)


def validate_pathology_config(pathology: dict[str, Any]) -> dict[str, Any]:
    """Waliduje konfigurację patologii i mutacji stanu symulacji.

    Parameters
    ----------
    pathology:
        Sekcja konfiguracji określająca włączenie patologii, scenariusz oraz
        listę mutacji stanu.

    Returns
    -------
    dict[str, Any]
        Znormalizowana sekcja ``pathology`` z listą zwalidowanych mutacji.

    Raises
    ------
    ConfigValidationError
        Gdy flaga ``enabled`` ma niepoprawny typ, mutacje nie są listą obiektów
        albo wymagane pola mutacji są puste.
    """
    if "enabled" not in pathology:
        raise ConfigValidationError("Brak pola pathology.enabled")
    pathology["enabled"] = require_bool(pathology["enabled"], "pathology.enabled")
    mutations = pathology.get("mutations", [])
    pathology["mutations"] = require_list(mutations, "pathology.mutations")
    scenario = pathology.get("scenario")
    if scenario is not None:
        pathology["scenario"] = require_non_empty_string(scenario, "pathology.scenario")
    for idx, mutation in enumerate(pathology["mutations"]):
        mutation_path = f"pathology.mutations[{idx}]"
        mutation_config = require_mapping(mutation, mutation_path)
        for required_key in ("kind", "scope", "target"):
            if required_key not in mutation_config:
                raise ConfigValidationError(f"Brak pola {mutation_path}.{required_key}")
            mutation_config[required_key] = require_non_empty_string(
                mutation_config[required_key], f"{mutation_path}.{required_key}"
            )
        pathology["mutations"][idx] = mutation_config
    return pathology
