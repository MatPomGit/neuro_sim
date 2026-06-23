"""Walidacja sekcji model konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.data_contracts import (
    CONTRACT_B_NETWORKS_POPULATIONS,
    validate_delay_steps_contract,
    validate_regional_vector_contract,
    validate_square_matrix_contract,
)
from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    coerce_string_tuple,
)


def validate_model_config(model: dict[str, Any]) -> dict[str, Any]:
    """Waliduje opcjonalne macierze regionalne modelu względem kontraktu B.

    Parameters
    ----------
    model:
        Sekcja modelu z opcjonalną listą regionów oraz polami macierzowymi.

    Returns
    -------
    dict[str, Any]
        Znormalizowana sekcja modelu po walidacji kontraktu danych.

    Raises
    ------
    ConfigValidationError
        Gdy lista regionów, konektywność, opóźnienia albo napędy regionalne
        mają kształt niezgodny z kontraktem danych.
    """
    if "regions" not in model:
        return model

    regions = coerce_string_tuple(model["regions"], "model.regions")
    if not regions:
        raise ConfigValidationError(
            "Kontrakt B: `networks` → `populations`: model.regions nie może być puste"
        )
    if len(set(regions)) != len(regions):
        raise ConfigValidationError(
            "Kontrakt B: `networks` → `populations`: model.regions musi być unikalne"
        )
    model["regions"] = list(regions)
    n_regions = len(regions)

    if "connectivity" in model:
        try:
            connectivity = validate_square_matrix_contract(
                model["connectivity"],
                n_regions,
                "model.connectivity",
                CONTRACT_B_NETWORKS_POPULATIONS,
            )
        except ValueError as error:
            raise ConfigValidationError(str(error)) from error
        model["connectivity"] = connectivity.tolist()

    if "delays_steps" in model:
        try:
            delays_steps = validate_delay_steps_contract(
                model["delays_steps"], n_regions
            )
        except ValueError as error:
            raise ConfigValidationError(str(error)) from error
        model["delays_steps"] = delays_steps.tolist()

    for vector_field in ("external_drive_E", "external_drive_I"):
        if vector_field in model:
            try:
                vector = validate_regional_vector_contract(
                    model[vector_field], n_regions, f"model.{vector_field}"
                )
            except ValueError as error:
                raise ConfigValidationError(str(error)) from error
            model[vector_field] = vector.tolist()
    return model
