"""Główny silnik uruchamiania eksperymentu i budowy artefaktów wynikowych."""

from __future__ import annotations

import json
import time as pytime
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import numpy as np

from brain_core.analysis.benchmark_loader import load_reference_benchmark_bundle
from brain_core.analysis.reports import (
    AnalysisReport,
    build_analysis_report,
    build_clinical_difference_report,
    build_roving_oddball_report,
    write_report_files,
)
from brain_core.cognition.mapping import mapping_for_task
from brain_core.experiments.protocols import ErrorType, TrialResult, get_task
from brain_core.populations.spiking_population import Brian2SpikingPopulationAdapter
from brain_model.io import build_output_dir, save_run
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from .config_schema import ExperimentConfig
from .events import build_event_timeline
from .scheduler import SimulationScheduler, TaskStimulusPlayer
from .signal_adapter import CouplingSignalAdapter, SNNPopulationMapping
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


def _build_snn_runtime(
    *,
    config: ExperimentConfig,
    region_names: list[str],
) -> tuple[
    tuple[str, ...],
    SNNPopulationMapping,
    CouplingSignalAdapter,
    Brian2SpikingPopulationAdapter,
    np.ndarray,
    np.ndarray,
]:
    """Buduje wspólne obiekty wykonawcze dla porównań SNN.

    Parameters
    ----------
    config:
        Zweryfikowana konfiguracja eksperymentu.
    region_names:
        Nazwy regionów neural-mass w kolejności modelu.

    Returns
    -------
    tuple
        Regiony SNN, mapowanie, adapter sygnału, populacja SNN, indeksy regionów
        i wektor wzmocnień sprzężenia.
    """
    circuits = config.snn.get("circuits", [])
    snn_regions = tuple(str(circuit["region"]) for circuit in circuits)
    mapping = SNNPopulationMapping(
        snn_region_names=snn_regions,
        neural_mass_region_names=tuple(region_names),
    )
    adapter = CouplingSignalAdapter(
        mapping=mapping,
        sync_dt=float(config.snn["sync_dt"]),
    )
    snn_population = Brian2SpikingPopulationAdapter(
        region_names=list(snn_regions),
        dt=min(config.timestep, float(config.snn["sync_dt"])),
    )
    mapped_indices = mapping.indices_in_neural_mass()
    gains = np.asarray(
        [float(circuit.get("coupling_gain", 0.2)) for circuit in circuits],
        dtype=float,
    )
    return snn_regions, mapping, adapter, snn_population, mapped_indices, gains


def _summarize_trace_metrics(
    *,
    baseline_trace: np.ndarray,
    compared_trace: np.ndarray,
    feedback_trace: np.ndarray | None = None,
) -> dict[str, float | int]:
    """Wylicza stabilne metryki porównania przebiegów regionalnych.

    Parameters
    ----------
    baseline_trace:
        Bazowy przebieg neural-mass bez SNN.
    compared_trace:
        Przebieg porównywany z bazowym.
    feedback_trace:
        Opcjonalny przebieg amplitudy wejścia zwrotnego SNN.

    Returns
    -------
    dict[str, float | int]
        Zaokrąglone metryki aktywności, długości i różnic względem baseline.
    """
    difference = np.abs(compared_trace - baseline_trace)
    metrics = {
        "mean_activity": round(float(np.mean(compared_trace)), 6),
        "max_activity": round(float(np.max(np.abs(compared_trace))), 6),
        "mean_abs_difference_vs_baseline": round(float(np.mean(difference)), 6),
        "max_abs_difference_vs_baseline": round(float(np.max(difference)), 6),
        "length": int(compared_trace.shape[0]),
    }
    if feedback_trace is not None:
        metrics["max_abs_feedback_drive"] = round(
            float(np.max(np.abs(feedback_trace))), 6
        )
    return metrics


