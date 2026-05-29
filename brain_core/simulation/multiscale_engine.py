from __future__ import annotations

"""Silnik współsymulacji modułów o różnych krokach czasowych."""

from dataclasses import dataclass
from typing import Protocol

from .state import SimulationState



@dataclass(frozen=True, slots=True)
class MultiScaleIOContract:
    """
    Formalny kontrakt I/O współsymulacji neural-mass <-> SNN.

    Atrybuty:
        base_dt (float): Bazowy krok czasowy.
        snn_sync_dt (float): Krok synchronizacji SNN.
        rate_unit (str): Jednostka częstości.
        activity_unit (str): Jednostka aktywności.
        mapped_populations (tuple[str, ...]): Mapowane populacje.
    """
    base_dt: float
    snn_sync_dt: float
    rate_unit: str
    activity_unit: str
    mapped_populations: tuple[str, ...]

    def validate(self) -> None:
        """
        Waliduje spójność kontraktu czasowego, jednostkowego i mapowania.

        Raises:
            ValueError: Jeśli którykolwiek z warunków nie jest spełniony.
        """
        if self.base_dt <= 0:
            raise ValueError("base_dt kontraktu musi być > 0")
        if self.snn_sync_dt <= 0:
            raise ValueError("snn_sync_dt kontraktu musi być > 0")
        ratio = self.snn_sync_dt / self.base_dt
        if abs(round(ratio) - ratio) > 1e-9:
            raise ValueError("snn_sync_dt musi być całkowitą wielokrotnością base_dt")
        if self.rate_unit != "Hz":
            raise ValueError("rate_unit musi być równe 'Hz'")
        if self.activity_unit != "fraction":
            raise ValueError("activity_unit musi być równe 'fraction'")
        if len(self.mapped_populations) == 0:
            raise ValueError("mapped_populations nie może być puste")



class TimeScaleModule(Protocol):
    """
    Interfejs modułu aktualizowanego z własnym krokiem czasowym.

    Args:
        state (SimulationState): Stan symulacji.
        dt (float): Krok czasowy.
    """
    def update(self, state: SimulationState, dt: float) -> None:
        """Aktualizuje moduł na podstawie stanu symulacji i kroku czasowego."""
        ...



@dataclass(slots=True)
class TimeScaleTask:
    """
    Definicja zadania współsymulacji uruchamianego w danej skali czasu.

    Atrybuty:
        name (str): Nazwa zadania.
        module (TimeScaleModule): Moduł do aktualizacji.
        dt (float): Krok czasowy zadania.
        _accumulator (float): Akumulator czasu.
    """
    name: str
    module: TimeScaleModule
    dt: float
    _accumulator: float = 0.0

    def tick(self, state: SimulationState, base_dt: float) -> int:
        """
        Wykonuje zadanie tyle razy, ile wynika z akumulowanego czasu.

        Args:
            state (SimulationState): Stan symulacji.
            base_dt (float): Bazowy krok czasowy.

        Returns:
            int: Liczba wykonanych kroków.

        Raises:
            ValueError: Jeśli parametry wejściowe są niepoprawne.
        """
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

    def __init__(
        self,
        base_dt: float,
        tasks: list[TimeScaleTask],
        io_contract: MultiScaleIOContract | None = None,
    ) -> None:
        """Inicjalizuje silnik i opcjonalnie waliduje kontrakt I/O."""
        if base_dt <= 0:
            raise ValueError("base_dt musi być > 0")
        if tasks is None:
            raise ValueError("tasks nie może być None")
        
        task_names = [t.name for t in tasks]
        if len(task_names) != len(set(task_names)):
            raise ValueError("Zadania (tasks) muszą mieć unikalne nazwy")

        self.base_dt: float = float(base_dt)
        self.tasks: list[TimeScaleTask] = tasks
        self.io_contract: MultiScaleIOContract | None = io_contract
        if self.io_contract is not None:
            self.io_contract.validate()
            if abs(self.io_contract.base_dt - self.base_dt) > 1e-12:
                raise ValueError("io_contract.base_dt musi być zgodny z base_dt silnika")

    def run_step(self, state: SimulationState) -> dict[str, int]:
        """Uruchamia pojedynczy krok współsymulacji i zwraca liczbę wywołań zadań."""
        if state is None:
            raise ValueError("state nie może być None")
        run_counts: dict[str, int] = {}
        for task in self.tasks:
            run_counts[task.name] = task.tick(state, self.base_dt)
        state.advance(self.base_dt)
        return run_counts
