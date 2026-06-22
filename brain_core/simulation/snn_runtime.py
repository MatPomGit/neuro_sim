"""Wykonanie i raportowanie demonstracyjnego sprzężenia SNN."""

from __future__ import annotations

from typing import Any

import numpy as np

from brain_core.populations.spiking_population import Brian2SpikingPopulationAdapter
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from .config_schema import ExperimentConfig
from .signal_adapter import CouplingSignalAdapter, SNNPopulationMapping

SNN_METRIC_DISCLAIMER_PL = (
    "metryka demonstracyjna SNN; służy do kontroli kontraktu HIP, "
    "a nie do interpretacji biologicznej"
)
SNN_FEEDBACK_NOTICE_LIMIT = 0.20
SNN_FEEDBACK_WARNING_LIMIT = 0.30


def build_snn_runtime(
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


def summarize_trace_metrics(
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


def classify_snn_feedback_amplitude(
    max_feedback_amplitude: float,
) -> dict[str, str | float]:
    """Klasyfikuje ostrzeżenie dla amplitudy sprzężenia SNN.

    Parameters
    ----------
    max_feedback_amplitude:
        Skonfigurowany limit bezwymiarowej amplitudy sprzężenia closed-loop.

    Returns
    -------
    dict[str, str | float]
        Poziom ostrzeżenia, progi i krótki opis po polsku.
    """
    if max_feedback_amplitude >= SNN_FEEDBACK_WARNING_LIMIT:
        level = "warning"
        message = (
            "max_feedback_amplitude jest wysokie dla demonstracyjnego closed-loop; "
            "wynik traktuj wyłącznie jako test stabilności kontraktu HIP."
        )
    elif max_feedback_amplitude >= SNN_FEEDBACK_NOTICE_LIMIT:
        level = "notice"
        message = (
            "max_feedback_amplitude przekracza próg informacyjny; porównaj "
            "metryki report_only_snn i closed_loop_snn przed interpretacją."
        )
    else:
        level = "ok"
        message = (
            "max_feedback_amplitude mieści się poniżej progów ostrzegawczych demo."
        )
    return {
        "level": level,
        "notice_limit": SNN_FEEDBACK_NOTICE_LIMIT,
        "warning_limit": SNN_FEEDBACK_WARNING_LIMIT,
        "message_pl": message,
    }


def simulate_closed_loop_snn_activity(
    *,
    config: ExperimentConfig,
    region_names: list[str],
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """Uruchamia wariant, w którym SNN modyfikuje wejście HIP w kolejnym kroku."""
    _, _, adapter, snn_population, _, gains = build_snn_runtime(
        config=config,
        region_names=region_names,
    )
    sync_stride = max(1, int(round(float(config.snn["sync_dt"]) / config.timestep)))
    max_feedback_amplitude = float(config.snn.get("max_feedback_amplitude", 0.15))
    pending_drive = np.zeros(len(region_names), dtype=float)
    applied_drives: list[np.ndarray] = []
    snn_updates = 0

    def external_drive_callback(
        step_index: int,
        _time_s: float,
        cognitive_activity: np.ndarray,
        excitatory_activity: np.ndarray,
        inhibitory_activity: np.ndarray,
    ) -> np.ndarray:
        """Zwraca opóźnione wejście SNN i kolejkuje sygnał na następny krok."""
        nonlocal pending_drive, snn_updates
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
            snn_updates += 1
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
    cost = {
        "model_runs": 1,
        "simulated_steps": int(closed_loop_activity.shape[0]),
        "snn_updates": int(snn_updates),
        "feedback_applications": int(feedback.shape[0]),
    }
    return closed_loop_activity, feedback, cost


def run_local_snn_comparison(
    *,
    config: ExperimentConfig,
    region_names: list[str],
    activity: np.ndarray,
    oscillations: dict[str, Any],
) -> dict[str, Any] | None:
    """Porównuje baseline oraz faktycznie policzone warianty SNN."""
    if not bool(config.snn.get("enabled", False)):
        return None

    circuits = config.snn.get("circuits", [])
    if not circuits:
        return None

    snn_regions, _, adapter, snn_population, mapped_indices, gains = build_snn_runtime(
        config=config, region_names=region_names
    )

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
    report_only_snn_updates = 0

    for step_index in range(activity.shape[0]):
        if step_index % sync_stride == 0:
            signal = adapter.rate_to_spike_drive(
                excitatory_rate_hz=excitatory[step_index] * adapter.MAX_FIRING_RATE_HZ,
                inhibitory_rate_hz=inhibitory[step_index] * adapter.MAX_FIRING_RATE_HZ,
            )
            report_only_snn_updates += 1
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

    closed_loop_activity, feedback_drive, closed_loop_cost = (
        simulate_closed_loop_snn_activity(
            config=config,
            region_names=region_names,
        )
    )
    if closed_loop_activity.shape != activity.shape:
        raise ValueError("Przebieg closed_loop_snn nie pasuje do baseline")
    if feedback_drive.shape != activity.shape:
        raise ValueError("Sygnał sprzężenia closed_loop_snn nie pasuje do baseline")

    mode_costs = {
        "baseline": {
            "model_runs": 0,
            "simulated_steps": int(activity.shape[0]),
            "snn_updates": 0,
            "feedback_applications": 0,
        },
        "report_only_snn": {
            "model_runs": 0,
            "simulated_steps": int(activity.shape[0]),
            "snn_updates": int(report_only_snn_updates),
            "feedback_applications": 0,
        },
        "closed_loop_snn": closed_loop_cost,
    }

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
        mode_metrics["report_only_snn"][region] = summarize_trace_metrics(
            baseline_trace=baseline_trace,
            compared_trace=report_only_trace,
        )
        mode_metrics["closed_loop_snn"][region] = summarize_trace_metrics(
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
        "status_pl": "włączony demonstracyjny obwód SNN hipokampa",
        "comparison_scope_pl": (
            "SNN jest raportowany jako deterministyczne porównanie "
            "demonstracyjne lokalnego obwodu HIP, a nie jako pełny model "
            "biologiczny."
        ),
        "comparison_note_pl": (
            "closed_loop_snn jest dodatkowym wariantem porównawczym liczonym "
            "obok baseline i report_only_snn."
        ),
        "regions": list(snn_regions),
        "neural_mass_regions": list(region_names),
        "requested_mode": requested_mode,
        "computed_modes": computed_modes,
        "sync_dt_s": float(config.snn["sync_dt"]),
        "max_feedback_amplitude": float(config.snn.get("max_feedback_amplitude", 0.15)),
        "max_feedback_amplitude_warning": classify_snn_feedback_amplitude(
            float(config.snn.get("max_feedback_amplitude", 0.15))
        ),
        "input_rate_unit": str(config.snn.get("input_rate_unit", "Hz")),
        "output_activity_unit": str(config.snn.get("output_activity_unit", "fraction")),
        "backend": str(circuits[0].get("backend", "brian2")),
        "metric_disclaimer_pl": SNN_METRIC_DISCLAIMER_PL,
        "mode_costs": mode_costs,
        "mode_metrics": mode_metrics,
        "region_differences": region_differences,
    }
