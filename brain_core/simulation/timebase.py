"""Wspólne narzędzia akumulacji czasu dla współsymulacji."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .state import SimulationState

TIMEBASE_RELATIVE_TOLERANCE = 1e-9


def is_time_multiple(candidate_dt: float, base_dt: float) -> bool:
    """Sprawdza, czy krok czasu jest całkowitą wielokrotnością bazy.

    Parameters
    ----------
    candidate_dt:
        Sprawdzany krok czasu w sekundach.
    base_dt:
        Bazowy krok czasu w sekundach.

    Returns
    -------
    bool
        ``True``, gdy ``candidate_dt / base_dt`` jest całkowite w granicach
        wspólnej tolerancji numerycznej osi czasu.

    Raises
    ------
    ValueError
        Gdy którykolwiek krok czasu nie jest dodatnią skończoną liczbą.
    """
    validated_candidate_dt = TimeAccumulator._validate_positive_finite(
        "candidate_dt", candidate_dt
    )
    validated_base_dt = TimeAccumulator._validate_positive_finite("base_dt", base_dt)
    ratio = validated_candidate_dt / validated_base_dt
    return abs(round(ratio) - ratio) <= TIMEBASE_RELATIVE_TOLERANCE


def compute_step_count(duration_s: float, dt_s: float) -> int:
    """Wyznacza liczbę kroków symulacji dla czasu trwania i kroku bazowego.

    Parameters
    ----------
    duration_s:
        Czas trwania symulacji w sekundach.
    dt_s:
        Bazowy krok czasu w sekundach.

    Returns
    -------
    int
        Liczba dyskretnych kroków do wykonania przez główną pętlę symulacji.

    Raises
    ------
    ValueError
        Gdy czas trwania jest ujemny, nieskończony albo krok czasu nie jest
        dodatnią skończoną liczbą.
    """
    validated_duration_s = TimeAccumulator._validate_non_negative_finite(
        "duration_s", duration_s
    )
    validated_dt_s = TimeAccumulator._validate_positive_finite("dt_s", dt_s)
    return int(round(validated_duration_s / validated_dt_s))


def compute_time_stride(candidate_dt: float, base_dt: float) -> int:
    """Wyznacza całkowity odstęp kroków między zdarzeniami czasowymi.

    Parameters
    ----------
    candidate_dt:
        Krok wolniejszego zdarzenia lub synchronizacji w sekundach.
    base_dt:
        Bazowy krok symulacji w sekundach.

    Returns
    -------
    int
        Liczba bazowych kroków przypadających na jeden krok ``candidate_dt``.

    Raises
    ------
    ValueError
        Gdy ``candidate_dt`` nie jest całkowitą wielokrotnością ``base_dt``
        w granicach wspólnej tolerancji osi czasu.
    """
    if not is_time_multiple(candidate_dt, base_dt):
        raise ValueError("candidate_dt musi być całkowitą wielokrotnością base_dt")
    return max(1, int(round(float(candidate_dt) / float(base_dt))))


class TimeSteppedModule(Protocol):
    """Interfejs modułu aktualizowanego przez wspólną bazę czasu.

    Protocol opisuje minimalny kontrakt wymagany przez akumulator czasu, aby
    scheduler i silnik wieloskalowy mogły uruchamiać moduły w identyczny sposób.
    """

    def update(self, state: SimulationState, dt: float) -> None:
        """Aktualizuje moduł dla pojedynczego lokalnego kroku czasowego."""
        ...


@dataclass(slots=True)
class TimeAccumulator:
    """Akumuluje bazowe kroki czasu i raportuje gotowe uruchomienia modułu.

    Parameters
    ----------
    dt:
        Lokalny krok czasowy modułu w sekundach.
    elapsed_time:
        Zakumulowany czas oczekujący na wykonanie lokalnego kroku w sekundach.
    relative_tolerance:
        Względna tolerancja numeryczna używana przy porównaniu czasu
        zakumulowanego z lokalnym krokiem.

    Raises
    ------
    ValueError
        Gdy ``dt`` albo ``relative_tolerance`` nie są skończone lub mają
        niepoprawny zakres.

    Notes
    -----
    Klasa może raportować liczbę deterministycznych uruchomień albo wykonać
    wskazany moduł. Dzięki temu scheduler i silnik wieloskalowy stosują tę samą
    tolerancję oraz tak samo zwracają liczniki wykonań.
    """

    dt: float
    elapsed_time: float = 0.0
    relative_tolerance: float = TIMEBASE_RELATIVE_TOLERANCE

    def __post_init__(self) -> None:
        """Waliduje parametry akumulatora po inicjalizacji."""
        self.dt = self._validate_positive_finite("dt", self.dt)
        self.elapsed_time = self._validate_non_negative_finite(
            "elapsed_time", self.elapsed_time
        )
        self.relative_tolerance = self._validate_non_negative_finite(
            "relative_tolerance", self.relative_tolerance
        )
        if self.relative_tolerance >= 1.0:
            raise ValueError("relative_tolerance musi być < 1.0")

    def advance(self, base_dt: float) -> int:
        """Dodaje bazowy krok czasu i zwraca liczbę gotowych uruchomień.

        Parameters
        ----------
        base_dt:
            Bazowy krok symulacji w sekundach, który ma zostać dodany do
            zakumulowanego czasu.

        Returns
        -------
        int
            Liczba pełnych lokalnych kroków ``dt`` dostępnych po akumulacji.

        Raises
        ------
        ValueError
            Gdy ``base_dt`` nie jest dodatnią skończoną liczbą.
        """
        validated_base_dt = self._validate_positive_finite("base_dt", base_dt)
        self.elapsed_time += validated_base_dt
        runs = 0
        tolerance = self.dt * self.relative_tolerance
        while self.elapsed_time >= self.dt - tolerance:
            self.elapsed_time -= self.dt
            runs += 1
        if abs(self.elapsed_time) <= tolerance:
            self.elapsed_time = 0.0
        return runs

    def run_due_steps(
        self, module: TimeSteppedModule, state: SimulationState, base_dt: float
    ) -> int:
        """Uruchamia moduł dla wszystkich kroków gotowych po akumulacji czasu.

        Parameters
        ----------
        module:
            Moduł symulacyjny aktualizowany lokalnym krokiem ``dt``.
        state:
            Mutowalny stan symulacji przekazywany do modułu.
        base_dt:
            Bazowy krok symulacji w sekundach dodawany do akumulatora.

        Returns
        -------
        int
            Liczba wywołań ``module.update`` wykonanych w tej akumulacji.

        Raises
        ------
        ValueError
            Gdy ``state`` jest ``None`` albo ``base_dt`` jest niepoprawny.
        """
        if state is None:
            raise ValueError("state nie może być None")
        runs = self.advance(base_dt)
        for _ in range(runs):
            module.update(state, self.dt)
        return runs

    @staticmethod
    def _validate_positive_finite(name: str, value: float) -> float:
        """Zwraca dodatnią skończoną wartość zmiennoprzecinkową."""
        numeric_value = float(value)
        if not np.isfinite(numeric_value) or numeric_value <= 0.0:
            raise ValueError(f"{name} musi być skończoną liczbą > 0")
        return numeric_value

    @staticmethod
    def _validate_non_negative_finite(name: str, value: float) -> float:
        """Zwraca nieujemną skończoną wartość zmiennoprzecinkową."""
        numeric_value = float(value)
        if not np.isfinite(numeric_value) or numeric_value < 0.0:
            raise ValueError(f"{name} musi być skończoną liczbą >= 0")
        return numeric_value
