
"""
Narzędzia warstwy symulacji `brain_core`.

Moduł eksportuje publiczne klasy i protokoły używane do:
- zarządzania stanem symulacji,
- harmonogramowania kroków czasowych,
- współsymulacji wieloskalowej,
- integracji numerycznej,
- zarządzania źródłami losowości.
"""

from .integrators import BaseIntegrator, EulerMaruyamaIntegrator, RK4Integrator
from .multiscale_engine import MultiScaleEngine, TimeScaleTask
from .random_sources import RandomSources
from .scheduler import CoSimulationHook, SimulationModule, SimulationScheduler
from .state import SimulationState

__all__: list[str] = [
    "SimulationState",
    "SimulationScheduler",
    "MultiScaleEngine",
    "TimeScaleTask",
    "SimulationModule",
    "CoSimulationHook",
    "BaseIntegrator",
    "EulerMaruyamaIntegrator",
    "RK4Integrator",
    "RandomSources",
]
