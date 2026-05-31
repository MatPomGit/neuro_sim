"""Główny silnik uruchamiania eksperymentu i budowy artefaktów wynikowych."""

from __future__ import annotations

import json
import time as pytime
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import numpy as np

from brain_core.analysis.benchmark_loader import load_reference_benchmarks
from brain_core.analysis.reports import (
    AnalysisReport,
    build_analysis_report,
    build_clinical_difference_report,
    write_report_files,
)
from brain_core.cognition.mapping import mapping_for_task
from brain_core.experiments.protocols import ErrorType, TrialResult, get_task
from brain_model.io import build_output_dir, save_run
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from .config_schema import ExperimentConfig
from .events import build_event_timeline
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
    if task_name == "roving_oddball":
        if condition == "deviant":
            return "detect" if key != 0 else None
        return "detect" if key == 0 else None
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


def _condition_gain(condition: str) -> float:
    """Zwraca deterministyczne wzmocnienie wejścia regionalnego dla warunku.

    Parameters
    ----------
    condition:
        Nazwa warunku eksperymentalnego.

    Returns
    -------
    float
        Bezwymiarowe wzmocnienie amplitudy wejścia regionalnego.
    """
    gains = {
        "incongruent": 1.35,
        "nogo": 1.3,
        "target": 1.25,
        "deviant": 1.4,
        "standard": 0.8,
    }
    return gains.get(condition, 1.0)


def _regional_input_for_stimulus(task_name: str, condition: str) -> dict[str, float]:
    """Przekłada bodziec zadania na deterministyczne wejście regionalne.

    Parameters
    ----------
    task_name:
        Techniczna nazwa zadania poznawczego.
    condition:
        Warunek pojedynczego bodźca.

    Returns
    -------
    dict[str, float]
        Mapa region→amplituda wejścia dla bieżącego bodźca.
    """
    mapping = mapping_for_task(task_name)
    gain = _condition_gain(condition)
    return {
        region: round(gain / (idx + 1), 6) for idx, region in enumerate(mapping.regions)
    }


