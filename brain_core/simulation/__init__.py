"""
Narzędzia warstwy symulacji `brain_core`.

Moduł eksportuje publiczne klasy i protokoły używane do:
- zarządzania stanem symulacji,
- harmonogramowania kroków czasowych,
- współsymulacji wieloskalowej,
- integracji numerycznej,
- zarządzania źródłami losowości.
"""

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
from .scheduler import CoSimulationHook, SimulationModule, SimulationScheduler
from .state import SimulationState
from .timebase import (
    TIMEBASE_RELATIVE_TOLERANCE,
    TimeAccumulator,
    compute_step_count,
    compute_time_stride,
    is_time_multiple,
)

__all__: list[str] = [
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
