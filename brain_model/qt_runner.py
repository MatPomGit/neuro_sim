"""Worker QThread uruchamiający symulacje dla GUI PySide6."""

from __future__ import annotations

import json
import time as pytime
from dataclasses import replace
from typing import Any

import numpy as np
from PySide6.QtCore import QThread, Signal

from brain_core.simulation.config_loader import load_config_from_string
from brain_core.simulation.engine import run_experiment

from .io import build_output_dir, save_run
from .model import CognitiveBrainModel
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .qt_state import QtGuiState

RunPayload = tuple[str, str, Any, Any, Any, Any, Any, Any, Any]
BatchPayload = tuple[list[dict[str, float | int]], Any, Any, Any, Any, Any, Any]


class SimulationWorker(QThread):
    """Wykonuje symulację poza wątkiem GUI i emituje wyniki przez sygnały Qt."""

    progress_changed = Signal(float)
    warning_reported = Signal(str)
    error_reported = Signal(str)
    result_ready = Signal(object)

    def __init__(self, state: QtGuiState, parent: Any | None = None) -> None:
        """Utwórz worker z migawką stanu przekazaną przez główne okno."""
        super().__init__(parent)
        self.state = state

    def run(self) -> None:
        """Uruchom symulację i przekaż wynik lub błąd do wątku GUI."""
        try:
            payload = run_simulation(self.state, self._emit_progress, self._emit_warning)
        except Exception as exc:
            self.error_reported.emit(str(exc))
            return
        self.result_ready.emit(payload)

    def _emit_progress(self, ratio: float) -> None:
        """Wyemituj postęp przeliczony na zakres procentowy paska Qt."""
        self.progress_changed.emit(max(0.0, min(100.0, ratio * 100.0)))

    def _emit_warning(self, message: str) -> None:
        """Wyemituj ostrzeżenie użytkowe bez przerywania symulacji."""
        self.warning_reported.emit(message)


def run_simulation(
    state: QtGuiState,
    progress_callback: Any,
    warning_callback: Any,
) -> RunPayload:
    """Wykonaj pojedynczą symulację albo batch na podstawie stanu GUI."""
    T, seed, dt = read_scalar_params(state)
    brain_params = replace(state.brain_params, dt=dt)
    oscillator_params = state.oscillator_params
    validate_parameters(T, dt, brain_params, oscillator_params)

    start = pytime.perf_counter()
    if state.command == "run":
        model, time, activity, diagnostics, oscillations, behavior = run_single_experiment(
            state, T, seed, dt, brain_params, oscillator_params, progress_callback
        )
        summary_text = summarize_metrics([extract_metrics(diagnostics, behavior)])
    else:
        runs, model, time, activity, diagnostics, oscillations, behavior = run_batch(
            state, T, brain_params, oscillator_params, progress_callback
        )
        summary_text = summarize_metrics(runs)
    elapsed = pytime.perf_counter() - start

    save_info = None
    if state.save_results:
        save_info = save_results_if_requested(
            state,
            seed,
            elapsed,
            model,
            time,
            activity,
            diagnostics,
            oscillations,
            behavior,
            warning_callback,
        )

    message = "Symulacja zakończona."
    if save_info:
        message += f" Wyniki zapisane: {save_info['output_dir']}"
    return (
        message,
        summary_text,
        save_info,
        model,
        time,
        activity,
        diagnostics,
        oscillations,
        behavior,
    )


def read_scalar_params(state: QtGuiState) -> tuple[float, int, float]:
    """Odczytaj i zwaliduj czas, seed oraz krok czasowy ze stanu GUI."""
    try:
        T = float(state.T)
        seed = int(state.seed)
        dt = auto_dt_for_duration(T) if state.auto_dt else float(state.dt)
    except ValueError as exc:
        raise ValueError("Niepoprawny czas symulacji, seed lub krok czasowy dt.") from exc
    return T, seed, dt


def auto_dt_for_duration(duration: float) -> float:
    """Dobierz prosty krok czasowy dla podanego czasu symulacji."""
    if duration <= 15.0:
        return 0.01
    if duration <= 60.0:
        return 0.02
    return 0.05


def validate_parameters(
    T: float,
    dt: float,
    brain_params: BrainParams,
    oscillator_params: WilsonCowanParams,
) -> None:
    """Sprawdź podstawowe ograniczenia parametrów przed uruchomieniem obliczeń."""
    if T <= 0:
        raise ValueError("Czas symulacji T musi być większy od zera.")
    if dt <= 0:
        raise ValueError("Krok czasowy dt musi być większy od zera.")
    if T < dt:
        raise ValueError("Czas symulacji T nie może być mniejszy od kroku czasowego dt.")
    if brain_params.noise < 0:
        raise ValueError("noise nie może być ujemny.")
    if oscillator_params.oscillator_noise < 0:
        raise ValueError("oscillator_noise nie może być ujemny.")


def run_single_experiment(
    state: QtGuiState,
    T: float,
    seed: int,
    dt: float,
    brain_params: BrainParams,
    oscillator_params: WilsonCowanParams,
    progress_callback: Any,
) -> tuple[Any, Any, Any, Any, Any, Any]:
    """Uruchom pojedynczy eksperyment przez warstwę `brain_core`."""
    config_doc = {
        "model": {
            "noise": brain_params.noise,
            "gw_threshold": brain_params.gw_threshold,
            "gw_gain": brain_params.gw_gain,
        },
        "integrator": {
            "method": "euler",
            "oscillator": {
                "cognitive_drive_gain": oscillator_params.cognitive_drive_gain,
                "oscillator_noise": oscillator_params.oscillator_noise,
            },
        },
        "timestep": dt,
        "seed": seed,
        "task": {"scenario": state.scenario, "duration": T},
        "output": {"save_results": False, "label": "gui", "output_dir": "outputs"},
    }
    cfg = load_config_from_string(json.dumps(config_doc), format_hint="json")
    result = run_experiment(cfg, progress_callback=progress_callback)
    return (
        result["model"],
        result["time"],
        result["activity"],
        result["diagnostics"],
        result["oscillations"],
        result["behavior"],
    )


