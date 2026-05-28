"""Fasada metryk sygnałowych dla kompatybilności API."""

from __future__ import annotations

import numpy as np

from .connectivity import compute_connectivity
from .phase_locking import compute_phase_locking
from .spectral import BAND_LIMITS, compute_band_powers


def band_powers(signal: np.ndarray, fs: float, bands: dict[str, tuple[float, float]] | None = None) -> dict[str, float]:
    """
    Zwraca podsumowanie energii pasm dla kompatybilności wstecznej.

    Args:
        signal (np.ndarray): Sygnał wejściowy.
        fs (float): Częstotliwość próbkowania.
        bands (dict[str, tuple[float, float]] | None): Zakresy pasm.

    Returns:
        dict[str, float]: Słownik z energią w pasmach.
    """
    return compute_band_powers(signal=signal, fs=fs, bands=bands).summary


def phase_locking_value(signal_a: np.ndarray, signal_b: np.ndarray) -> float:
    """
    Zwraca PLV dla kompatybilności wstecznej.

    Args:
        signal_a (np.ndarray): Pierwszy sygnał.
        signal_b (np.ndarray): Drugi sygnał.

    Returns:
        float: Wartość PLV.
    """
    return compute_phase_locking(signal_a=signal_a, signal_b=signal_b).summary["plv"]


def connectivity_matrix(signals: np.ndarray) -> np.ndarray:
    """
    Zwraca macierz korelacji dla kompatybilności wstecznej.

    Args:
        signals (np.ndarray): Macierz sygnałów.

    Returns:
        np.ndarray: Macierz korelacji.
    """
    return compute_connectivity(signals=signals).series["correlation"]


def comparative_report(simulated: np.ndarray, target: np.ndarray) -> dict[str, float]:
    """
    Raport porównawczy dwóch sygnałów.

    Args:
        simulated (np.ndarray): Sygnał symulowany.
        target (np.ndarray): Sygnał referencyjny.

    Returns:
        dict[str, float]: Słownik z metrykami MAE, RMSE i korelacją.

    Raises:
        ValueError: Jeśli sygnały mają różne kształty.
    """
    sim = np.asarray(simulated, dtype=float)
    tgt = np.asarray(target, dtype=float)
    if sim.shape != tgt.shape:
        raise ValueError("Simulated and target arrays must match in shape")
    mae = float(np.mean(np.abs(sim - tgt)))
    rmse = float(np.sqrt(np.mean((sim - tgt) ** 2)))
    corr = float(np.corrcoef(sim.ravel(), tgt.ravel())[0, 1])
    return {"mae": mae, "rmse": rmse, "correlation": corr}
