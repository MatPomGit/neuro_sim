"""Signal analysis utilities for EEG/fMRI comparisons."""

from __future__ import annotations

import numpy as np


BAND_LIMITS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "beta": (12.0, 30.0),
    "gamma": (30.0, 80.0),
}


def band_powers(signal: np.ndarray, fs: float, bands: dict[str, tuple[float, float]] | None = None) -> dict[str, float]:
    x = np.asarray(signal, dtype=float)
    if x.ndim != 1:
        raise ValueError("signal must be 1D")
    freqs = np.fft.rfftfreq(x.shape[0], d=1.0 / fs)
    spectrum = np.abs(np.fft.rfft(x)) ** 2
    selected = bands or BAND_LIMITS
    out: dict[str, float] = {}
    for name, (f_lo, f_hi) in selected.items():
        mask = (freqs >= f_lo) & (freqs < f_hi)
        out[name] = float(np.sum(spectrum[mask]))
    return out


def phase_locking_value(signal_a: np.ndarray, signal_b: np.ndarray) -> float:
    a = np.asarray(signal_a, dtype=float)
    b = np.asarray(signal_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("Signals for PLV must have matching shapes")
    phase_a = np.angle(np.fft.fft(a))
    phase_b = np.angle(np.fft.fft(b))
    return float(np.abs(np.mean(np.exp(1j * (phase_a - phase_b)))))


def connectivity_matrix(signals: np.ndarray) -> np.ndarray:
    x = np.asarray(signals, dtype=float)
    if x.ndim != 2:
        raise ValueError("signals must be [n_samples, n_channels]")
    return np.corrcoef(x, rowvar=False)


def comparative_report(simulated: np.ndarray, target: np.ndarray) -> dict[str, float]:
    sim = np.asarray(simulated, dtype=float)
    tgt = np.asarray(target, dtype=float)
    if sim.shape != tgt.shape:
        raise ValueError("Simulated and target arrays must match in shape")
    mae = float(np.mean(np.abs(sim - tgt)))
    rmse = float(np.sqrt(np.mean((sim - tgt) ** 2)))
    corr = float(np.corrcoef(sim.ravel(), tgt.ravel())[0, 1])
    return {"mae": mae, "rmse": rmse, "correlation": corr}
