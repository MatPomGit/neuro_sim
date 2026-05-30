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
        """Emituje nowe zdarzenia i odświeża aktywne wejścia regionalne."""
        del dt
        emitted = state.metrics.setdefault("trial_events", [])
        while (
            self.cursor < len(self.stimuli)
            and self.stimuli[self.cursor].onset_s <= state.time + 1e-9
        ):
            stimulus = self.stimuli[self.cursor]
            regional_input = self._regional_input_for(stimulus)
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

        self._apply_active_regional_inputs(state)

    def _apply_active_regional_inputs(self, state: SimulationState) -> None:
        """Ustawia amplitudy tylko dla bodźców aktywnych w bieżącym czasie.

        Parameters
        ----------
        state:
            Mutowalny stan symulacji z czasem oraz mapą wejść regionalnych.
        """
        managed_regions: set[str] = set()
        active_inputs: dict[str, float] = {}
        for stimulus in self.stimuli:
            regional_input = self._regional_input_for(stimulus)
            managed_regions.update(regional_input)
            if not self._is_stimulus_active(stimulus, state.time):
                continue
            for region, amplitude in regional_input.items():
                active_inputs[region] = active_inputs.get(region, 0.0) + float(
                    amplitude
                )

        for region in managed_regions:
            state.regions[region] = np.array(
                [active_inputs.get(region, 0.0)], dtype=float
            )

    @staticmethod
    def _is_stimulus_active(stimulus: Any, time_s: float) -> bool:
        """Sprawdza, czy bodziec obejmuje bieżący czas symulacji.

        Parameters
        ----------
        stimulus:
            Bodziec z polami ``onset_s`` oraz ``duration_s`` wyrażonymi w sekundach.
        time_s:
            Bieżący czas symulacji w sekundach.

        Returns
        -------
        bool
            ``True``, gdy czas należy do półotwartego przedziału aktywności
            ``[onset_s, onset_s + duration_s)``.
        """
        return stimulus.onset_s <= time_s + 1e-9 and time_s < (
            stimulus.onset_s + stimulus.duration_s
        )

    @staticmethod
    def _regional_input_for(stimulus: Any) -> dict[str, float]:
        """Zwraca znormalizowaną mapę wejść regionalnych bodźca.

        Parameters
        ----------
        stimulus:
            Bodziec zawierający jawne ``regional_input`` albo starszy wpis
            ``payload["regional_input"]``.

        Returns
        -------
        dict[str, float]
            Kopia mapy region→amplituda z wartościami liczbowymi typu ``float``.
        """
        regional_input = getattr(stimulus, "regional_input", None)
        if regional_input is None:
            regional_input = stimulus.payload.get("regional_input", {})
        return {
            region: float(amplitude) for region, amplitude in regional_input.items()
        }


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
