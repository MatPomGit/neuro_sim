"""Publiczne API uruchamiania eksperymentów symulacyjnych."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from brain_core.experiments.protocols import TrialStimulus
from brain_model.io import REPO_ROOT, collect_environment_info, collect_git_info

from .config_schema import ExperimentConfig
from .engine import run_experiment as _run_experiment_legacy
from .results import ExperimentResult


def _result_from_legacy(
    config: ExperimentConfig,
    legacy: dict[str, Any],
) -> ExperimentResult:
    """Zbuduj typowany wynik z kontraktu backendu zgodnego z legacy API."""
    analysis_report = dict(legacy.get("analysis_report") or {})
    randomness = dict(legacy.get("randomness") or {})
    save_info = legacy.get("save_info")
    output_dir = (
        Path(save_info["output_dir"])
        if isinstance(save_info, dict) and save_info.get("output_dir")
        else None
    )
    return ExperimentResult(
        config=config,
        signals={
            "model": legacy.get("model"),
            "time": legacy.get("time"),
            "activity": legacy.get("activity"),
            "diagnostics": legacy.get("diagnostics"),
            "oscillations": legacy.get("oscillations"),
            "behavior": legacy.get("behavior"),
        },
        metrics={
            "metrics": analysis_report.get("metrics", {}),
            "comparison": analysis_report.get("comparison", {}),
            "randomness": randomness,
        },
        trial_events=list(legacy.get("trial_events") or []),
        analysis_report=analysis_report,
        output_dir=output_dir,
        git_info=collect_git_info(REPO_ROOT),
        environment_info=collect_environment_info(),
        trial_results=list(legacy.get("trial_results") or []),
        trial_report_context=dict(legacy.get("trial_report_context") or {}),
        stimulus_sequence_signature=dict(
            legacy.get("stimulus_sequence_signature") or {}
        ),
        event_timeline=list(legacy.get("event_timeline") or []),
        task_activation=dict(legacy.get("task_activation") or {}),
        clinical_profile=dict(legacy.get("clinical_profile") or {}),
        snn_comparison=legacy.get("snn_comparison"),
        save_info=save_info,
        elapsed=float(legacy.get("elapsed", 0.0)),
        randomness=randomness,
    )


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
    legacy = _run_experiment_legacy(
        config,
        progress_callback=progress_callback,
        stimulus_sequence=stimulus_sequence,
    )
    return _result_from_legacy(config, legacy)


def run_experiment_legacy(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> dict[str, Any]:
    """Uruchom eksperyment i zwróć literalny słownik legacy.

    Funkcja jest jawnie oznaczoną granicą kompatybilności dla starszych
    integracji, które wymagają ``dict`` zamiast interfejsu ``Mapping``.
    """
    return _run_experiment_legacy(
        config,
        progress_callback=progress_callback,
        stimulus_sequence=stimulus_sequence,
    )
