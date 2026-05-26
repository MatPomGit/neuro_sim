"""Minimal BOLD model via HRF convolution."""

from __future__ import annotations

import numpy as np


def canonical_hrf(length: int, dt: float, peak_latency: float = 5.0, undershoot_latency: float = 12.0, ratio: float = 0.35) -> np.ndarray:
    """Build a simple bi-gamma-like HRF from two alpha functions."""
    if length <= 0:
        raise ValueError("length must be > 0")
    if dt <= 0:
        raise ValueError("dt must be > 0")

    t = np.arange(length, dtype=float) * dt
    peak = (t / peak_latency) ** 8 * np.exp(-(t - peak_latency) / peak_latency)
    undershoot = (t / undershoot_latency) ** 8 * np.exp(-(t - undershoot_latency) / undershoot_latency)
    hrf = peak - ratio * undershoot
    norm = np.sum(np.abs(hrf))
    if norm == 0:
        return hrf
    return hrf / norm


def convolve_with_hrf(neural_drive: np.ndarray, hrf: np.ndarray) -> np.ndarray:
    """Convolve per-region neural drive with HRF along time axis."""
    drive = np.asarray(neural_drive, dtype=float)
    kernel = np.asarray(hrf, dtype=float)
    if drive.ndim == 1:
        return np.convolve(drive, kernel, mode="full")[: drive.shape[0]]
    if drive.ndim == 2:
        out = np.zeros_like(drive, dtype=float)
        for i in range(drive.shape[1]):
            out[:, i] = np.convolve(drive[:, i], kernel, mode="full")[: drive.shape[0]]
        return out
    raise ValueError("neural_drive must have shape [n_samples] or [n_samples, n_regions].")
