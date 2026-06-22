"""Wspólne narzędzia akumulacji czasu dla współsymulacji."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

TIMEBASE_RELATIVE_TOLERANCE = 1e-9


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
    Klasa nie uruchamia modułów bezpośrednio. Zwraca wyłącznie liczbę
    deterministycznych uruchomień, aby scheduler i silnik wieloskalowy mogły
    stosować identyczną tolerancję oraz raportowanie liczników.
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
