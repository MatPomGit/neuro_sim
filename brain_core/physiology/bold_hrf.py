"""
Minimalistyczny model BOLD oparty o splot z funkcją HRF.
"""

from __future__ import annotations

import numpy as np


def canonical_hrf(
    length: int,
    dt: float,
    peak_latency: float = 5.0,
    undershoot_latency: float = 12.0,
    ratio: float = 0.35,
) -> np.ndarray:
    """
    Buduje prostą funkcję HRF (bi-gamma) z dwóch funkcji alfa.

    Args:
        length (int): Długość sygnału w próbkach.
        dt (float): Rozdzielczość czasowa w sekundach [s].
        peak_latency (float): Opóźnienie piku w sekundach [s].
        undershoot_latency (float): Opóźnienie podbicia w sekundach [s].
        ratio (float): Bezwymiarowy stosunek amplitudy podbicia do piku.

    Returns:
        np.ndarray: Bezwymiarowy, znormalizowany wektor HRF o zadanej długości;
        suma wartości bezwzględnych wynosi 1, gdy norma jest niezerowa.

    Raises:
        ValueError: Jeśli parametry są niepoprawne.
    """
    if length <= 0:
        raise ValueError("length must be > 0")
    if dt <= 0:
        raise ValueError("dt must be > 0")
    if peak_latency <= 0 or undershoot_latency <= 0:
        raise ValueError("peak_latency and undershoot_latency must be > 0")

    t = np.arange(length, dtype=float) * dt
    peak = (t / peak_latency) ** 8 * np.exp(-(t - peak_latency) / peak_latency)
    undershoot = (t / undershoot_latency) ** 8 * np.exp(
        -(t - undershoot_latency) / undershoot_latency
    )
    hrf = peak - ratio * undershoot
    norm = np.sum(np.abs(hrf))
    if norm == 0:
        return hrf
    return hrf / norm


def convolve_with_hrf(neural_drive: np.ndarray, hrf: np.ndarray) -> np.ndarray:
    """
    Splot napędu neuronalnego z HRF wzdłuż osi czasu (po regionach).

    Args:
        neural_drive (np.ndarray): Nieujemny napęd neuronalny/BOLD proxy
            [n_próbek] lub [n_próbek, n_regionów].
        hrf (np.ndarray): Bezwymiarowy wektor HRF, zwykle znormalizowany przez
            ``canonical_hrf``.

    Returns:
        np.ndarray: Sygnał BOLD proxy po splocie, w jednostkach względnej
        amplitudy wynikających ze skali ``neural_drive``.

    Raises:
        ValueError: Jeśli wejście ma niepoprawny kształt.
    """
    drive = np.asarray(neural_drive, dtype=float)
    kernel = np.asarray(hrf, dtype=float)
    if drive.ndim == 1:
        return np.convolve(drive, kernel, mode="full")[: drive.shape[0]]
    if drive.ndim == 2:
        out = np.zeros_like(drive, dtype=float)
        for i in range(drive.shape[1]):
            out[:, i] = np.convolve(drive[:, i], kernel, mode="full")[: drive.shape[0]]
        return out
    raise ValueError(
        "neural_drive must have shape [n_samples] or [n_samples, n_regions]."
    )
