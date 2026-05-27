"""Metryki fazowe i synchronizacja sygnałów."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PhaseLockingMetricResult:
    """Wynik metryk fazowych."""

    series: dict[str, np.ndarray]
    summary: dict[str, float]


def compute_phase_locking(signal_a: np.ndarray, signal_b: np.ndarray) -> PhaseLockingMetricResult:
    """Liczy PLV dla dwóch sygnałów oraz zwraca serię różnic faz."""
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
    return PhaseLockingMetricResult(series={"phase_diff": phase_diff}, summary={"plv": plv})
