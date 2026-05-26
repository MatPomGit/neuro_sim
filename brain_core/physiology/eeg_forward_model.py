"""EEG forward models and inverse solvers based on a leadfield matrix."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ForwardModelConfig:
    """Configuration for forward modeling variants."""

    sensor_noise_std: float = 0.0
    reference: str = "none"  # none | average


class EEGForwardModel:
    """Linear EEG forward model projecting regional sources to sensors."""

    def __init__(self, leadfield: np.ndarray, config: ForwardModelConfig | None = None) -> None:
        lf = np.asarray(leadfield, dtype=float)
        if lf.ndim != 2:
            raise ValueError("Leadfield must be a 2D matrix [n_sensors, n_sources].")
        if lf.shape[0] == 0 or lf.shape[1] == 0:
            raise ValueError("Leadfield cannot be empty.")
        self.leadfield = lf
        self.config = config or ForwardModelConfig()

    @property
    def n_sensors(self) -> int:
        return int(self.leadfield.shape[0])

    @property
    def n_sources(self) -> int:
        return int(self.leadfield.shape[1])

    def _apply_reference(self, eeg: np.ndarray) -> np.ndarray:
        if self.config.reference == "none":
            return eeg
        if self.config.reference == "average":
            if eeg.ndim == 1:
                return eeg - np.mean(eeg)
            return eeg - np.mean(eeg, axis=-1, keepdims=True)
        raise ValueError("Unsupported reference. Use 'none' or 'average'.")

    def project(self, source_activity: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
        src = np.asarray(source_activity, dtype=float)
        if src.ndim == 1:
            if src.shape[0] != self.n_sources:
                raise ValueError("Source vector length must match number of sources.")
            eeg = self.leadfield @ src
        elif src.ndim == 2:
            if src.shape[1] != self.n_sources:
                raise ValueError("Source matrix second dimension must match number of sources.")
            eeg = src @ self.leadfield.T
        else:
            raise ValueError("source_activity must be [n_sources] or [n_samples, n_sources].")

        if self.config.sensor_noise_std > 0.0:
            noise_rng = rng if rng is not None else np.random.default_rng(0)
            eeg = eeg + noise_rng.normal(scale=self.config.sensor_noise_std, size=eeg.shape)
        return self._apply_reference(eeg)


class EEGInverseSolver:
    """Inverse solvers for recovering source activity from EEG sensor space."""

    def __init__(self, leadfield: np.ndarray) -> None:
        lf = np.asarray(leadfield, dtype=float)
        if lf.ndim != 2:
            raise ValueError("Leadfield must be a 2D matrix [n_sensors, n_sources].")
        self.leadfield = lf

    def _solve(self, eeg: np.ndarray, operator: np.ndarray) -> np.ndarray:
        y = np.asarray(eeg, dtype=float)
        if y.ndim == 1:
            return operator @ y
        if y.ndim == 2:
            return y @ operator.T
        raise ValueError("eeg must have shape [n_sensors] or [n_samples, n_sensors].")

    def minimum_norm(self, eeg: np.ndarray, lam: float = 1e-2) -> np.ndarray:
        """L2-regularized MNE (ridge) inverse."""
        if lam <= 0:
            raise ValueError("lam must be > 0")
        g = self.leadfield
        inv = np.linalg.inv(g @ g.T + lam * np.eye(g.shape[0]))
        operator = g.T @ inv
        return self._solve(eeg, operator)

    def weighted_minimum_norm(self, eeg: np.ndarray, lam: float = 1e-2, depth: np.ndarray | None = None) -> np.ndarray:
        """Depth-weighted minimum norm (diagonal source prior)."""
        if lam <= 0:
            raise ValueError("lam must be > 0")
        g = self.leadfield
        n_sources = g.shape[1]
        d = np.ones(n_sources, dtype=float) if depth is None else np.asarray(depth, dtype=float)
        if d.shape != (n_sources,):
            raise ValueError("depth must have shape [n_sources]")
        if np.any(d <= 0):
            raise ValueError("depth weights must be positive")
        w = np.diag(d)
        gw = g @ w
        inv = np.linalg.inv(gw @ gw.T + lam * np.eye(g.shape[0]))
        operator = w @ g.T @ inv
        return self._solve(eeg, operator)
