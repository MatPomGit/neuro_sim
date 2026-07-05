"""Główny silnik uruchamiania eksperymentu i budowy artefaktów wynikowych."""

from __future__ import annotations

import time as pytime
from pathlib import Path
from typing import Any, Callable

import numpy as np

from brain_core.analysis.benchmark_loader import load_reference_benchmark_bundle
from brain_core.analysis.reports import (
    AnalysisReport,
    build_analysis_report,
    build_roving_oddball_report,
    write_report_files,
)
from brain_core.cognition.mapping import mapping_for_task
from brain_core.experiments.protocols import (
    ErrorType,
    TrialResult,
    TrialStimulus,
    get_task,
)
from brain_model.io import (
    REPO_ROOT,
    build_output_dir,
    collect_environment_info,
    collect_git_info,
    save_run,
)
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from .config_schema import ExperimentConfig
from .events import build_event_timeline
from .profile_comparison import (
    apply_clinical_profile_config as _apply_clinical_profile_config,
)
from .profile_comparison import (
    build_batch_educational_comments,
    build_profile_comparison_table,
    build_roving_profile_comparison,
    build_roving_profile_pair_comparisons,
    build_stimulus_sequence_signature,
    classify_roving_profile_group,
    describe_roving_signed_difference,
    summarize_batch_profiles,
)
from .profile_comparison import (
    run_task_across_clinical_profiles as _run_task_across_clinical_profiles,
)
from .random_sources import RandomSources
from .results import ExperimentResult
from .scheduler import SimulationScheduler, TaskStimulusPlayer
from .snn_runtime import (
    build_snn_runtime,
    classify_snn_feedback_amplitude,
    run_local_snn_comparison,
    simulate_closed_loop_snn_activity,
    summarize_trace_metrics,
)
from .state import SimulationState
from .timebase import compute_step_count


def _effective_rng_seed(config: ExperimentConfig) -> int:
    """Wyznacz ziarno RNG używane przez komponenty symulacji.

    Parameters
    ----------
    config:
        Konfiguracja eksperymentu z historycznym polem ``seed`` i docelowym
        polem ``rng_seed``.

    Returns:
    -------
    int
        Jawne ziarno generatora losowego; gdy ``rng_seed`` nie jest ustawione,
        zachowywana jest zgodność z polem ``seed``.
    """
    return int(config.rng_seed if config.rng_seed is not None else config.seed)


