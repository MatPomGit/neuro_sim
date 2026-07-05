"""Walidacja sekcji clinical_profile konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_non_empty_string,
    require_number,
)

ALLOWED_CLINICAL_PROFILE_IDS = {
    "healthy_v1",
    "dopamine_deficit",
    "gaba_dysregulation",
    "serotonin_imbalance",
    "hippocampal_lesion",
    "dlpfc_weakening",
}

ALLOWED_CLINICAL_PROFILE_KEYS = {
    "id",
    "display_name",
    "mechanism",
    "affected_regions",
    "cognitive_functions",
    "expected_effects",
    "expected_direction",
    "severity_level",
    "primary_metric",
    "tolerance",
    "applicability_scope",
    "benchmark_source",
    "amplitude_latency_mechanism",
}


def validate_amplitude_latency_mechanism_config(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Waliduje opis mechanizmu amplituda-latencja dla raportu roving oddball.

    Parameters
    ----------
    profile:
        Sekcja ``clinical_profile`` po podstawowej walidacji pól tekstowych.

    Returns:
    -------
    dict[str, Any]
        Znormalizowane metadane sekcji raportowej.

    Raises:
    ------
    ConfigValidationError
        Gdy sekcja ma niepoprawny typ, brakuje wymaganych pól albo próg nie
        jest dodatnią liczbą.
    """
    mechanism = profile.get("amplitude_latency_mechanism")
    if mechanism is None:
        mechanism = {
            "expected_amplitude_direction": profile.get(
                "expected_direction", "stable_reference"
            ),
            "expected_readaptation_direction": "stable_reference",
            "qualitative_threshold": 0.05,
            "mechanism_comment": profile.get("mechanism", "n/a"),
            "educational_comment": (
                "Brak dedykowanego opisu w konfiguracji; raport używa ogólnego "
                "mechanizmu profilu klinicznego."
            ),
        }
    if not isinstance(mechanism, dict):
        raise ConfigValidationError(
            "clinical_profile.amplitude_latency_mechanism musi być obiektem"
        )

    required_text_keys = (
        "expected_amplitude_direction",
        "expected_readaptation_direction",
        "mechanism_comment",
        "educational_comment",
    )
    normalized = dict(mechanism)
    for text_key in required_text_keys:
        if text_key not in normalized:
            raise ConfigValidationError(
                f"Brak pola clinical_profile.amplitude_latency_mechanism.{text_key}"
            )
        value = normalized[text_key]
        if not isinstance(value, str) or not value.strip():
            raise ConfigValidationError(
                f"clinical_profile.amplitude_latency_mechanism.{text_key} musi być tekstem"
            )
        normalized[text_key] = value.strip()

    if "qualitative_threshold" not in normalized:
        raise ConfigValidationError(
            "Brak pola clinical_profile.amplitude_latency_mechanism.qualitative_threshold"
        )
    normalized["qualitative_threshold"] = require_number(
        normalized["qualitative_threshold"],
        "clinical_profile.amplitude_latency_mechanism.qualitative_threshold",
    )
    if normalized["qualitative_threshold"] < 0.0:
        raise ConfigValidationError(
            "clinical_profile.amplitude_latency_mechanism.qualitative_threshold musi być >= 0"
        )
    return normalized


