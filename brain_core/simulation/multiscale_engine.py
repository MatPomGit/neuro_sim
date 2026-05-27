from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .state import SimulationState


class TimeScaleModule(Protocol):
    def update(self, state: SimulationState, dt: float) -> None: ...


@dataclass(slots=True)
class TimeScaleTask:
    name: str
    module: TimeScaleModule
    dt: float
    _accumulator: float = 0.0

    def tick(self, state: SimulationState, base_dt: float) -> int:
        if state is None:
            raise ValueError("state nie może być None")
        if base_dt <= 0:
            raise ValueError("base_dt musi być > 0")
        if self.dt <= 0:
            raise ValueError(f"Task '{self.name}' ma niepoprawne dt={self.dt}")
        self._accumulator += base_dt
        runs = 0
        eps = self.dt * 1e-9
        while self._accumulator >= self.dt - eps:
            self.module.update(state, self.dt)
            self._accumulator -= self.dt
            runs += 1
        return runs


class MultiScaleEngine:
    """Uruchamia współsymulację modułów o różnych krokach czasowych."""

    def __init__(self, base_dt: float, tasks: list[TimeScaleTask]):
        if base_dt <= 0:
            raise ValueError("base_dt musi być > 0")
        if tasks is None:
            raise ValueError("tasks nie może być None")
        self.base_dt = float(base_dt)
        self.tasks = tasks

    def run_step(self, state: SimulationState) -> dict[str, int]:
        if state is None:
            raise ValueError("state nie może być None")
        run_counts: dict[str, int] = {}
        for task in self.tasks:
            run_counts[task.name] = task.tick(state, self.base_dt)
        state.advance(self.base_dt)
        return run_counts
