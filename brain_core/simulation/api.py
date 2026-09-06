"""Publiczne API uruchamiania eksperymentów symulacyjnych."""

from __future__ import annotations

from typing import Any, Callable

from brain_core.experiments.protocols import TrialStimulus

from .config_schema import ExperimentConfig
from .engine import run_experiment as _run_experiment
from .results import ExperimentResult


def run_experiment(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> ExperimentResult:
    """Uruchom eksperyment i zwróć typowany ``ExperimentResult``.

    Jest to docelowy publiczny punkt wejścia. ``ExperimentResult`` implementuje
    ``Mapping``, dlatego odwołania w stylu ``result["time"]`` pozostają zgodne
    w okresie migracji.
    """
    return _run_experiment(
        config,
        progress_callback=progress_callback,
        stimulus_sequence=stimulus_sequence,
    )


def run_experiment_legacy(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> dict[str, Any]:
    """Uruchom eksperyment i zwróć literalny słownik legacy.

    Funkcja jest jawną granicą kompatybilności dla starszych integracji, które
    wymagają ``dict`` zamiast interfejsu ``Mapping``.
    """
    return _run_experiment(
        config,
        progress_callback=progress_callback,
        stimulus_sequence=stimulus_sequence,
    ).to_legacy_dict()
