"""Walidacja sekcji task konfiguracji symulacji."""

from __future__ import annotations

from typing import Any

from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_non_empty_string,
    require_non_negative_int,
    require_number,
    require_positive_number,
)


def validate_task_config(task: dict[str, Any]) -> dict[str, Any]:
    """Waliduje parametry zadania eksperymentalnego.

    Parameters
    ----------
    task:
        Sekcja konfiguracji z nazwą scenariusza, czasem trwania oraz
        opcjonalnymi parametrami liczbowymi zadania.

    Returns
    -------
    dict[str, Any]
        Znormalizowana sekcja ``task`` gotowa do użycia przez silnik.

    Raises
    ------
    ConfigValidationError
        Gdy wymagane pola są nieobecne albo pola liczbowe, tekstowe lub
        całkowite mają niepoprawny typ bądź zakres.
    """
    if "scenario" not in task:
        raise ConfigValidationError("Brak pola task.scenario")
    task["scenario"] = require_non_empty_string(task["scenario"], "task.scenario")
    if "duration" not in task:
        raise ConfigValidationError("Brak pola task.duration")
    task["duration"] = require_positive_number(task["duration"], "task.duration")
    if "name" in task:
        task["name"] = require_non_empty_string(task["name"], "task.name")
    for int_field in ("n_runs", "run_length_min", "run_length_max", "n"):
        if int_field in task:
            task[int_field] = require_non_negative_int(
                task[int_field], f"task.{int_field}"
            )
    for number_field in ("deviant_probability", "inter_stimulus_interval", "jitter"):
        if number_field in task:
            task[number_field] = require_number(
                task[number_field], f"task.{number_field}"
            )
    return task
