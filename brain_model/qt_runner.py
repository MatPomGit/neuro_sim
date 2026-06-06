"""Worker QObject uruchamiający symulacje dla GUI PySide6."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from brain_core.simulation.config_loader import load_config_from_string
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import run_experiment

from .gui_state import GuiState
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .qt_config import load_scenario_yaml_document

RunPayload = tuple[str, str, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]
BatchPayload = tuple[list[dict[str, float | int]], dict[str, Any]]


class SimulationWorker(QObject):
    """Wykonuje symulację poza wątkiem GUI i emituje wyniki przez sygnały Qt."""

    progress = Signal(float)
    done = Signal(object)
    warning = Signal(str)
    error = Signal(str)

    def __init__(self, state: GuiState, parent: Any | None = None) -> None:
        """Utwórz worker QObject z migawką stanu przekazaną przez główne okno."""
        super().__init__(parent)
        self.state = state

    @Slot()
    def run(self) -> None:
        """Uruchom symulację i przekaż wynik lub błąd do wątku GUI."""
        try:
            payload = run_simulation(
                self.state, self._emit_progress, self._emit_warning
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return
        self.done.emit(payload)

    def _emit_progress(self, ratio: float) -> None:
        """Wyemituj postęp przeliczony na zakres procentowy paska Qt."""
        self.progress.emit(max(0.0, min(100.0, ratio * 100.0)))

    def _emit_warning(self, message: str) -> None:
        """Wyemituj ostrzeżenie użytkowe bez przerywania symulacji."""
        self.warning.emit(message)


def run_simulation(
    state: GuiState,
    progress_callback: Any,
    warning_callback: Any,
) -> RunPayload:
    """Wykonaj pojedynczą symulację albo batch przez silnik `brain_core`."""
    T, seed, dt = read_scalar_params(state)
    brain_params = replace(state.brain_params, dt=dt)
    oscillator_params = state.oscillator_params
    validate_parameters(T, dt, brain_params, oscillator_params)

    if state.command == "run":
        result = run_single_experiment(
            state, T, seed, dt, brain_params, oscillator_params, progress_callback
        )
        summary_text = summarize_metrics(
            [extract_metrics(result["diagnostics"], result["behavior"])]
        )
    else:
        runs, result = run_batch(
            state, T, brain_params, oscillator_params, progress_callback
        )
        summary_text = summarize_metrics(runs)
    save_info = result.get("save_info")
    if state.save_results and save_info is None:
        warning_callback("Silnik nie zwrócił informacji o zapisanych wynikach.")

    message = "Symulacja zakończona."
    if save_info:
        message += f" Wyniki zapisane: {save_info['output_dir']}"
    return (
        message,
        summary_text,
        save_info,
        result["model"],
        result["time"],
        result["activity"],
        result["diagnostics"],
        result["oscillations"],
        result["behavior"],
        result.get("event_timeline", []),
        result.get("clinical_profile", {}),
        result.get("analysis_report", {}),
    )


def read_scalar_params(state: GuiState) -> tuple[float, int, float]:
    """Odczytaj i zwaliduj czas, seed oraz krok czasowy ze stanu GUI."""
    try:
        T = float(state.T)
        seed = int(state.seed)
        dt = auto_dt_for_duration(T) if state.auto_dt else float(state.dt)
    except ValueError as exc:
        raise ValueError(
            "Niepoprawny czas symulacji, seed lub krok czasowy dt."
        ) from exc
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
        raise ValueError(
            "Czas symulacji T nie może być mniejszy od kroku czasowego dt."
        )
    if brain_params.noise < 0:
        raise ValueError("noise nie może być ujemny.")
    if oscillator_params.oscillator_noise < 0:
        raise ValueError("oscillator_noise nie może być ujemny.")


def build_engine_config(
    state: GuiState,
    T: float,
    seed: int,
    dt: float,
    brain_params: BrainParams,
    oscillator_params: WilsonCowanParams,
) -> ExperimentConfig:
    """Przekaż wybrany preset YAML do walidacji schematu `brain_core`.

    Parameters
    ----------
    state:
        Migawka stanu GUI z wybraną ścieżką `configs/*.yaml`.
    T:
        Czas pokazany w GUI; zapisany do `task.duration` przed walidacją silnika.
    seed:
        Ziarno losowości z GUI, przepisywane do pól `seed` i `rng_seed`.
    dt:
        Krok czasowy z GUI, przepisywany do `timestep`.
    brain_params:
        Parametry modelu zachowane w sygnaturze workera; preset YAML pozostaje
        źródłem właściwej konfiguracji modelu.
    oscillator_params:
        Parametry oscylatorów zachowane w sygnaturze workera; preset YAML
        pozostaje źródłem właściwej konfiguracji integratora.

    Returns
    -------
    ExperimentConfig
        Konfiguracja zwalidowana wyłącznie przez loader i schemat `brain_core`.

    Raises
    ------
    ValueError
        Gdy stan GUI nie wskazuje pliku konfiguracyjnego scenariusza.
    """
    _ = (brain_params, oscillator_params)
    if not state.scenario_config_path:
        raise ValueError("Wybierz konfigurację YAML scenariusza przed uruchomieniem.")

    raw_config = load_scenario_yaml_document(state.scenario_config_path)
    task_config = raw_config.setdefault("task", {})
    task_config["duration"] = T
    raw_config["timestep"] = dt
    raw_config["seed"] = seed
    raw_config["rng_seed"] = seed
    raw_config.setdefault("output", {})["save_results"] = state.save_results
    return load_config_from_string(
        _dump_json_compatible(raw_config), format_hint="json"
    )


def _dump_json_compatible(config_doc: dict[str, Any]) -> str:
    """Serializuj dokument konfiguracji do JSON bez logiki eksperymentalnej GUI."""
    import json

    return json.dumps(config_doc, ensure_ascii=False)


def run_single_experiment(
    state: GuiState,
    T: float,
    seed: int,
    dt: float,
    brain_params: BrainParams,
    oscillator_params: WilsonCowanParams,
    progress_callback: Any,
) -> dict[str, Any]:
    """Uruchom pojedynczy eksperyment przez warstwę `brain_core`."""
    cfg = build_engine_config(state, T, seed, dt, brain_params, oscillator_params)
    return run_experiment(cfg, progress_callback=progress_callback)


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
        "prediction_error_mean": np.mean(
            [run["prediction_error_mean"] for run in runs]
        ),
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
    state: GuiState,
    T: float,
    base_params: BrainParams,
    oscillator_params: WilsonCowanParams,
    progress_callback: Any,
) -> BatchPayload:
    """Wykonaj serię symulacji, delegując każde uruchomienie do silnika."""
    seeds = [int(value) for value in parse_list(state.batch_seeds)]
    if not seeds:
        raise ValueError("Lista seedów serii (batch_seeds) nie może być pusta.")
    scenarios = parse_list(state.batch_scenarios) or [state.scenario]
    sens_params = parse_list(state.sensitivity_params)
    delta = float(state.sensitivity_delta)
    base_total = len(seeds) * len(scenarios)
    perturb_total = base_total * len(sens_params) * 2
    total_runs = base_total + perturb_total if sens_params else base_total
    completed = 0
    metrics: list[dict[str, float | int]] = []
    last_result: dict[str, Any] | None = None
    for scenario in scenarios:
        for seed in seeds:
            run_state = replace(state, scenario=scenario, seed=str(seed))
            result = run_single_experiment(
                run_state,
                T,
                seed,
                base_params.dt,
                base_params,
                oscillator_params,
                None,
            )
            metrics.append(extract_metrics(result["diagnostics"], result["behavior"]))
            last_result = result
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
                    result = run_single_experiment(
                        run_state,
                        T,
                        seed,
                        perturbed.dt,
                        perturbed,
                        oscillator_params,
                        None,
                    )
                    metrics.append(
                        extract_metrics(result["diagnostics"], result["behavior"])
                    )
                    completed += 1
                    progress_callback(completed / total_runs)
    if last_result is None:
        raise ValueError("Batch nie wygenerował żadnych przebiegów.")
    return metrics, last_result
