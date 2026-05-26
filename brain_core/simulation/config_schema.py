from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class ExperimentConfig:
    model: Dict[str, Any] = field(default_factory=dict)
    integrator: Dict[str, Any] = field(default_factory=lambda: {"method": "euler"})
    timestep: float = 0.005
    seed: int = 7
    task: Dict[str, Any] = field(default_factory=lambda: {"scenario": "reward-learning", "duration": 45.0})
    output: Dict[str, Any] = field(default_factory=lambda: {"save_results": True, "label": "run", "output_dir": "outputs"})


class ConfigValidationError(ValueError):
    pass


def validate_config(raw: Dict[str, Any]) -> ExperimentConfig:
    if not isinstance(raw, dict):
        raise ConfigValidationError("Konfiguracja musi być obiektem mapującym (dict).")

    cfg = ExperimentConfig(**{k: v for k, v in raw.items() if k in ExperimentConfig.__dataclass_fields__})

    if cfg.timestep <= 0:
        raise ConfigValidationError("timestep musi być > 0")
    if cfg.seed < 0:
        raise ConfigValidationError("seed musi być >= 0")
    if float(cfg.task.get("duration", 0.0)) <= 0:
        raise ConfigValidationError("task.duration musi być > 0")
    method = str(cfg.integrator.get("method", "euler"))
    if method != "euler":
        raise ConfigValidationError("integrator.method aktualnie wspiera tylko 'euler'")

    cfg.output["output_dir"] = str(Path(cfg.output.get("output_dir", "outputs")))
    return cfg
