"""Zapis i odczyt konfiguracji GUI PySide6 w formacie JSON."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, TypeVar

import yaml

from brain_core.simulation.config_loader import load_config as load_engine_config
from brain_core.simulation.config_schema import ExperimentConfig

from .gui_forms import APP_VERSION, RULE_FIELDS
from .gui_state import GuiState

TDataclass = TypeVar("TDataclass")
CONFIG_FORMAT = "brain-model-gui-config-v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_YAML_PRESETS: tuple[tuple[str, Path], ...] = (
    ("Roving oddball — zdrowy", Path("configs/roving_oddball_healthy.yaml")),
    (
        "Roving oddball — zaburzenie GABA",
        Path("configs/roving_oddball_disorder_gaba.yaml"),
    ),
    (
        "Roving oddball — lezja hipokampa",
        Path("configs/roving_oddball_lesion_hippocampus.yaml"),
    ),
    ("SNN — demo hipokampa", Path("configs/snn_hippocampus_demo.yaml")),
)

SCENARIO_YAML_DESCRIPTIONS: dict[str, str] = {
    "Roving oddball — zdrowy": (
        "Profil referencyjny bez patologii. Wybierz go, aby zobaczyć bazową "
        "identyfikację standardów, dewiantów, habituacji i readaptacji."
    ),
    "Roving oddball — zaburzenie GABA": (
        "Ten wariant modeluje profil z obniżoną inhibicją GABA i służy do "
        "porównania, jak większy szum oraz niestabilność kontroli przedczołowej "
        "zmieniają odpowiedź na dewiant."
    ),
    "Roving oddball — lezja hipokampa": (
        "Ten wariant modeluje skutki uszkodzenia hipokampa i pokazuje, jak słabsza "
        "integracja epizodyczna wpływa na wykrywanie nowości oraz readaptację."
    ),
    "SNN — demo hipokampa": (
        "Demo sprzężenia lokalnego obwodu SNN regionu HIP z modelem masowym; "
        "użyj go do sprawdzenia zamkniętej pętli hipokampa zamiast lekcji roving oddball."
    ),
}


def editable_dataclass_values(
    instance: Any, exclude: set[str] | None = None
) -> dict[str, Any]:
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


def scenario_yaml_preset_labels() -> list[str]:
    """Zwróć polskie etykiety gotowych konfiguracji YAML dostępnych w GUI."""
    return [label for label, _path in SCENARIO_YAML_PRESETS]


def scenario_yaml_description_for_label(label: str) -> str:
    """Zwróć polski opis konfiguracji YAML widoczny w szybkim starcie GUI.

    Parameters
    ----------
    label:
        Etykieta konfiguracji YAML wybrana przez użytkownika w GUI.

    Returns
    -------
    str
        Krótki opis celu dydaktycznego i różnic względem pozostałych presetów.
    """

    return SCENARIO_YAML_DESCRIPTIONS.get(
        label,
        "Własna konfiguracja YAML; sprawdź pola task, pathology i clinical_profile.",
    )


def default_scenario_yaml_path() -> str:
    """Zwróć domyślną konfigurację YAML wybieraną w szybkim starcie GUI."""
    return str(SCENARIO_YAML_PRESETS[0][1])


def label_for_scenario_yaml_path(path: str | Path) -> str:
    """Dopasuj ścieżkę konfiguracji YAML do etykiety prezentowanej użytkownikowi."""
    normalized = Path(path)
    for label, preset_path in SCENARIO_YAML_PRESETS:
        if normalized == preset_path or normalized == REPO_ROOT / preset_path:
            return label
    return str(path)


def scenario_yaml_path_for_label(label: str) -> Path:
    """Zwróć ścieżkę repozytoryjną konfiguracji YAML wskazanej etykietą GUI."""
    for preset_label, preset_path in SCENARIO_YAML_PRESETS:
        if label == preset_label:
            return preset_path
    candidate = Path(label)
    if candidate.suffix in {".yaml", ".yml"}:
        return candidate
    raise ValueError(f"Nieznana konfiguracja YAML scenariusza: {label}")


def resolve_repo_path(path: str | Path) -> Path:
    """Zamień ścieżkę względną z konfiguracji GUI na ścieżkę względem repozytorium."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def load_scenario_yaml_config(path: str | Path) -> ExperimentConfig:
    """Wczytaj i zwaliduj konfigurację YAML scenariusza przez loader silnika."""
    return load_engine_config(resolve_repo_path(path))


def load_scenario_yaml_document(path: str | Path) -> dict[str, Any]:
    """Wczytaj surowy dokument YAML scenariusza do podglądu lub zapisu stanu GUI."""
    config_path = resolve_repo_path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def state_to_config(state: GuiState) -> dict[str, Any]:
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
        "scenario_config_path": state.scenario_config_path,
        "save_results": state.save_results,
        "brain_params": {
            **editable_dataclass_values(state.brain_params, exclude=set(RULE_FIELDS)),
            "dt": state.dt,
        },
        "oscillator_params": editable_dataclass_values(state.oscillator_params),
        "plots": dict(state.plots),
    }


def apply_config_to_state(state: GuiState, config: dict[str, Any]) -> GuiState:
    """Zastosuj słownik konfiguracji do istniejącego stanu GUI i zwróć ten stan."""
    state.T = str(config.get("T", state.T))
    state.dt = str(config.get("dt", state.dt))
    state.auto_dt = bool(config.get("auto_dt", state.auto_dt))
    state.seed = str(config.get("seed", state.seed))
    state.command = str(config.get("command", state.command))
    state.batch_seeds = str(config.get("batch_seeds", state.batch_seeds))
    state.batch_scenarios = str(config.get("batch_scenarios", state.batch_scenarios))
    state.sensitivity_params = str(
        config.get("sensitivity_params", state.sensitivity_params)
    )
    state.sensitivity_delta = str(
        config.get("sensitivity_delta", state.sensitivity_delta)
    )
    state.scenario = str(config.get("scenario", state.scenario))
    state.scenario_config_path = str(
        config.get("scenario_config_path", state.scenario_config_path)
    )
    state.save_results = bool(config.get("save_results", state.save_results))
    state.brain_params = dataclass_with_updates(
        state.brain_params, config.get("brain_params", {})
    )
    state.oscillator_params = dataclass_with_updates(
        state.oscillator_params, config.get("oscillator_params", {})
    )
    plots_config = config.get("plots")
    if isinstance(plots_config, dict):
        state.plots = {str(name): bool(value) for name, value in plots_config.items()}
    return state


def save_config(path: Path, state: GuiState) -> None:
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
