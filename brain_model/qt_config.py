"""Zapis i odczyt konfiguracji GUI PySide6 w formacie JSON."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, TypeVar

from .gui_forms import APP_VERSION, RULE_FIELDS
from .qt_state import QtGuiState

TDataclass = TypeVar("TDataclass")
CONFIG_FORMAT = "brain-model-gui-config-v1"


def editable_dataclass_values(instance: Any, exclude: set[str] | None = None) -> dict[str, Any]:
    """Zwróć wartości pól dataclass z opcjonalnym pominięciem pól technicznych."""
    if not is_dataclass(instance):
        raise TypeError("Oczekiwano instancji dataclass.")
    skipped = exclude or set()
    return {
        field.name: getattr(instance, field.name)
        for field in fields(instance)
        if field.name not in skipped
    }


def dataclass_with_updates(instance: TDataclass, updates: Any) -> TDataclass:
    """Zbuduj kopię dataclass z bezpiecznie przepisanymi wartościami z konfiguracji."""
    if not isinstance(updates, dict):
        return instance
    converted: dict[str, Any] = {}
    for field in fields(instance):
        if field.name not in updates:
            continue
        value = updates[field.name]
        if field.type is bool:
            converted[field.name] = bool(value)
        elif field.type is int:
            converted[field.name] = int(value)
        elif field.type is float:
            converted[field.name] = float(value)
        else:
            converted[field.name] = value
    return replace(instance, **converted)


def state_to_config(state: QtGuiState) -> dict[str, Any]:
    """Zamień stan GUI PySide6 na słownik kompatybilny z dotychczasowym JSON."""
    return {
        "T": state.T,
        "dt": state.dt,
        "auto_dt": state.auto_dt,
        "seed": state.seed,
        "command": state.command,
        "batch_seeds": state.batch_seeds,
        "batch_scenarios": state.batch_scenarios,
        "sensitivity_params": state.sensitivity_params,
        "sensitivity_delta": state.sensitivity_delta,
        "scenario": state.scenario,
        "save_results": state.save_results,
        "brain_params": {
            **editable_dataclass_values(state.brain_params, exclude=set(RULE_FIELDS)),
            "dt": state.dt,
        },
        "oscillator_params": editable_dataclass_values(state.oscillator_params),
        "plots": dict(state.plots),
    }


def apply_config_to_state(state: QtGuiState, config: dict[str, Any]) -> QtGuiState:
    """Zastosuj słownik konfiguracji do istniejącego stanu GUI i zwróć ten stan."""
    state.T = str(config.get("T", state.T))
    state.dt = str(config.get("dt", state.dt))
    state.auto_dt = bool(config.get("auto_dt", state.auto_dt))
    state.seed = str(config.get("seed", state.seed))
    state.command = str(config.get("command", state.command))
    state.batch_seeds = str(config.get("batch_seeds", state.batch_seeds))
    state.batch_scenarios = str(config.get("batch_scenarios", state.batch_scenarios))
    state.sensitivity_params = str(config.get("sensitivity_params", state.sensitivity_params))
    state.sensitivity_delta = str(config.get("sensitivity_delta", state.sensitivity_delta))
    state.scenario = str(config.get("scenario", state.scenario))
    state.save_results = bool(config.get("save_results", state.save_results))
    state.brain_params = dataclass_with_updates(state.brain_params, config.get("brain_params", {}))
    state.oscillator_params = dataclass_with_updates(
        state.oscillator_params, config.get("oscillator_params", {})
    )
    state.plots = {
        str(name): bool(value) for name, value in dict(config.get("plots", state.plots)).items()
    }
    return state


def save_config(path: Path, state: QtGuiState) -> None:
    """Zapisz konfigurację GUI do pliku JSON z metadanymi aplikacji."""
    payload = {
        "format": CONFIG_FORMAT,
        "app_version": APP_VERSION,
        "saved_date": date.today().isoformat(),
        "config": state_to_config(state),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: Path) -> dict[str, Any]:
    """Wczytaj konfigurację GUI z pliku JSON i zwróć właściwą sekcję ustawień."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    config = payload.get("config", payload)
    if not isinstance(config, dict):
        raise ValueError("Plik konfiguracji nie zawiera poprawnego obiektu JSON.")
    return config


def default_config_filename() -> str:
    """Zwróć domyślną nazwę pliku konfiguracji z aktualną datą."""
    return f"neuro_sim_gui_{date.today().isoformat()}.json"
