"""Testy deterministycznej akumulacji czasu współsymulacji."""

from __future__ import annotations

import pytest

from brain_core.simulation.multiscale_engine import TimeScaleTask
from brain_core.simulation.scheduler import CoSimulationHook
from brain_core.simulation.state import SimulationState
from brain_core.simulation.timebase import TimeAccumulator


class CountingModule:
    """Moduł testowy zapisujący liczbę i kroki czasowe uruchomień."""

    def __init__(self) -> None:
        """Inicjalizuje pusty rejestr deterministycznych uruchomień."""
        self.run_dts: list[float] = []

    @property
    def runs(self) -> int:
        """Zwraca liczbę zarejestrowanych uruchomień modułu."""
        return len(self.run_dts)

    def update(self, state: SimulationState, dt: float) -> None:
        """Dopisuje krok czasowy do metryk i lokalnego rejestru testowego."""
        self.run_dts.append(dt)
        state.metrics["runs"] = state.metrics.get("runs", 0) + 1


@pytest.mark.parametrize("task_factory", [TimeScaleTask, CoSimulationHook])
def test_timebase_runs_every_step_when_dt_equals_base_dt(task_factory: type) -> None:
    """Moduł uruchamia się deterministycznie w każdym kroku dla dt == base_dt."""
    module = CountingModule()
    task = task_factory("fast", module, 0.001)
    state = SimulationState()

    counts = [task.tick(state, 0.001) for _ in range(5)]

    assert counts == [1, 1, 1, 1, 1]
    assert module.runs == 5
    assert module.run_dts == [0.001] * 5
    assert state.metrics["runs"] == 5


@pytest.mark.parametrize("task_factory", [TimeScaleTask, CoSimulationHook])
def test_timebase_runs_on_integer_multiple_of_base_dt(task_factory: type) -> None:
    """Moduł raportuje pojedyncze uruchomienie po całkowitej wielokrotności base_dt."""
    module = CountingModule()
    task = task_factory("slow", module, 0.003)
    state = SimulationState()

    counts = [task.tick(state, 0.001) for _ in range(6)]

    assert counts == [0, 0, 1, 0, 0, 1]
    assert module.runs == 2
    assert state.metrics["runs"] == 2


@pytest.mark.parametrize("task_factory", [TimeScaleTask, CoSimulationHook])
def test_timebase_uses_same_floating_point_tolerance(task_factory: type) -> None:
    """Mały błąd zmiennoprzecinkowy nie zmienia deterministycznej liczby uruchomień."""
    module = CountingModule()
    task = task_factory("tolerant", module, 0.3)
    state = SimulationState()

    counts = [task.tick(state, 0.1 - 1e-12) for _ in range(3)]

    assert counts == [0, 0, 1]
    assert module.runs == 1
    assert state.metrics["runs"] == 1


def test_time_accumulator_can_report_multiple_runs_after_large_base_step() -> None:
    """Akumulator raportuje wszystkie zaległe uruchomienia po większym kroku bazowym."""
    accumulator = TimeAccumulator(dt=0.002)

    assert accumulator.advance(0.005) == 2
    assert accumulator.advance(0.001) == 1
