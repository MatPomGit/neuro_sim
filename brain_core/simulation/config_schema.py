"""Schema i walidacja konfiguracji eksperymentu symulacyjnego."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExperimentConfig:
    """
    Ujednolicony obiekt konfiguracji eksperymentu po walidacji.

    Atrybuty:
        model (dict[str, Any]): Konfiguracja modelu.
        integrator (dict[str, Any]): Konfiguracja integratora.
        timestep (float): Krok czasowy symulacji.
        seed (int): Ziarno generatora losowego.
        task (dict[str, Any]): Konfiguracja zadania.
        pathology (dict[str, Any]): Konfiguracja patologii.
        output (dict[str, Any]): Ustawienia wyjścia.
        snn (dict[str, Any]): Konfiguracja SNN.
        analysis (dict[str, Any]): Konfiguracja analiz.
    """

    model: dict[str, Any] = field(default_factory=dict)
    integrator: dict[str, Any] = field(default_factory=lambda: {"method": "euler"})
    timestep: float = 0.005
    seed: int = 7
    task: dict[str, Any] = field(
        default_factory=lambda: {"scenario": "reward-learning", "duration": 45.0}
    )
    pathology: dict[str, Any] = field(
        default_factory=lambda: {"enabled": False, "mutations": [], "scenario": None}
    )
    output: dict[str, Any] = field(
        default_factory=lambda: {
            "save_results": True,
            "label": "run",
            "output_dir": "outputs",
        }
    )
    snn: dict[str, Any] = field(
        default_factory=lambda: {"enabled": False, "circuits": []}
    )
    analysis: dict[str, Any] = field(
        default_factory=lambda: {
            "sets": ["spectral", "phase_locking", "connectivity", "information_flow"]
        }
    )


class ConfigValidationError(ValueError):
    """
    Błąd walidacji konfiguracji eksperymentu.
    """


def validate_config(raw: dict[str, Any]) -> ExperimentConfig:
    """
    Waliduje surową konfigurację i zwraca obiekt `ExperimentConfig`.

    Args:
        raw (dict[str, Any]): Surowa konfiguracja.

    Returns:
        ExperimentConfig: Zweryfikowany obiekt konfiguracji.

    Raises:
        ConfigValidationError: Jeśli konfiguracja jest niepoprawna.
    """
    if not isinstance(raw, dict):
        raise ConfigValidationError("Konfiguracja musi być obiektem mapującym (dict).")

    cfg = ExperimentConfig(
        **{k: v for k, v in raw.items() if k in ExperimentConfig.__dataclass_fields__}
    )

    if cfg.timestep <= 0:
        raise ConfigValidationError("timestep musi być > 0")
    if cfg.seed < 0:
        raise ConfigValidationError("seed musi być >= 0")
    if float(cfg.task.get("duration", 0.0)) <= 0:
        raise ConfigValidationError("task.duration musi być > 0")
    method = str(cfg.integrator.get("method", "euler"))
    if method != "euler":
        raise ConfigValidationError("integrator.method aktualnie wspiera tylko 'euler'")

    if not isinstance(cfg.pathology, dict):
        raise ConfigValidationError("pathology musi być obiektem")
    mutations = cfg.pathology.get("mutations", [])
    if not isinstance(mutations, list):
        raise ConfigValidationError("pathology.mutations musi być listą")
    for idx, mutation in enumerate(mutations):
        if not isinstance(mutation, dict):
            raise ConfigValidationError(f"pathology.mutations[{idx}] musi być obiektem")
        for required_key in ("kind", "scope", "target"):
            if required_key not in mutation:
                raise ConfigValidationError(
                    f"Brak pola pathology.mutations[{idx}].{required_key}"
                )

    _validate_snn_config(cfg)
    _validate_analysis_config(cfg)
    cfg.output["output_dir"] = str(Path(cfg.output.get("output_dir", "outputs")))
    return cfg


def _validate_snn_config(cfg: ExperimentConfig) -> None:
    """Waliduje sekcję konfiguracji współsymulacji SNN."""
    if not isinstance(cfg.snn, dict):
        raise ConfigValidationError("snn musi być obiektem")
    circuits = cfg.snn.get("circuits", [])
    if not isinstance(circuits, list):
        raise ConfigValidationError("snn.circuits musi być listą")
    for idx, circuit in enumerate(circuits):
        if not isinstance(circuit, dict):
            raise ConfigValidationError(f"snn.circuits[{idx}] musi być obiektem")
        if "region" not in circuit:
            raise ConfigValidationError(f"Brak pola snn.circuits[{idx}].region")

    sync_dt_val = cfg.snn.get("sync_dt")
    if sync_dt_val is None:
        sync_dt = cfg.timestep
    else:
        try:
            sync_dt = float(sync_dt_val)
        except (ValueError, TypeError):
            raise ConfigValidationError("snn.sync_dt musi być liczbą")

    if sync_dt <= 0:
        raise ConfigValidationError("snn.sync_dt musi być > 0")
    ratio = sync_dt / cfg.timestep
    if abs(round(ratio) - ratio) > 1e-9:
        raise ConfigValidationError("snn.sync_dt musi być wielokrotnością timestep")
    cfg.snn["sync_dt"] = sync_dt


def _validate_analysis_config(cfg: ExperimentConfig) -> None:
    """Waliduje wybór zestawów analiz uruchamianych po symulacji."""
    if not isinstance(cfg.analysis, dict):
        raise ConfigValidationError("analysis musi być obiektem")
    sets_val = cfg.analysis.get("sets", [])
    if not isinstance(sets_val, list):
        raise ConfigValidationError("analysis.sets musi być listą")
    allowed = {"spectral", "phase_locking", "connectivity", "information_flow"}
    unknown = [name for name in sets_val if name not in allowed]
    if unknown:
        raise ConfigValidationError(f"Nieznane analysis.sets: {unknown}")
