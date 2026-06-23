"""Harmonogram faz symulacji oraz hooki współsymulacyjne."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

import numpy as np

from .state import SimulationState
from .timebase import TimeAccumulator

LOGGER = logging.getLogger(__name__)


@runtime_checkable
class StimulusLike(Protocol):
    """Jawny kontrakt bodźca obsługiwanego przez odtwarzacz zadań.

    Protocol opisuje minimalny zestaw pól wymaganych przez harmonogram
    symulacji. Pole ``regional_input`` pozostaje opcjonalne i jest modelowane
    osobnym protokołem, aby zachować zgodność ze starszym formatem
    ``payload["regional_input"]``.
    """

    @property
    def trial_id(self) -> int | str:
        """Identyfikator trialu używany w metrykach i raportach."""
        ...

    @property
    def onset_s(self) -> float:
        """Czas rozpoczęcia bodźca w sekundach."""
        ...

    @property
    def duration_s(self) -> float:
        """Czas trwania bodźca w sekundach."""
        ...

    @property
    def condition(self) -> str:
        """Nazwa warunku eksperymentalnego prezentowana w metrykach."""
        ...

    @property
    def payload(self) -> Mapping[str, object]:
        """Dodatkowe dane bodźca, w tym starsze ``regional_input``."""
        ...

    @property
    def regional_input(self) -> Mapping[str, object] | None:
        """Opcjonalna jawna mapa region→amplituda dla aktywacji bodźca."""
        ...


@runtime_checkable
class RegionalStimulusLike(StimulusLike, Protocol):
    """Zgodnościowy alias kontraktu bodźca z wejściem regionalnym."""


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
    _accumulator: TimeAccumulator | None = None

    def __post_init__(self) -> None:
        """Inicjalizuje wspólny akumulator czasu hooka współsymulacji."""
        if self._accumulator is None:
            self._accumulator = TimeAccumulator(self.dt)

    def tick(self, state: SimulationState, base_dt: float) -> int:
        """Akumuluje czas bazowy, uruchamia moduł i zwraca liczbę wykonań."""
        if state is None:
            raise ValueError("state nie może być None")
        if self._accumulator is None:
            self._accumulator = TimeAccumulator(self.dt)
        runs = self._accumulator.advance(base_dt)
        for _ in range(runs):
            self.module.update(state, self.dt)
        return runs


@dataclass(slots=True)
class TaskStimulusPlayer:
    """Wstrzykuje bodźce zadania poznawczego do osi czasu metryk."""

    stimuli: list[StimulusLike]
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
            try:
                trial_number = int(stimulus.trial_id)
            except (ValueError, TypeError):
                trial_number = None
            emitted.append(
                {
                    "trial_id": stimulus.trial_id,
                    "trial_number": trial_number,
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
    def _is_stimulus_active(stimulus: StimulusLike, time_s: float) -> bool:
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
    def _regional_input_for(stimulus: StimulusLike) -> dict[str, float]:
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
        regional_input = getattr(stimulus, "regional_input", None) or {}
        if not regional_input:
            legacy_regional_input = stimulus.payload.get("regional_input", {})
            if not isinstance(legacy_regional_input, Mapping):
                LOGGER.warning(
                    "Pominięto niepoprawną mapę wejścia regionalnego w payload: %r.",
                    legacy_regional_input,
                )
                legacy_regional_input = {}
            regional_input = legacy_regional_input
        return {
            region: TaskStimulusPlayer._safe_regional_amplitude(region, amplitude)
            for region, amplitude in regional_input.items()
        }

    @staticmethod
    def _safe_regional_amplitude(region: str, raw_value: Any) -> float:
        """Bezpiecznie zamienia wartość wejścia regionalnego na ``float``.

        Parameters
        ----------
        region:
            Nazwa regionu, dla którego konwertowana jest amplituda wejścia.
        raw_value:
            Surowa wartość amplitudy pochodząca z konfiguracji bodźca.

        Returns
        -------
        float
            Skonwertowana amplituda albo ``0.0``, gdy wartość jest pusta lub
            nie da się jej poprawnie zamienić na liczbę zmiennoprzecinkową.
        """
        if raw_value is None:
            LOGGER.warning(
                "Pominięto pustą amplitudę wejścia regionalnego dla regionu %s.",
                region,
            )
            return 0.0

        try:
            return float(raw_value)
        except (TypeError, ValueError):
            LOGGER.warning(
                "Pominięto niepoprawną amplitudę wejścia regionalnego dla regionu %s: %r.",
                region,
                raw_value,
            )
            return 0.0


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
