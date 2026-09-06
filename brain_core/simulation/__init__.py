"""
Narzędzia warstwy symulacji `brain_core`.

Moduł eksportuje publiczne klasy i protokoły używane do:
- uruchamiania eksperymentów przez typowane API,
- zarządzania stanem symulacji,
- harmonogramowania kroków czasowych,
- współsymulacji wieloskalowej,
- integracji numerycznej,
- zarządzania źródłami losowości.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .events import SimulationEvent, build_event_timeline
from .integrators import (
    INTEGRATOR_REGISTRY,
    BaseIntegrator,
    EulerMaruyamaIntegrator,
    IntegratorRegistryEntry,
    RK4Integrator,
)
from .multiscale_engine import ClosedLoopFeedbackPath, MultiScaleEngine, TimeScaleTask
from .random_sources import RandomSources
from .results import ExperimentResult
from .scheduler import CoSimulationHook, SimulationModule, SimulationScheduler
from .state import SimulationState
from .timebase import (
    TIMEBASE_RELATIVE_TOLERANCE,
    TimeAccumulator,
    compute_step_count,
    compute_time_stride,
    is_time_multiple,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from brain_core.experiments.protocols import TrialStimulus

    from .config_schema import ExperimentConfig


def run_experiment(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> ExperimentResult:
    """Uruchom eksperyment przez leniwie ładowane publiczne API."""
    from .api import run_experiment as _run_experiment

    return _run_experiment(
        config,
        progress_callback=progress_callback,
        stimulus_sequence=stimulus_sequence,
    )


def run_experiment_legacy(
    config: ExperimentConfig,
    progress_callback: Callable[[float], None] | None = None,
    stimulus_sequence: list[TrialStimulus] | None = None,
) -> dict[str, Any]:
    """Uruchom eksperyment przez jawny adapter zgodności z API słownikowym."""
    from .api import run_experiment_legacy as _run_experiment_legacy

    return _run_experiment_legacy(
        config,
        progress_callback=progress_callback,
        stimulus_sequence=stimulus_sequence,
    )


__all__: list[str] = [
    "run_experiment",
    "run_experiment_legacy",
    "ExperimentResult",
    "SimulationEvent",
    "build_event_timeline",
    "SimulationState",
    "SimulationScheduler",
    "MultiScaleEngine",
    "ClosedLoopFeedbackPath",
    "TimeScaleTask",
    "TimeAccumulator",
    "TIMEBASE_RELATIVE_TOLERANCE",
    "is_time_multiple",
    "compute_step_count",
    "compute_time_stride",
    "SimulationModule",
    "CoSimulationHook",
    "BaseIntegrator",
    "IntegratorRegistryEntry",
    "INTEGRATOR_REGISTRY",
    "EulerMaruyamaIntegrator",
    "RK4Integrator",
    "RandomSources",
]
