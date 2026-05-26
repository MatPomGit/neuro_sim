from __future__ import annotations

import numpy as np


class DelayBuffer:
    """Ring-buffer for per-connection delayed activity lookup."""

    def __init__(self, n_regions: int, delays_steps: np.ndarray):
        if delays_steps.shape != (n_regions, n_regions):
            raise ValueError("delays_steps musi mieć rozmiar [n_regions, n_regions]")
        if np.any(delays_steps < 0):
            raise ValueError("delays_steps nie może zawierać wartości ujemnych")

        self.delays_steps = delays_steps.astype(int)
        self.max_delay = int(np.max(self.delays_steps))
        self._history = np.zeros((self.max_delay + 1, n_regions), dtype=float)
        self._cursor = 0

    def push(self, activity: np.ndarray) -> None:
        if activity.shape != (self._history.shape[1],):
            raise ValueError("activity musi mieć rozmiar [n_regions]")
        self._cursor = (self._cursor + 1) % self._history.shape[0]
        self._history[self._cursor] = activity

    def delayed_activity_matrix(self) -> np.ndarray:
        n = self._history.shape[1]
        out = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(n):
                delay = self.delays_steps[i, j]
                idx = (self._cursor - delay) % self._history.shape[0]
                out[i, j] = self._history[idx, j]
        return out


def delayed_coupling(connectivity: np.ndarray, delayed_matrix: np.ndarray) -> np.ndarray:
    """Compute coupling_i(t) = Σ_j C_ij * activity_j(t-delay_ij)."""
    if connectivity.shape != delayed_matrix.shape:
        raise ValueError("connectivity i delayed_matrix muszą mieć ten sam rozmiar [n_regions, n_regions]")
    return np.sum(connectivity * delayed_matrix, axis=1)