def _build_task_activation_summary(
    task_name: str,
    trial_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Buduje podsumowanie regionów i funkcji pobudzonych przez task.

    Parameters
    ----------
    task_name:
        Techniczna nazwa zadania poznawczego.
    trial_events:
        Lista zdarzeń bodźcowych z wejściami regionalnymi.

    Returns
    -------
    dict[str, Any]
        Sekcja raportu opisująca funkcje, regiony i średnie pobudzenie.
    """
    mapping = mapping_for_task(task_name)
    totals = {region: 0.0 for region in mapping.regions}
    for event in trial_events:
        regional_input = event.get("regional_input", {})
        for region in totals:
            totals[region] += float(regional_input.get(region, 0.0))

    event_count = max(len(trial_events), 1)
    mean_regional_input = {
        region: round(total / event_count, 6) for region, total in totals.items()
    }
    return {
        "task_name": mapping.task_name,
        "functions": list(mapping.functions),
        "regions": list(mapping.regions),
        "module_names": list(mapping.module_names),
        "mean_regional_input": mean_regional_input,
    }


def _attach_task_activation_section(
    report: AnalysisReport,
    task_activation: dict[str, Any],
) -> AnalysisReport:
    """Dodaje sekcję task→regiony/funkcje do raportu analizy.

    Parameters
    ----------
    report:
        Raport analizy sygnałów do rozszerzenia.
    task_activation:
        Podsumowanie pobudzenia regionów i funkcji przez zadanie.

    Returns
    -------
    AnalysisReport
        Nowy raport z dodatkową sekcją opisową.
    """
    payload = dict(report.payload)
    payload["task_activation"] = task_activation
    return AnalysisReport(payload=payload)


def _simulate_task_trials(
    config: ExperimentConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Symuluje przebieg triali i zwraca bodźce oraz wyniki punktacji."""
    task_name = str(config.task.get("name", "stroop"))
    task = get_task(task_name, **config.task)
    duration = float(config.task.get("duration", 45.0))
    stimuli = [
        stimulus.with_regional_input(
            _regional_input_for_stimulus(task.name, stimulus.condition)
        )
        for stimulus in task.generate_stimuli(seed=config.seed, duration_s=duration)
    ]

    scheduler = SimulationScheduler(stimuli=[TaskStimulusPlayer(stimuli=stimuli)])
    state = SimulationState()
    for _ in range(round(duration / config.timestep)):
        scheduler.run_step(state, config.timestep)

    trial_results: list[dict[str, Any]] = []
    for stimulus in stimuli:
        observed = _deterministic_observed_response(
            task.name,
            stimulus.condition,
            stimulus.trial_id,
            config.seed,
            expected=task.expected_response(stimulus),
        )
        reaction_time = (
            None
            if observed is None
            else round(0.25 + ((stimulus.trial_id + config.seed) % 5) * 0.05, 3)
        )
        result: TrialResult = task.score_trial(stimulus, observed, reaction_time)
        trial_result = {
            "trial_id": result.trial_id,
            "reaction_time_s": result.reaction_time_s,
            "correct": result.correct,
            "error_type": (
                result.error_type.value
                if isinstance(result.error_type, ErrorType)
                else str(result.error_type)
            ),
            "condition": result.condition,
        }
        trial_result["regional_input"] = dict(stimulus.regional_input)
        for metric_name in (
            "surprise_index",
            "habituation_level",
            "readaptation_latency",
        ):
            if metric_name in stimulus.payload:
                trial_result[metric_name] = stimulus.payload[metric_name]
        trial_results.append(trial_result)

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
    task_activation = _build_task_activation_summary(
        str(config.task.get("name", "stroop")), trial_events
    )

    eeg_raw = oscillations.get("eeg", activity[:, :2])
    eeg = eeg_raw[:, None] if getattr(eeg_raw, "ndim", 1) == 1 else eeg_raw
    fmri = activity[:, :2]
    behavior_series = (
        behavior.get("decision_score", activity[:, 0])
        if isinstance(behavior, dict)
        else activity[:, 0]
    )
    behavior_matrix = (
        behavior_series[:, None]
        if getattr(behavior_series, "ndim", 1) == 1
        else behavior_series
    )

    benchmark = load_reference_benchmarks()
    benchmark = {
        "eeg": _align_cols(_align_rows(benchmark["eeg"], eeg.shape[0]), eeg.shape[1]),
        "fmri": _align_cols(
            _align_rows(benchmark["fmri"], fmri.shape[0]), fmri.shape[1]
        ),
        "behavior": _align_cols(
            _align_rows(benchmark["behavior"], behavior_matrix.shape[0]),
            behavior_matrix.shape[1],
        ),
    }
    analysis_report = build_analysis_report(
        eeg=eeg,
        fmri=fmri,
        behavior=behavior_matrix,
        benchmark=benchmark,
        fs=1.0 / config.timestep,
        analysis_set=config.analysis.get("sets"),
    )
    analysis_report = _attach_task_activation_section(analysis_report, task_activation)
    event_timeline = build_event_timeline(
        time=time,
        activity=activity,
        diagnostics=diagnostics,
        trial_events=trial_events,
        trial_results=trial_results,
        pathology=config.pathology,
        clinical_profile=config.clinical_profile,
        region_names=list(model.names),
    )
    analysis_report.payload["event_timeline"] = event_timeline
    analysis_report.payload["clinical_profile"] = dict(config.clinical_profile)

    save_info: dict[str, Any] | None = None
    if config.output.get("save_results", False):
        out_dir = build_output_dir(
            config.task.get("scenario", "run"), config.output.get("label", "run")
        )
        report_files = write_report_files(
            analysis_report, Path(out_dir), stem="analysis_report"
        )
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
        if config.output.get("save_event_timeline", True):
            event_timeline_path = Path(out_dir) / "event_timeline.json"
            event_timeline_path.write_text(
                json.dumps(event_timeline, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            save_info["event_timeline"] = str(event_timeline_path)

    return {
        "model": model,
        "time": time,
        "activity": activity,
        "diagnostics": diagnostics,
        "oscillations": oscillations,
        "behavior": behavior,
        "trial_events": trial_events,
        "trial_results": trial_results,
        "event_timeline": event_timeline,
        "analysis_report": analysis_report.payload,
        "task_activation": task_activation,
        "clinical_profile": dict(config.clinical_profile),
        "save_info": save_info,
        "elapsed": elapsed,
    }


def apply_clinical_profile_config(
    base_config: ExperimentConfig,
    profile_config: dict[str, Any],
) -> ExperimentConfig:
    """Scal bazową konfigurację zadania z pojedynczym profilem klinicznym.

    Parameters
    ----------
    base_config:
        Konfiguracja referencyjna definiująca wspólny task i seed.
    profile_config:
        Zweryfikowany fragment konfiguracji profilu klinicznego.

    Returns
    -------
    ExperimentConfig
        Nowa konfiguracja z tym samym zadaniem i seedem, ale z nadpisaniami
        modelu, patologii i metadanych profilu klinicznego.
    """
    profile = deepcopy(profile_config)
    merged_model = deepcopy(base_config.model)
    merged_model.update(profile.get("model", {}))

    output = deepcopy(base_config.output)
    profile_metadata = profile.get("clinical_profile", {})
    profile_id = profile_metadata.get("id", output.get("label", "clinical_profile"))
    output.update(profile.get("output", {}))
    output["label"] = str(profile_id)

    return replace(
        base_config,
        model=merged_model,
        pathology=deepcopy(profile.get("pathology", base_config.pathology)),
        output=output,
        clinical_profile=deepcopy(profile_metadata),
    )


def run_task_across_clinical_profiles(
    base_config: ExperimentConfig,
    clinical_profiles: list[dict[str, Any]],
    progress_callback: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Uruchom ten sam task z tym samym seedem dla wielu profili klinicznych.

    Parameters
    ----------
    base_config:
        Konfiguracja bazowa. Jej `task` oraz `seed` są zachowywane dla każdego
        profilu, aby różnice wynikały z profilu klinicznego, a nie z losowości.
    clinical_profiles:
        Lista fragmentów konfiguracji wczytanych z `configs/clinical_profiles/`.
    progress_callback:
        Opcjonalna funkcja raportująca postęp pojedynczego uruchomienia.

    Returns
    -------
    dict[str, Any]
        Wyniki per profil oraz raport różnic względem `healthy_v1`, jeśli jest
        dostępny, albo względem pierwszego profilu z listy.

    Raises
    ------
    ValueError
        Gdy lista profili klinicznych jest pusta.
    """
    if not clinical_profiles:
        raise ValueError("Lista profili klinicznych nie może być pusta.")

    runs: dict[str, dict[str, Any]] = {}
    for profile_config in clinical_profiles:
        profile_id = str(
            profile_config.get("clinical_profile", {}).get("id", "profile")
        )
        profile_run_config = apply_clinical_profile_config(base_config, profile_config)
        runs[profile_id] = run_experiment(
            profile_run_config, progress_callback=progress_callback
        )

    reference_id = "healthy_v1" if "healthy_v1" in runs else next(iter(runs))
    compared = {key: value for key, value in runs.items() if key != reference_id}
    difference_report = build_clinical_difference_report(runs[reference_id], compared)
    return {
        "seed": base_config.seed,
        "task": dict(base_config.task),
        "reference_profile_id": reference_id,
        "runs": runs,
        "clinical_difference_report": difference_report.payload,
    }
