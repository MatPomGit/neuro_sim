"""Metryki spektralne sygnałów neuro."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


BAND_LIMITS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "beta": (12.0, 30.0),
    "gamma": (30.0, 80.0),
}


@dataclass(frozen=True)
class SpectralMetricResult:
    """
    Wynik metryk spektralnych z szeregiem i statystykami zbiorczymi.

    Attributes:
        series (dict[str, np.ndarray]): Słownik z seriami spektralnymi.
        summary (dict[str, float]): Słownik z podsumowaniem energii w pasmach.
    """
    series: dict[str, np.ndarray]
    summary: dict[str, float]


def _validate_signal(signal: np.ndarray) -> np.ndarray:
    """
    Waliduje i normalizuje wejście do postaci sygnału 1D.

    Args:
        signal (np.ndarray): Sygnał wejściowy.

    Returns:
        np.ndarray: Sygnał 1D.

    Raises:
        ValueError: Jeśli sygnał nie jest 1D lub jest pusty.
    """
    x = np.asarray(signal, dtype=float)
    if x.ndim != 1:
        raise ValueError("signal must be 1D")
    if x.size == 0:
        raise ValueError("signal cannot be empty")
    return x


def compute_band_powers(
    signal: np.ndarray,
    fs: float,
    bands: dict[str, tuple[float, float]] | None = None,
) -> SpectralMetricResult:
    """
    Liczy energię pasm i zwraca pełne series + podsumowanie.

    Args:
        signal (np.ndarray): Sygnał wejściowy (1D).
        fs (float): Częstotliwość próbkowania.
        bands (dict[str, tuple[float, float]] | None): Zakresy pasm.

    Returns:
        SpectralMetricResult: Wynik z seriami i podsumowaniem energii w pasmach.
    """
    x = _validate_signal(signal)
    n = x.shape[0]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    spectrum = np.abs(np.fft.rfft(x)) ** 2 / (n**2)

    selected = bands or BAND_LIMITS
    band_series: dict[str, np.ndarray] = {}
    summary: dict[str, float] = {}
    for name, (f_lo, f_hi) in selected.items():
        mask = (freqs >= f_lo) & (freqs < f_hi)
        values = spectrum[mask]
        band_series[name] = values
        summary[name] = float(np.sum(values))

    return SpectralMetricResult(
        series={"frequencies": freqs, "power_spectrum": spectrum, "band_values": band_series},
        summary=summary,
    )
