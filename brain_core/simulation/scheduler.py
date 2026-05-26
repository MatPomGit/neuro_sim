from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .state import SimulationState


class SimulationModule(Protocol):
    def update(self, state: SimulationState, dt: float) -> None: ...


@dataclass(slots=True)
class CoSimulationHook:
    """Punkt rozszerzeń pod co-simulation z różnymi krokami czasowymi."""

    name: str
    module: SimulationModule
    dt: float
    _accumulator: float = 0.0

    def tick(self, state: SimulationState, base_dt: float) -> None:
        self._accumulator += base_dt
        while self._accumulator >= self.dt:
            self.module.update(state, self.dt)
            self._accumulator -= self.dt


@dataclass(slots=True)
class SimulationScheduler:
    """Wykonuje krok symulacji w ustalonej kolejności faz."""

    stimuli: list[SimulationModule] = field(default_factory=list)
    neuronal_dynamics: list[SimulationModule] = field(default_factory=list)
    couplings: list[SimulationModule] = field(default_factory=list)
    physiology: list[SimulationModule] = field(default_factory=list)
    logging: list[SimulationModule] = field(default_factory=list)
    co_simulation_hooks: list[CoSimulationHook] = field(default_factory=list)

    def run_step(self, state: SimulationState, dt: float) -> None:
        self._run_group(self.stimuli, state, dt)
        self._run_group(self.neuronal_dynamics, state, dt)
        self._run_group(self.couplings, state, dt)
        self._run_group(self.physiology, state, dt)

        for hook in self.co_simulation_hooks:
            hook.tick(state, dt)

        self._run_group(self.logging, state, dt)
        state.advance(dt)

    @staticmethod
    def _run_group(group: list[SimulationModule], state: SimulationState, dt: float) -> None:
        for module in group:
            module.update(state, dt)
