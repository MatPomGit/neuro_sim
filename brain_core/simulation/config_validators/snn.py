"""Walidacja sekcji snn konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    coerce_string_tuple,
    require_bool,
    require_list,
    require_positive_number,
)
from brain_core.simulation.signal_adapter import (
    ALLOWED_SNN_COUPLING_MODES,
    DEMO_SNN_REGION_NAME,
    SNNPopulationMapping,
)
from brain_core.simulation.timebase import is_time_multiple


def validate_snn_config(snn: dict[str, Any], timestep: float) -> dict[str, Any]:
    """Waliduje sekcję konfiguracji współsymulacji SNN.

    Parameters
    ----------
    snn:
        Sekcja konfiguracji opisująca obwody SNN i parametry synchronizacji.
    timestep:
        Krok czasowy symulacji neural-mass w sekundach, używany jako domyślne
        ``sync_dt`` i baza sprawdzenia wielokrotności.

    Returns:
    -------
    dict[str, Any]
        Znormalizowana sekcja ``snn`` gotowa do użycia przez silnik symulacji.

    Raises:
    ------
    ConfigValidationError
        Gdy typy pól, nazwy obwodów, tryb sprzężenia albo jednostki naruszają
        obsługiwany kontrakt pilotażu SNN.
    """
    if "enabled" not in snn:
        raise ConfigValidationError("Brak pola snn.enabled")
    snn["enabled"] = require_bool(snn["enabled"], "snn.enabled")
    circuits = require_list(snn.get("circuits", []), "snn.circuits")

    circuit_regions: list[str] = []
    for idx, circuit in enumerate(circuits):
        if not isinstance(circuit, dict):
            raise ConfigValidationError(f"snn.circuits[{idx}] musi być obiektem")
        region = circuit.get("region")
        if not isinstance(region, str) or not region.strip():
            raise ConfigValidationError(f"Brak pola snn.circuits[{idx}].region")
        circuit["region"] = region.strip()
        circuit_regions.append(circuit["region"])

    if len(circuit_regions) != len(set(circuit_regions)):
        raise ConfigValidationError("snn.circuits.region musi zawierać unikalne nazwy")
    if circuit_regions and circuit_regions != [DEMO_SNN_REGION_NAME]:
        raise ConfigValidationError(
            "Bieżący pilotaż SNN obsługuje dokładnie jeden obwód "
            f"demonstracyjny: {DEMO_SNN_REGION_NAME}"
        )
    for idx, circuit in enumerate(circuits):
        backend = str(circuit.get("backend", "brian2"))
        if backend != "brian2":
            raise ConfigValidationError(
                f"snn.circuits[{idx}].backend musi mieć wartość 'brian2' w bieżącym pilotażu"
            )
        circuit["backend"] = backend

    sync_dt_val = snn.get("sync_dt")
    sync_dt = (
        timestep
        if sync_dt_val is None
        else require_positive_number(sync_dt_val, "snn.sync_dt")
    )

    if not is_time_multiple(sync_dt, timestep):
        raise ConfigValidationError("snn.sync_dt musi być wielokrotnością timestep")

    coupling_mode = str(snn.get("mode", "report_only"))
    if coupling_mode not in ALLOWED_SNN_COUPLING_MODES:
        allowed_modes = ", ".join(ALLOWED_SNN_COUPLING_MODES)
        raise ConfigValidationError(
            f"snn.mode musi mieć jedną z wartości: {allowed_modes}"
        )

    max_feedback_amplitude = require_positive_number(
        snn.get("max_feedback_amplitude", 0.15), "snn.max_feedback_amplitude"
    )

    input_rate_unit = str(snn.get("input_rate_unit", "Hz"))
    output_activity_unit = str(snn.get("output_activity_unit", "fraction"))
    if input_rate_unit != "Hz":
        raise ConfigValidationError("snn.input_rate_unit musi mieć wartość 'Hz'")
    if output_activity_unit != "fraction":
        raise ConfigValidationError(
            "snn.output_activity_unit musi mieć wartość 'fraction'"
        )

    neural_mass_regions_value = snn.get("neural_mass_regions")
    if neural_mass_regions_value is not None:
        neural_mass_regions = coerce_string_tuple(
            neural_mass_regions_value, "snn.neural_mass_regions"
        )
        try:
            SNNPopulationMapping(
                snn_region_names=tuple(circuit_regions),
                neural_mass_region_names=neural_mass_regions,
            ).indices_in_neural_mass()
        except ValueError as exc:
            raise ConfigValidationError(str(exc)) from exc
        snn["neural_mass_regions"] = list(neural_mass_regions)

    snn["circuits"] = circuits
    snn["mode"] = coupling_mode
    snn["max_feedback_amplitude"] = max_feedback_amplitude
    snn["sync_dt"] = sync_dt
    snn["input_rate_unit"] = input_rate_unit
    snn["output_activity_unit"] = output_activity_unit
    return snn
