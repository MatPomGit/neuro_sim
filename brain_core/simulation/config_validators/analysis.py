"""Walidacja sekcji analysis konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_bool,
    require_list,
    require_non_empty_string,
    require_non_negative_int,
)


def validate_analysis_config(analysis: dict[str, Any]) -> dict[str, Any]:
    """Waliduje wybór zestawów analiz uruchamianych po symulacji.

    Parameters
    ----------
    analysis:
        Sekcja konfiguracji z listą zestawów analiz oraz opcjonalnymi
        parametrami raportowania triali.

    Returns:
    -------
    dict[str, Any]
        Znormalizowana sekcja ``analysis`` z unikalnymi nazwami analiz.

    Raises:
    ------
    ConfigValidationError
        Gdy lista analiz ma niepoprawny typ, zawiera puste lub nieznane nazwy
        albo parametry raportowania mają niepoprawny typ.
    """
    sets_val = require_list(analysis.get("sets", []), "analysis.sets")
    sets_val = [
        require_non_empty_string(set_name, f"analysis.sets[{idx}]")
        for idx, set_name in enumerate(sets_val)
    ]
    if len(sets_val) != len(set(sets_val)):
        raise ConfigValidationError("analysis.sets musi zawierać unikalne nazwy")

    allowed = {"spectral", "phase_locking", "connectivity", "information_flow"}
    unknown = [name for name in sets_val if name not in allowed]
    if unknown:
        raise ConfigValidationError(f"Nieznane analysis.sets: {unknown}")
    analysis["sets"] = sets_val
    if "max_report_trials" in analysis:
        analysis["max_report_trials"] = require_non_negative_int(
            analysis["max_report_trials"], "analysis.max_report_trials"
        )
    if "include_full_trial_table" in analysis:
        analysis["include_full_trial_table"] = require_bool(
            analysis["include_full_trial_table"],
            "analysis.include_full_trial_table",
        )
    return analysis