def _build_randomness_section(
    config: ExperimentConfig, random_sources: RandomSources
) -> dict[str, Any]:
    """Zbuduj sekcję replikowalności opisującą kontrolę losowości.

    Parameters
    ----------
    config:
        Konfiguracja eksperymentu zawierająca jawne pola ziarna.
    random_sources:
        Rejestr nazw komponentów, które pobrały deterministyczne strumienie RNG.

    Returns:
    -------
    dict[str, Any]
        Sekcja ``randomness`` do zapisu w metrykach, raporcie i wyniku API.
    """
    randomness = random_sources.metadata()
    randomness["seed"] = int(config.seed)
    return randomness


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

    Returns:
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

    Returns:
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

    Returns:
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

    Returns:
    -------
    AnalysisReport
        Nowy raport z dodatkową sekcją opisową.
    """
    payload = dict(report.payload)
    payload["task_activation"] = task_activation
    return AnalysisReport(payload=payload)


# Zachowujemy aliasy prywatne dla kompatybilności testów i starszych importów.
_build_snn_runtime = build_snn_runtime
_summarize_trace_metrics = summarize_trace_metrics
_classify_snn_feedback_amplitude = classify_snn_feedback_amplitude
_simulate_closed_loop_snn_activity = simulate_closed_loop_snn_activity
_run_local_snn_comparison = run_local_snn_comparison


def _generate_task_stimuli(config: ExperimentConfig) -> list[TrialStimulus]:
    """Wygeneruj deterministyczną sekwencję bodźców dla konfiguracji zadania.

    Parameters
    ----------
    config:
        Konfiguracja eksperymentu zawierająca nazwę zadania, czas trwania i seed.

    Returns:
    -------
    list[TrialStimulus]
        Bodźce z przypisanym wejściem regionalnym, gotowe do ponownego użycia w
        porównaniach profili klinicznych.
    """
    task_name = str(config.task.get("name", "stroop"))
    task = get_task(task_name, **config.task)
    duration = float(config.task.get("duration", 45.0))
    return [
        stimulus.with_regional_input(
            _regional_input_for_stimulus(task.name, stimulus.condition)
        )
        for stimulus in task.generate_stimuli(seed=config.seed, duration_s=duration)
    ]


def _simulate_task_trials(
    config: ExperimentConfig,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Symuluje przebieg triali i zwraca bodźce oraz wyniki punktacji.

    Parameters
    ----------
    config:
        Konfiguracja eksperymentu z taskiem i seedem.
    stimulus_sequence:
        Opcjonalna, wcześniej wygenerowana sekwencja bodźców. Umożliwia
        uruchomienie wielu profili klinicznych na identycznym bodźcu bez zmian
        w logice punktacji silnika.

    Returns:
    -------
    tuple[list[dict[str, Any]], list[dict[str, Any]]]
        Zdarzenia triali i wyniki punktacji.
    """
    task_name = str(config.task.get("name", "stroop"))
    task = get_task(task_name, **config.task)
    duration = float(config.task.get("duration", 45.0))
    stimuli = (
        list(stimulus_sequence)
        if stimulus_sequence is not None
        else _generate_task_stimuli(config)
    )

    scheduler = SimulationScheduler(stimuli=[TaskStimulusPlayer(stimuli=stimuli)])
    state = SimulationState()
    for _ in range(compute_step_count(duration, config.timestep)):
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
        expected_response = task.expected_response(stimulus)
        result: TrialResult = task.score_trial(stimulus, observed, reaction_time)
        error_type = (
            result.error_type.value
            if isinstance(result.error_type, ErrorType)
            else str(result.error_type)
        )
        metrics: dict[str, Any] = {
            "reaction_time_s": result.reaction_time_s,
            "correct": result.correct,
            "error_type": error_type,
        }
        try:
            trial_number = int(result.trial_id)
        except (ValueError, TypeError):
            trial_number = None
        trial_result = {
            "trial_id": result.trial_id,
            "trial_number": trial_number,
            "stimulus_type": result.condition,
            "model_response": observed,
            "observed_response": observed,
            "expected_response": expected_response,
            "reaction_time_s": result.reaction_time_s,
            "correct": result.correct,
            "error_type": error_type,
            "condition": result.condition,
            "scenario": str(config.task.get("scenario", task.name)),
            "profile_id": str((config.clinical_profile or {}).get("id", "healthy_v1")),
        }
        trial_result["regional_input"] = dict(stimulus.regional_input)
        for metric_name in (
            "surprise_index",
            "habituation_level",
            "readaptation_latency",
        ):
            if metric_name in stimulus.payload:
                trial_result[metric_name] = stimulus.payload[metric_name]
                metrics[metric_name] = stimulus.payload[metric_name]
        trial_result["metrics"] = metrics
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


# Zachowujemy alias prywatny dla stabilności wewnętrznych testów.
_build_stimulus_sequence_signature = build_stimulus_sequence_signature


