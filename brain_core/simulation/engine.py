from __future__ import annotations

"""Główny silnik uruchamiania eksperymentu i budowy artefaktów wynikowych."""

import time as pytime
from pathlib import Path
from typing import Any, Callable

import numpy as np

from brain_core.analysis.benchmark_loader import load_reference_benchmarks
from brain_core.analysis.reports import build_analysis_report, write_report_files
from brain_core.experiments.protocols import ErrorType, TrialResult, get_task
from brain_model.io import build_output_dir, save_run
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from .config_schema import ExperimentConfig
from .scheduler import SimulationScheduler, TaskStimulusPlayer
from .state import SimulationState


def _deterministic_observed_response(
    task_name: str,
    condition: str,
    trial_id: int,
    seed: int,
    expected: str | None = None,
) -> str | None:
    """Generuje deterministyczną odpowiedź obserwowaną do walidacji tasków."""
    key = (trial_id + seed) % 7
    if task_name == "stroop":
        if key == 0:
            return None
        if key == 1:
            colors = [c for c in ("red", "green", "blue", "yellow") if c != expected]
            return colors[(trial_id + seed) % len(colors)]
        return expected
    if task_name == "go_nogo":
        if condition == "go":
            return "press" if key != 0 else None
        return "press" if key == 0 else None
    if task_name == "n_back":
        if condition == "target":
            return "match" if key != 0 else None
        return "match" if key == 0 else None
    return None


def _align_rows(reference: np.ndarray, target_rows: int) -> np.ndarray:
    """Dopasowuje liczbę wierszy macierzy referencyjnej do wymiaru docelowego."""
    if reference.shape[0] == target_rows:
        return reference
    idx = np.linspace(0, reference.shape[0] - 1, num=target_rows).astype(int)
    return reference[idx]


def _align_cols(reference: np.ndarray, target_cols: int) -> np.ndarray:
    """Dopasowuje liczbę kolumn macierzy referencyjnej do wymiaru docelowego."""
    if reference.shape[1] == target_cols:
        return reference
    if reference.shape[1] > target_cols:
        return reference[:, :target_cols]
    reps = int(np.ceil(target_cols / reference.shape[1]))
    expanded = np.tile(reference, (1, reps))
    return expanded[:, :target_cols]


def _simulate_task_trials(config: ExperimentConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Symuluje przebieg triali i zwraca bodźce oraz wyniki punktacji."""
    task_name = str(config.task.get("name", "stroop"))
    task = get_task(task_name, **config.task)
    duration = float(config.task.get("duration", 45.0))
    stimuli = task.generate_stimuli(seed=config.seed, duration_s=duration)

    scheduler = SimulationScheduler(stimuli=[TaskStimulusPlayer(stimuli=stimuli)])
    state = SimulationState()
    for _ in range(round(duration / config.timestep)):
        scheduler.run_step(state, config.timestep)

    trial_results: list[dict[str, Any]] = []
    for stimulus in stimuli:
        observed = _deterministic_observed_response(task.name, stimulus.condition, stimulus.trial_id, config.seed, expected=task.expected_response(stimulus))
        reaction_time = None if observed is None else round(0.25 + ((stimulus.trial_id + config.seed) % 5) * 0.05, 3)
        result: TrialResult = task.score_trial(stimulus, observed, reaction_time)
        trial_results.append(
            {
                "trial_id": result.trial_id,
                "reaction_time_s": result.reaction_time_s,
                "correct": result.correct,
                "error_type": result.error_type.value if isinstance(result.error_type, ErrorType) else str(result.error_type),
                "condition": result.condition,
            }
        )

    return state.metrics.get("trial_events", []), trial_results


def run_experiment(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Uruchamia pełny eksperyment, analizę oraz opcjonalny zapis wyników."""
    model_params = BrainParams(dt=config.timestep, **config.model)
    osc_params = WilsonCowanParams(**config.integrator.get("oscillator", {}))
    stimulus_scenario = str(config.task.get("scenario", "reward-learning"))
    try:
        model = CognitiveBrainModel(
            params=model_params,
            oscillator_params=osc_params,
            seed=config.seed,
            stimulus=stimulus_scenario,
        )
    except ValueError:
        model = CognitiveBrainModel(
            params=model_params,
            oscillator_params=osc_params,
            seed=config.seed,
            stimulus="reward-learning",
        )

    start = pytime.perf_counter()
    time, activity, diagnostics, oscillations, behavior = model.simulate(
        T=float(config.task.get("duration", 45.0)),
        progress_callback=progress_callback,
    )
    elapsed = pytime.perf_counter() - start

    trial_events, trial_results = _simulate_task_trials(config)

    eeg_raw = oscillations.get("eeg", activity[:, :2])
    eeg = eeg_raw[:, None] if getattr(eeg_raw, "ndim", 1) == 1 else eeg_raw
    fmri = activity[:, :2]
    behavior_series = behavior.get("decision_score", activity[:, 0]) if isinstance(behavior, dict) else activity[:, 0]
    behavior_matrix = behavior_series[:, None] if getattr(behavior_series, "ndim", 1) == 1 else behavior_series

    benchmark = load_reference_benchmarks()
    benchmark = {
        "eeg": _align_cols(_align_rows(benchmark["eeg"], eeg.shape[0]), eeg.shape[1]),
        "fmri": _align_cols(_align_rows(benchmark["fmri"], fmri.shape[0]), fmri.shape[1]),
        "behavior": _align_cols(_align_rows(benchmark["behavior"], behavior_matrix.shape[0]), behavior_matrix.shape[1]),
    }
    analysis_report = build_analysis_report(eeg=eeg, fmri=fmri, behavior=behavior_matrix, benchmark=benchmark, fs=1.0 / config.timestep)

    save_info: dict[str, Any] | None = None
    if config.output.get("save_results", False):
        out_dir = build_output_dir(config.task.get("scenario", "run"), config.output.get("label", "run"))
        report_files = write_report_files(analysis_report, Path(out_dir), stem="analysis_report")
        save_info = save_run(
            out_dir,
            time,
            activity,
            diagnostics,
            oscillations,
            model_params=model.p,
            oscillator_params=model.oscillator_bank.params,
            scenario=oscillations.get("metadata"),
            seed=config.seed,
            duration_s=elapsed,
        )
        save_info["analysis_report_files"] = report_files

    return {
        "model": model,
        "time": time,
        "activity": activity,
        "diagnostics": diagnostics,
        "oscillations": oscillations,
        "behavior": behavior,
        "trial_events": trial_events,
        "trial_results": trial_results,
        "analysis_report": analysis_report.payload,
        "save_info": save_info,
        "elapsed": elapsed,
    }