def save_results_if_requested(
    state: QtGuiState,
    seed: int,
    elapsed: float,
    model: Any,
    time: Any,
    activity: Any,
    diagnostics: Any,
    oscillations: Any,
    behavior: Any,
    warning_callback: Any,
) -> Any:
    """Zapisz wyniki symulacji, a problem raportuj jako ostrzeżenie użytkowe."""
    try:
        out_dir = build_output_dir(state.scenario, "gui")
        return save_run(
            out_dir,
            time,
            activity,
            diagnostics,
            oscillations,
            extra_metadata={
                "behavior": {
                    "decision": [str(value) for value in behavior["decision"]],
                    "latency": behavior["latency"].tolist(),
                    "confidence": behavior["confidence"].tolist(),
                    "decision_score": behavior["decision_score"].tolist(),
                    "decision_event": behavior["decision_event"].astype(int).tolist(),
                }
            },
            model_params=model.p,
            oscillator_params=model.oscillator_bank.params,
            scenario=oscillations.get("metadata"),
            seed=seed,
            duration_s=elapsed,
        )
    except Exception as exc:
        warning_callback(f"Nie udało się zapisać wyników symulacji: {exc}")
        return None


def extract_metrics(
    diagnostics: dict[str, Any], behavior: dict[str, Any]
) -> dict[str, float | int]:
    """Wylicz podstawowe metryki diagnostyczne i behawioralne."""
    return {
        "prediction_error_mean": float(np.mean(diagnostics["prediction_error"])),
        "gw_ignition_mean": float(np.mean(diagnostics["gw_ignition"])),
        "confidence_mean": float(np.mean(behavior["confidence"])),
        "decision_events": int(np.sum(behavior["decision_event"])),
    }


def summarize_metrics(runs: list[dict[str, float | int]]) -> str:
    """Zbuduj tekstowe podsumowanie średnich metryk uruchomień."""
    agg = {
        "prediction_error_mean": np.mean([run["prediction_error_mean"] for run in runs]),
        "gw_ignition_mean": np.mean([run["gw_ignition_mean"] for run in runs]),
        "confidence_mean": np.mean([run["confidence_mean"] for run in runs]),
        "decision_events": np.mean([run["decision_events"] for run in runs]),
    }
    return (
        "Podsumowanie metryk:\n"
        f"średni błąd predykcji={agg['prediction_error_mean']:.4f}, "
        f"średni zapłon globalnej przestrzeni roboczej={agg['gw_ignition_mean']:.4f}, "
        f"średnia pewność={agg['confidence_mean']:.4f}, "
        f"średnie zdarzenia decyzyjne={agg['decision_events']:.2f}"
    )


def parse_list(raw: str) -> list[str]:
    """Podziel tekst z listą rozdzielaną przecinkami na wartości."""
    return [part.strip() for part in raw.split(",") if part.strip()]


def run_batch(
    state: QtGuiState,
    T: float,
    base_params: BrainParams,
    oscillator_params: WilsonCowanParams,
    progress_callback: Any,
) -> BatchPayload:
    """Wykonaj serię symulacji dla seedów, scenariuszy i perturbacji."""
    seeds = [int(value) for value in parse_list(state.batch_seeds)]
    scenarios = parse_list(state.batch_scenarios) or [state.scenario]
    sens_params = parse_list(state.sensitivity_params)
    delta = float(state.sensitivity_delta)
    base_total = len(seeds) * len(scenarios)
    perturb_total = base_total * len(sens_params) * 2
    total_runs = base_total + perturb_total if sens_params else base_total
    completed = 0
    metrics: list[dict[str, float | int]] = []
    last: tuple[Any, Any, Any, Any, Any, Any] | None = None
    for scenario in scenarios:
        for seed in seeds:
            model = CognitiveBrainModel(
                params=base_params,
                oscillator_params=oscillator_params,
                seed=seed,
                stimulus=scenario,
            )
            time, activity, diagnostics, oscillations, behavior = model.simulate(T=T)
            metrics.append(extract_metrics(diagnostics, behavior))
            last = model, time, activity, diagnostics, oscillations, behavior
            completed += 1
            progress_callback(completed / total_runs)
            for parameter_name in sens_params:
                if not hasattr(base_params, parameter_name):
                    continue
                base_value = getattr(base_params, parameter_name)
                for sign in (-1.0, 1.0):
                    perturbed = replace(
                        base_params,
                        **{parameter_name: base_value * (1.0 + sign * delta)},
                    )
                    model = CognitiveBrainModel(
                        params=perturbed,
                        oscillator_params=oscillator_params,
                        seed=seed,
                        stimulus=scenario,
                    )
                    _, _, diag_p, _, beh_p = model.simulate(T=T)
                    metrics.append(extract_metrics(diag_p, beh_p))
                    completed += 1
                    progress_callback(completed / total_runs)
    if last is None:
        raise ValueError("Batch nie wygenerował żadnych przebiegów.")
    return metrics, *last