def _simulate_closed_loop_snn_activity(
    *,
    config: ExperimentConfig,
    region_names: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    """Uruchamia wariant, w którym SNN modyfikuje wejście HIP w kolejnym kroku.

    Parameters
    ----------
    config:
        Zweryfikowana konfiguracja z sekcją SNN.
    region_names:
        Nazwy regionów neural-mass w kolejności modelu.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Aktywność closed-loop oraz macierz zastosowanego wejścia zwrotnego.
    """
    _, _, adapter, snn_population, _, gains = _build_snn_runtime(
        config=config,
        region_names=region_names,
    )
    sync_stride = max(1, int(round(float(config.snn["sync_dt"]) / config.timestep)))
    max_feedback_amplitude = float(config.snn.get("max_feedback_amplitude", 0.15))
    pending_drive = np.zeros(len(region_names), dtype=float)
    applied_drives: list[np.ndarray] = []

    def external_drive_callback(
        step_index: int,
        _time_s: float,
        cognitive_activity: np.ndarray,
        excitatory_activity: np.ndarray,
        inhibitory_activity: np.ndarray,
    ) -> np.ndarray:
        """Zwraca opóźnione wejście SNN i kolejkuje sygnał na następny krok."""
        nonlocal pending_drive
        applied_drive = pending_drive.copy()
        if step_index % sync_stride == 0:
            excitatory_source = excitatory_activity
            inhibitory_source = inhibitory_activity
            if not np.any(excitatory_source) and not np.any(inhibitory_source):
                excitatory_source = cognitive_activity
                inhibitory_source = 0.5 * cognitive_activity
            signal = adapter.rate_to_spike_drive(
                excitatory_rate_hz=excitatory_source * adapter.MAX_FIRING_RATE_HZ,
                inhibitory_rate_hz=inhibitory_source * adapter.MAX_FIRING_RATE_HZ,
            )
            snn_output = snn_population.step(signal)
            coupling_drive = adapter.spike_summary_to_closed_loop_drive(
                snn_output=snn_output,
                n_regions=len(region_names),
                coupling_gain=gains,
                max_abs_amplitude=max_feedback_amplitude,
            )
            pending_drive = coupling_drive.drive
        applied_drives.append(applied_drive)
        return applied_drive

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
    _, closed_loop_activity, _, _, _ = model.simulate(
        T=float(config.task.get("duration", 45.0)),
        external_drive_callback=external_drive_callback,
    )
    feedback = np.asarray(applied_drives, dtype=float)
    return closed_loop_activity, feedback


def _run_local_snn_comparison(
    *,
    config: ExperimentConfig,
    region_names: list[str],
    activity: np.ndarray,
    oscillations: dict[str, Any],
) -> dict[str, Any] | None:
    """Porównuje baseline oraz faktycznie policzone warianty SNN.

    Parameters
    ----------
    config:
        Zweryfikowana konfiguracja eksperymentu z sekcją `snn`.
    region_names:
        Nazwy regionów neural-mass w kolejności kolumn macierzy `activity`.
    activity:
        Bazowy przebieg aktywności neural-mass bez sprzężenia zwrotnego SNN.
    oscillations:
        Słownik oscylacji zawierający sygnały ekscytujące i hamujące.

    Returns
    -------
    dict[str, Any] | None
        Sekcja raportu z metrykami trybów albo `None`, gdy SNN jest wyłączone.

    Raises
    ------
    ValueError
        Gdy konfiguracja SNN nie pasuje do regionów modelu lub sygnałów oscylacji.
    """
    if not bool(config.snn.get("enabled", False)):
        return None

    circuits = config.snn.get("circuits", [])
    if not circuits:
        return None

    (
        snn_regions,
        _,
        adapter,
        snn_population,
        mapped_indices,
        gains,
    ) = _build_snn_runtime(config=config, region_names=region_names)

    excitatory_raw = oscillations.get("excitatory")
    inhibitory_raw = oscillations.get("inhibitory")
    if excitatory_raw is None or inhibitory_raw is None:
        raise ValueError(
            "Sygnały oscylacji 'excitatory' lub 'inhibitory' są wymagane do porównania SNN"
        )
    excitatory = np.asarray(excitatory_raw, dtype=float)
    inhibitory = np.asarray(inhibitory_raw, dtype=float)
    if excitatory.shape != activity.shape or inhibitory.shape != activity.shape:
        raise ValueError("Sygnały oscylacji nie pasują do macierzy aktywności")

    sync_stride = max(1, int(round(float(config.snn["sync_dt"]) / config.timestep)))
    snn_activity = np.zeros_like(activity, dtype=float)
    report_only_activity = np.array(activity, dtype=float, copy=True)
    last_regional = np.zeros(activity.shape[1], dtype=float)

    for step_index in range(activity.shape[0]):
        if step_index % sync_stride == 0:
            signal = adapter.rate_to_spike_drive(
                excitatory_rate_hz=excitatory[step_index] * adapter.MAX_FIRING_RATE_HZ,
                inhibitory_rate_hz=inhibitory[step_index] * adapter.MAX_FIRING_RATE_HZ,
            )
            snn_output = snn_population.step(signal)
            last_regional = adapter.spike_summary_to_regional_activity(
                snn_output, n_regions=activity.shape[1]
            )
        snn_activity[step_index] = last_regional
        report_only_activity[step_index, mapped_indices] = np.clip(
            (1.0 - gains) * activity[step_index, mapped_indices]
            + gains * last_regional[mapped_indices],
            0.0,
            1.0,
        )

    requested_mode = str(config.snn.get("mode", "report_only"))
    computed_modes = ["baseline", "report_only_snn", "closed_loop_snn"]

    closed_loop_activity, feedback_drive = _simulate_closed_loop_snn_activity(
        config=config,
        region_names=region_names,
    )
    if closed_loop_activity.shape != activity.shape:
        raise ValueError("Przebieg closed_loop_snn nie pasuje do baseline")
    if feedback_drive.shape != activity.shape:
        raise ValueError("Sygnał sprzężenia closed_loop_snn nie pasuje do baseline")

    region_differences: dict[str, dict[str, float]] = {}
    mode_metrics: dict[str, dict[str, dict[str, float]]] = {
        mode_name: {} for mode_name in computed_modes
    }
    for region, region_index in zip(snn_regions, mapped_indices, strict=True):
        baseline_trace = activity[:, region_index]
        report_only_trace = report_only_activity[:, region_index]
        closed_loop_trace = closed_loop_activity[:, region_index]
        feedback_trace = feedback_drive[:, region_index]
        mode_metrics["baseline"][region] = {
            "mean_activity": round(float(np.mean(baseline_trace)), 6),
            "max_activity": round(float(np.max(np.abs(baseline_trace))), 6),
            "length": int(baseline_trace.shape[0]),
        }
        mode_metrics["report_only_snn"][region] = _summarize_trace_metrics(
            baseline_trace=baseline_trace,
            compared_trace=report_only_trace,
        )
        mode_metrics["closed_loop_snn"][region] = _summarize_trace_metrics(
            baseline_trace=baseline_trace,
            compared_trace=closed_loop_trace,
            feedback_trace=feedback_trace,
        )
        region_differences[region] = {
            "mean_without_snn": mode_metrics["baseline"][region]["mean_activity"],
            "mean_snn_local_activity": round(
                float(np.mean(snn_activity[:, region_index])), 6
            ),
            "mean_with_snn": mode_metrics["report_only_snn"][region]["mean_activity"],
            "mean_abs_difference": mode_metrics["report_only_snn"][region][
                "mean_abs_difference_vs_baseline"
            ],
            "max_abs_difference": mode_metrics["report_only_snn"][region][
                "max_abs_difference_vs_baseline"
            ],
        }

    return {
        "status_pl": "włączony lokalny obwód SNN",
        "regions": list(snn_regions),
        "neural_mass_regions": list(region_names),
        "requested_mode": requested_mode,
        "computed_modes": computed_modes,
        "comparison_note_pl": comparison_note_pl,
        "sync_dt_s": float(config.snn["sync_dt"]),
        "max_feedback_amplitude": float(config.snn.get("max_feedback_amplitude", 0.15)),
        "input_rate_unit": str(config.snn.get("input_rate_unit", "Hz")),
        "output_activity_unit": str(config.snn.get("output_activity_unit", "fraction")),
        "backend": str(circuits[0].get("backend", "brian2")),
        "mode_metrics": mode_metrics,
        "region_differences": region_differences,
    }


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
        for payload_name in (
            "tone_hz",
            "previous_standard_hz",
            "run_index",
            "repetition_index",
            "is_new_standard",
        ):
            if payload_name in stimulus.payload:
                trial_result[payload_name] = stimulus.payload[payload_name]
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

    benchmark_bundle = load_reference_benchmark_bundle()
    benchmark = {
        "eeg": _align_cols(
            _align_rows(benchmark_bundle.data["eeg"], eeg.shape[0]), eeg.shape[1]
        ),
        "fmri": _align_cols(
            _align_rows(benchmark_bundle.data["fmri"], fmri.shape[0]), fmri.shape[1]
        ),
        "behavior": _align_cols(
            _align_rows(benchmark_bundle.data["behavior"], behavior_matrix.shape[0]),
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
        benchmark_metadata=benchmark_bundle.metadata_payload(),
    )
    analysis_report = _attach_task_activation_section(analysis_report, task_activation)
    if str(config.task.get("name") or "") in {"roving_oddball", "roving-oddball"}:
        analysis_report.payload["roving_oddball"] = build_roving_oddball_report(
            trial_results,
            profile_id=str(
                config.clinical_profile.get("id") or config.output.get("label") or "run"
            ),
        )
    snn_comparison = _run_local_snn_comparison(
        config=config,
        region_names=list(model.names),
        activity=activity,
        oscillations=oscillations,
    )
    if snn_comparison is not None:
        analysis_report.payload["snn_comparison"] = snn_comparison
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
        "snn_comparison": snn_comparison,
        "save_info": save_info,
        "elapsed": elapsed,
    }


def _classify_roving_profile_group(profile_id: str, result: dict[str, Any]) -> str:
    """Klasyfikuje profil roving oddball do grupy healthy/disorder/lesion.

    Parameters
    ----------
    profile_id:
        Techniczny identyfikator profilu klinicznego.
    result:
        Wynik uruchomienia eksperymentu zawierający metadane profilu i patologię.

    Returns
    -------
    str
        Jedna z grup porównawczych: ``healthy``, ``disorder`` albo ``lesion``.
    """
    profile = result.get("clinical_profile") or {}
    profile_text = " ".join(
        str(value).lower()
        for value in (
            profile_id,
            profile.get("id", ""),
            profile.get("mechanism", ""),
            profile.get("display_name", ""),
        )
    )
    pathology = (result.get("analysis_report") or {}).get("clinical_profile") or {}
    pathology_text = str(pathology.get("pathology_scenario", "")).lower()
    combined_text = f"{profile_text} {pathology_text}"
    if "lesion" in combined_text or "uszkod" in combined_text:
        return "lesion"
    if "healthy" in combined_text or "zdrow" in combined_text:
        return "healthy"
    return "disorder"


def _build_roving_profile_comparison(
    *,
    seed: int,
    runs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Porównuje metryki roving oddball przy wspólnym seedzie i sekwencji.

    Parameters
    ----------
    seed:
        Ziarno użyte do wygenerowania wspólnej sekwencji bodźców.
    runs:
        Wyniki uruchomień per profil kliniczny.

    Returns
    -------
    dict[str, Any]
        Raport z agregatami per profil oraz flagami zgodności seeda i sekwencji.
    """
    profiles: list[dict[str, object]] = []
    signatures: list[Any] = []
    for profile_id, result in runs.items():
        roving_report = build_roving_oddball_report(
            result.get("trial_results") or [],
            profile_id=profile_id,
        )
        roving_report["profile_group"] = _classify_roving_profile_group(
            profile_id,
            result,
        )
        profiles.append(roving_report)
        signatures.append(roving_report.get("sequence_signature") or [])

    reference_signature = signatures[0] if signatures else []
    same_sequence = all(signature == reference_signature for signature in signatures)
    return {
        "seed": seed,
        "same_seed": True,
        "same_sequence": same_sequence,
        "profiles": profiles,
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
    batch_report: dict[str, Any] = {
        "seed": base_config.seed,
        "task": dict(base_config.task),
        "reference_profile_id": reference_id,
        "runs": runs,
        "clinical_difference_report": difference_report.payload,
    }
    if str(base_config.task.get("name") or "") in {"roving_oddball", "roving-oddball"}:
        roving_profile_comparison = _build_roving_profile_comparison(
            seed=base_config.seed,
            runs=runs,
        )
        batch_report["roving_profile_comparison"] = roving_profile_comparison
        difference_report.payload["roving_profile_comparison"] = (
            roving_profile_comparison
        )
    return batch_report
