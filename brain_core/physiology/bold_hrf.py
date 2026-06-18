"""
Minimalistyczny model BOLD oparty o splot z funkcją HRF.
"""

from __future__ import annotations

from numbers import Integral

import numpy as np

from brain_core.data_contracts import (
    CONTRACT_D_POPULATIONS_PHYSIOLOGY,
    validate_bold_drive_contract,
    validate_hrf_contract,
)


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
        undershoot_latency (float): Opóźnienie dołka następczego (undershoot)
            w sekundach [s].
        ratio (float): Bezwymiarowy stosunek amplitudy dołka następczego
            do amplitudy piku.

    Returns:
        np.ndarray: Bezwymiarowy, znormalizowany wektor HRF o zadanej długości;
        suma wartości bezwzględnych wynosi 1, gdy norma jest niezerowa.

    Raises:
        ValueError: Jeśli parametry są niepoprawne.
    """
    if isinstance(length, bool) or not isinstance(length, Integral) or length <= 0:
        raise ValueError(
            f"{CONTRACT_D_POPULATIONS_PHYSIOLOGY}: "
            "hrf.length musi być dodatnią liczbą całkowitą"
        )
    if dt <= 0:
        raise ValueError(
            f"{CONTRACT_D_POPULATIONS_PHYSIOLOGY}: hrf.dt musi być > 0 [s]"
        )
    if peak_latency <= 0 or undershoot_latency <= 0:
        raise ValueError(
            f"{CONTRACT_D_POPULATIONS_PHYSIOLOGY}: "
            "peak_latency i undershoot_latency muszą być > 0 [s]"
        )
    if not np.all(np.isfinite([dt, peak_latency, undershoot_latency, ratio])):
        raise ValueError(
            f"{CONTRACT_D_POPULATIONS_PHYSIOLOGY}: "
            "Parametry HRF (dt, peak_latency, undershoot_latency, ratio) "
            "muszą być skończone"
        )
    if ratio < 0.0:
        raise ValueError(
            f"{CONTRACT_D_POPULATIONS_PHYSIOLOGY}: hrf.ratio musi być >= 0"
        )

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
    drive = validate_bold_drive_contract(neural_drive)
    kernel = validate_hrf_contract(hrf)
    if drive.ndim == 1:
        return np.convolve(drive, kernel, mode="full")[: drive.shape[0]]
    if drive.ndim == 2:
        out = np.zeros_like(drive, dtype=float)
        for i in range(drive.shape[1]):
            out[:, i] = np.convolve(drive[:, i], kernel, mode="full")[: drive.shape[0]]
        return out
    raise ValueError(
        "Kontrakt D: `populations` → `physiology`: "
        "neural_drive musi mieć kształt [n_samples] albo [n_samples, n_regions]."
    )
