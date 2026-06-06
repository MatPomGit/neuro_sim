"""Metryki fazowe i synchronizacja sygnałów."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

REPORTABLE_PHASE_LOCKING_METRICS = (
    {
        "name": "phase_locking_value",
        "scope": "para kanałów EEG",
        "unit": "bezwymiarowe 0–1",
        "profile_groups": ("healthy", "disorder", "lesion"),
        "interpretation_pl": (
            "PLV jest gotowe do raportowania jako syntetyczna miara stałości "
            "relacji fazowej między dwoma sygnałami."
        ),
        "limitations_pl": (
            "Implementacja używa faz FFT całego sygnału, więc nie opisuje "
            "lokalnych zmian fazy w oknach czasowych."
        ),
    },
)


@dataclass(frozen=True)
class PhaseLockingMetricResult:
    """
    Wynik metryk fazowych.

    Attributes:
        series (dict[str, np.ndarray]): Słownik z seriami metryk fazowych.
        summary (dict[str, float]): Słownik z podsumowującymi statystykami.
    """

    series: dict[str, np.ndarray]
    summary: dict[str, float]


def compute_phase_locking(
    signal_a: np.ndarray, signal_b: np.ndarray
) -> PhaseLockingMetricResult:
    """
    Liczy PLV dla dwóch sygnałów oraz zwraca serię różnic faz.

    Args:
        signal_a (np.ndarray): Pierwszy sygnał (1D).
        signal_b (np.ndarray): Drugi sygnał (1D).

    Returns:
        PhaseLockingMetricResult: Wynik z serią różnic faz i wartością PLV.

    Raises:
        ValueError: Jeśli sygnały są puste, niejednowymiarowe lub mają różne kształty.
    """
    a = np.asarray(signal_a, dtype=float)
    b = np.asarray(signal_b, dtype=float)
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("Signals for PLV must be 1D arrays")
    if a.size == 0:
        raise ValueError("Signals for PLV cannot be empty")
    if a.shape != b.shape:
        raise ValueError("Signals for PLV must have matching shapes")
    phase_a = np.angle(np.fft.fft(a))
    phase_b = np.angle(np.fft.fft(b))
    phase_diff = phase_a - phase_b
    plv = float(np.abs(np.mean(np.exp(1j * phase_diff))))
    return PhaseLockingMetricResult(
        series={"phase_diff": phase_diff}, summary={"plv": plv}
    )
