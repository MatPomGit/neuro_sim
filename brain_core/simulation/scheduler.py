"""Harmonogram faz symulacji oraz hooki współsymulacyjne."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

from .state import SimulationState


class SimulationModule(Protocol):
    """Interfejs modułu wykonywanego przez harmonogram."""

    def update(self, state: SimulationState, dt: float) -> None:
        """Aktualizuje moduł w ramach pojedynczego kroku harmonogramu."""
        ...


@dataclass(slots=True)
class CoSimulationHook:
    """Punkt rozszerzeń pod co-simulation z różnymi krokami czasowymi."""

    name: str
    module: SimulationModule
    dt: float
    _accumulator: float = 0.0

    def tick(self, state: SimulationState, base_dt: float) -> None:
        """Akumuluje czas bazowy i wywołuje moduł, gdy osiągnięto lokalny krok."""
        self._accumulator += base_dt
        while self._accumulator >= self.dt - 1e-9:
            self.module.update(state, self.dt)
            self._accumulator -= self.dt


@dataclass(slots=True)
class TaskStimulusPlayer:
    """Wstrzykuje bodźce zadania poznawczego do osi czasu metryk."""

    stimuli: list[Any]
    cursor: int = 0

    def __post_init__(self) -> None:
        """Zapewnia kolejność chronologiczną bodźców względem onset."""
        self.stimuli = sorted(self.stimuli, key=lambda stimulus: stimulus.onset_s)

    def update(self, state: SimulationState, dt: float) -> None:
        """Emituje wszystkie bodźce, których czas onset został osiągnięty."""
        del dt
        emitted = state.metrics.setdefault("trial_events", [])
        while (
            self.cursor < len(self.stimuli)
            and self.stimuli[self.cursor].onset_s <= state.time + 1e-9
        ):
            stimulus = self.stimuli[self.cursor]
            regional_input = getattr(stimulus, "regional_input", None)
            if regional_input is None:
                regional_input = stimulus.payload.get("regional_input", {})
            regional_input = dict(regional_input)
            for region, amplitude in regional_input.items():
                state.regions[region] = np.array([float(amplitude)], dtype=float)
            emitted.append(
                {
                    "trial_id": stimulus.trial_id,
                    "onset_s": stimulus.onset_s,
                    "duration_s": stimulus.duration_s,
                    "condition": stimulus.condition,
                    "payload": stimulus.payload,
                    "regional_input": regional_input,
                }
            )
            self.cursor += 1


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
        """Wykonuje pojedynczy krok we wszystkich fazach harmonogramu."""
        self._run_group(self.stimuli, state, dt)
        self._run_group(self.neuronal_dynamics, state, dt)
        self._run_group(self.couplings, state, dt)
        self._run_group(self.physiology, state, dt)

        for hook in self.co_simulation_hooks:
            hook.tick(state, dt)

        self._run_group(self.logging, state, dt)
        state.advance(dt)

    @staticmethod
    def _run_group(
        group: list[SimulationModule], state: SimulationState, dt: float
    ) -> None:
        """Uruchamia wszystkie moduły w jednej fazie."""
        for module in group:
            module.update(state, dt)
