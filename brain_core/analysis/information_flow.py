"""Uproszczone metryki przepływu informacji między regionami."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class InformationFlowMetricResult:
    """Wynik metryk kierunkowości przepływu."""

    series: dict[str, np.ndarray]
    summary: dict[str, float]


def compute_information_flow(signals: np.ndarray) -> InformationFlowMetricResult:
    """Wyznacza uproszczoną kierunkowość opartą o korelacje opóźnione o 1 próbkę."""
    x = np.asarray(signals, dtype=float)
    if x.ndim != 2:
        raise ValueError("signals must be [n_samples, n_channels]")
    if x.shape[0] < 3:
        raise ValueError("signals must have at least 3 samples")

    n_channels = x.shape[1]
    directional = np.zeros((n_channels, n_channels), dtype=float)
    for i in range(n_channels):
        src_lag = x[:-1, i]
        for j in range(n_channels):
            if i == j:
                continue
            tgt_now = x[1:, j]
            tgt_lag = x[:-1, j]
            forward = np.corrcoef(src_lag, tgt_now)[0, 1]
            backward = np.corrcoef(tgt_lag, x[1:, i])[0, 1]
            directional[i, j] = float(np.nan_to_num(forward - backward, nan=0.0))

    outgoing = np.sum(np.maximum(directional, 0.0), axis=1)
    return InformationFlowMetricResult(
        series={"directional_matrix": directional, "outgoing_strength": outgoing},
        summary={
            "directional_mean": float(np.mean(directional)),
            "directional_abs_mean": float(np.mean(np.abs(directional))),
            "outgoing_mean": float(np.mean(outgoing)),
        },
    )