def run_experiment(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> dict[str, Any]:
    """Uruchamia pełny eksperyment, analizę oraz opcjonalny zapis wyników.

    Parameters
    ----------
    config:
        Konfiguracja eksperymentu.
    progress_callback:
        Opcjonalna funkcja raportowania postępu symulacji modelu.
    stimulus_sequence:
        Opcjonalna wspólna sekwencja bodźców używana w porównaniach profili
        klinicznych przy tym samym seedzie.

    Returns:
    -------
    dict[str, Any]
        Wyniki symulacji, triali, raportów i opcjonalnego zapisu artefaktów.
    """
    rng_seed = _effective_rng_seed(config)
    random_sources = RandomSources(seed=rng_seed)
    random_sources.get("cognitive_brain_model")
    random_sources.get("task_stimulus_generator")
    random_sources.get("task_response_model")
    random_sources.get("wilson_cowan_oscillator_bank")

    model_params = BrainParams(dt=config.timestep, **config.model)
    osc_params = WilsonCowanParams(**config.integrator.get("oscillator", {}))
    stimulus_scenario = str(config.task.get("scenario", "reward-learning"))
    try:
        model = CognitiveBrainModel(
            params=model_params,
            oscillator_params=osc_params,
            seed=rng_seed,
            stimulus=stimulus_scenario,
        )
    except ValueError:
        model = CognitiveBrainModel(
            params=model_params,
            oscillator_params=osc_params,
            seed=rng_seed,
            stimulus="reward-learning",
        )

    start = pytime.perf_counter()
    time, activity, diagnostics, oscillations, behavior = model.simulate(
        T=float(config.task.get("duration", 45.0)),
        progress_callback=progress_callback,
    )
    elapsed = pytime.perf_counter() - start

    task_stimulus_sequence = (
        list(stimulus_sequence)
        if stimulus_sequence is not None
        else _generate_task_stimuli(config)
    )
    trial_events, trial_results = _simulate_task_trials(
        config, stimulus_sequence=task_stimulus_sequence
    )
    stimulus_sequence_signature = _build_stimulus_sequence_signature(
        task_stimulus_sequence
    )
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
        clinical_profile=config.clinical_profile,
        task_name=str(config.task.get("name") or "n/a"),
    )
    analysis_report = _attach_task_activation_section(analysis_report, task_activation)
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
    if str(config.task.get("name") or "") in {"roving_oddball", "roving-oddball"}:
        analysis_report.payload["roving_oddball"] = build_roving_oddball_report(
            trial_results,
            profile_id=str(
                config.clinical_profile.get("id") or config.output.get("label") or "run"
            ),
            clinical_profile=config.clinical_profile,
            event_timeline=event_timeline,
        )
    randomness = _build_randomness_section(config, random_sources)
    analysis_report.payload["stimulus_sequence_signature"] = stimulus_sequence_signature
    analysis_report.payload["randomness"] = randomness
    analysis_report.payload["clinical_profile"] = dict(config.clinical_profile)
    analysis_report.payload["analysis"] = dict(config.analysis)

    save_info: dict[str, Any] | None = None
    if config.output.get("save_results", False):
        out_dir = build_output_dir(
            config.task.get("scenario", "run"),
            config.output.get("label", "run"),
            root=config.output.get("output_dir", "outputs"),
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
            seed=rng_seed,
            duration_s=elapsed,
            config=config,
            extra_metadata={"randomness": randomness},
            metrics={
                "metrics": analysis_report.payload.get("metrics", {}),
                "comparison": analysis_report.payload.get("comparison", {}),
                "randomness": randomness,
            },
            event_timeline=event_timeline,
        )
        save_info["analysis_report_files"] = report_files

    output_dir = Path(save_info["output_dir"]) if save_info is not None else None
    experiment_result = ExperimentResult(
        config=config,
        signals={
            "model": model,
            "time": time,
            "activity": activity,
            "diagnostics": diagnostics,
            "oscillations": oscillations,
            "behavior": behavior,
        },
        metrics={
            "metrics": analysis_report.payload.get("metrics", {}),
            "comparison": analysis_report.payload.get("comparison", {}),
            "randomness": randomness,
        },
        trial_events=trial_events,
        analysis_report=analysis_report.payload,
        output_dir=output_dir,
        git_info=collect_git_info(REPO_ROOT),
        environment_info=collect_environment_info(),
        trial_results=trial_results,
        trial_report_context={
            "scenario": str(config.task.get("scenario", "run")),
            "task_name": str(config.task.get("name", "stroop")),
            "profile_id": str((config.clinical_profile or {}).get("id", "healthy_v1")),
            "metrics": analysis_report.payload.get("metrics", {}),
        },
        stimulus_sequence_signature=stimulus_sequence_signature,
        event_timeline=event_timeline,
        task_activation=task_activation,
        clinical_profile=dict(config.clinical_profile),
        snn_comparison=snn_comparison,
        save_info=save_info,
        elapsed=elapsed,
        randomness=randomness,
    )
    return experiment_result.to_legacy_dict()


_classify_roving_profile_group = classify_roving_profile_group
_describe_roving_signed_difference = describe_roving_signed_difference
_build_roving_profile_pair_comparisons = build_roving_profile_pair_comparisons
_build_roving_profile_comparison = build_roving_profile_comparison
_summarize_batch_profiles = summarize_batch_profiles
_build_profile_comparison_table = build_profile_comparison_table
_build_batch_educational_comments = build_batch_educational_comments


def apply_clinical_profile_config(
    base_config: ExperimentConfig,
    profile_config: dict[str, Any],
) -> ExperimentConfig:
    """Scal bazową konfigurację zadania z pojedynczym profilem klinicznym."""
    return _apply_clinical_profile_config(base_config, profile_config)


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

    Returns:
    -------
    dict[str, Any]
        Wyniki per profil oraz raport różnic względem profilu referencyjnego.
    """
    return _run_task_across_clinical_profiles(
        base_config,
        clinical_profiles,
        experiment_runner=run_experiment,
        stimulus_generator=_generate_task_stimuli,
        progress_callback=progress_callback,
    )
