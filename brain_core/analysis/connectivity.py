"""Metryki konektywności i metryki sieciowe regionów."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConnectivityMetricResult:
    """
    Wynik metryk konektywności.

    Attributes:
        series (dict[str, np.ndarray]): Słownik z macierzami metryk.
        summary (dict[str, float]): Słownik z podsumowującymi statystykami.
    """
    series: dict[str, np.ndarray]
    summary: dict[str, float]


def _pairwise_pli_proxy(signals: np.ndarray) -> np.ndarray:
    """
    Wyznacza uproszczony PLI-proxy z faz FFT dla par kanałów.

    Args:
        signals (np.ndarray): Macierz sygnałów [n_samples, n_channels].

    Returns:
        np.ndarray: Macierz PLI-proxy [n_channels, n_channels].
    """
    phase = np.angle(np.fft.fft(signals, axis=0))
    n_channels = signals.shape[1]
    pli = np.eye(n_channels)
    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            diff = phase[:, i] - phase[:, j]
            value = float(np.abs(np.mean(np.sign(np.sin(diff)))))
            pli[i, j] = value
            pli[j, i] = value
    return pli


def compute_connectivity(signals: np.ndarray) -> ConnectivityMetricResult:
    """
    Liczy macierze sieciowe per region i per parę regionów.

    Args:
        signals (np.ndarray): Macierz sygnałów [n_samples, n_channels].

    Returns:
        ConnectivityMetricResult: Wynik z macierzami i podsumowaniem metryk.

    Raises:
        ValueError: Jeśli wejście ma niepoprawny kształt lub za mało próbek.
    """
    x = np.asarray(signals, dtype=float)
    if x.ndim != 2:
        raise ValueError("signals must be [n_samples, n_channels]")
    if x.shape[0] < 2:
        raise ValueError("signals must have at least 2 samples to compute connectivity")

    corr = np.corrcoef(x, rowvar=False)
    pli = _pairwise_pli_proxy(x)
    region_strength = np.mean(np.abs(corr), axis=1)

    return ConnectivityMetricResult(
        series={"correlation": corr, "pli_proxy": pli, "region_strength": region_strength},
        summary={
            "correlation_mean": float(np.mean(corr)),
            "correlation_abs_mean": float(np.mean(np.abs(corr))),
            "pli_proxy_mean": float(np.mean(pli)),
            "region_strength_mean": float(np.mean(region_strength)),
        },
    )