def validate_clinical_profile_config(
    clinical_profile: dict[str, Any], *, require_tolerance: bool = False
) -> dict[str, Any]:
    """Waliduje metadane profilu klinicznego ładowanego z konfiguracji."""
    profile_id = clinical_profile.get("id", "healthy_v1")
    if profile_id not in ALLOWED_CLINICAL_PROFILE_IDS:
        allowed = sorted(ALLOWED_CLINICAL_PROFILE_IDS)
        raise ConfigValidationError(
            f"Nieznany clinical_profile.id: {profile_id}. Dozwolone: {allowed}"
        )

    unknown_keys = sorted(
        key for key in clinical_profile if key not in ALLOWED_CLINICAL_PROFILE_KEYS
    )
    if unknown_keys:
        raise ConfigValidationError(f"Nieznane pola clinical_profile: {unknown_keys}")

    required_text_keys = ("display_name", "mechanism")
    optional_text_defaults = {
        "applicability_scope": "Brak jawnie opisanego zakresu zastosowania.",
        "benchmark_source": "Brak jawnie opisanego źródła benchmarku.",
    }
    for text_key in required_text_keys:
        if text_key not in clinical_profile:
            raise ConfigValidationError(f"Brak pola clinical_profile.{text_key}")
        value = clinical_profile[text_key]
        if not isinstance(value, str) or not value.strip():
            raise ConfigValidationError(f"clinical_profile.{text_key} musi być tekstem")

    for text_key, default_value in optional_text_defaults.items():
        value = clinical_profile.get(text_key, default_value)
        if not isinstance(value, str) or not value.strip():
            raise ConfigValidationError(f"clinical_profile.{text_key} musi być tekstem")
        clinical_profile[text_key] = value

    for list_key in ("affected_regions", "cognitive_functions"):
        value = clinical_profile.get(list_key, [])
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ConfigValidationError(
                f"clinical_profile.{list_key} musi być listą tekstów"
            )

    expected_effects = clinical_profile.get("expected_effects", {})
    if not isinstance(expected_effects, dict):
        raise ConfigValidationError(
            "clinical_profile.expected_effects musi być obiektem"
        )

    expected_direction = clinical_profile.get("expected_direction", "stable_reference")
    if not isinstance(expected_direction, str) or not expected_direction.strip():
        raise ConfigValidationError(
            "clinical_profile.expected_direction musi być tekstem"
        )

    primary_metric = clinical_profile.get("primary_metric", "mean_abs_difference")
    if primary_metric not in {"mean_abs_difference", "max_abs_difference"}:
        raise ConfigValidationError(
            "clinical_profile.primary_metric musi mieć wartość "
            "'mean_abs_difference' albo 'max_abs_difference'"
        )

    severity_level = clinical_profile.get(
        "severity_level", {"small": 0.0, "medium": 0.02, "large": 0.05}
    )
    if not isinstance(severity_level, dict):
        raise ConfigValidationError(
            "clinical_profile.severity_level musi być obiektem z progami"
        )
    for threshold_name in ("small", "medium", "large"):
        if threshold_name not in severity_level:
            raise ConfigValidationError(
                f"Brak progu clinical_profile.severity_level.{threshold_name}"
            )
        severity_level[threshold_name] = require_number(
            severity_level[threshold_name],
            f"clinical_profile.severity_level.{threshold_name}",
        )
    if not (
        severity_level["small"] <= severity_level["medium"] <= severity_level["large"]
    ):
        raise ConfigValidationError(
            "Progi clinical_profile.severity_level muszą spełniać small <= medium <= large"
        )

    if require_tolerance and "tolerance" not in clinical_profile:
        raise ConfigValidationError(
            "clinical_profile.tolerance musi być obiektem z polami absolute, relative i unit"
        )
    tolerance = clinical_profile.get(
        "tolerance",
        {"absolute": 0.005, "relative": 0.0, "unit": "mean_abs_difference"},
    )
    if not isinstance(tolerance, dict):
        raise ConfigValidationError(
            "clinical_profile.tolerance musi być obiektem z polami absolute, relative i unit"
        )
    for tolerance_key in ("absolute", "relative"):
        if tolerance_key not in tolerance:
            raise ConfigValidationError(
                f"Brak pola clinical_profile.tolerance.{tolerance_key}"
            )
        tolerance[tolerance_key] = require_number(
            tolerance[tolerance_key], f"clinical_profile.tolerance.{tolerance_key}"
        )
        if tolerance[tolerance_key] < 0.0:
            raise ConfigValidationError(
                f"clinical_profile.tolerance.{tolerance_key} musi być >= 0"
            )
    if "unit" not in tolerance:
        raise ConfigValidationError("Brak pola clinical_profile.tolerance.unit")
    tolerance["unit"] = require_non_empty_string(
        tolerance["unit"], "clinical_profile.tolerance.unit"
    )

    clinical_profile["id"] = str(profile_id)
    clinical_profile["display_name"] = clinical_profile["display_name"].strip()
    clinical_profile["mechanism"] = clinical_profile["mechanism"].strip()
    clinical_profile["applicability_scope"] = clinical_profile[
        "applicability_scope"
    ].strip()
    clinical_profile["benchmark_source"] = clinical_profile["benchmark_source"].strip()
    clinical_profile["affected_regions"] = list(
        clinical_profile.get("affected_regions", [])
    )
    clinical_profile["cognitive_functions"] = list(
        clinical_profile.get("cognitive_functions", [])
    )
    clinical_profile["expected_effects"] = dict(expected_effects)
    clinical_profile["expected_direction"] = expected_direction.strip()
    clinical_profile["primary_metric"] = str(primary_metric)
    clinical_profile["severity_level"] = dict(severity_level)
    clinical_profile["tolerance"] = dict(tolerance)
    clinical_profile["amplitude_latency_mechanism"] = (
        validate_amplitude_latency_mechanism_config(clinical_profile)
    )
    return clinical_profile
