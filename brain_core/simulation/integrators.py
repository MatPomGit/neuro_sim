from __future__ import annotations

"""Integratory numeryczne używane przez komponenty dynamiczne symulacji."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class DynamicsFn(Protocol):
    """Sygnatura funkcji dynamiki deterministycznej."""

    def __call__(self, t: float, y: np.ndarray) -> np.ndarray: ...


class NoiseFn(Protocol):
    """Sygnatura funkcji składowej dyfuzyjnej dla SDE."""

    def __call__(self, t: float, y: np.ndarray) -> np.ndarray: ...


class BaseIntegrator(Protocol):
    """Wspólny interfejs integratorów czasu."""

    def step(self, t: float, y: np.ndarray, dt: float, f: DynamicsFn) -> np.ndarray: ...


@dataclass(slots=True)
class EulerMaruyamaIntegrator:
    """Integrator dla SDE: y' = f(t, y) + g(t, y) * xi."""

    noise_fn: NoiseFn
    rng: np.random.Generator

    def step(self, t: float, y: np.ndarray, dt: float, f: DynamicsFn) -> np.ndarray:
        """Wykonuje pojedynczy krok Eulera-Maruyamy."""
        drift = f(t, y) * dt
        diffusion = self.noise_fn(t, y) * self.rng.normal(size=y.shape) * np.sqrt(dt)
        return y + drift + diffusion


@dataclass(slots=True)
class RK4Integrator:
    """Klasyczny deterministyczny krok RK4."""

    def step(self, t: float, y: np.ndarray, dt: float, f: DynamicsFn) -> np.ndarray:
        """Wykonuje pojedynczy krok Rungego-Kutty 4. rzędu."""
        k1 = f(t, y)
        k2 = f(t + 0.5 * dt, y + 0.5 * dt * k1)
        k3 = f(t + 0.5 * dt, y + 0.5 * dt * k2)
        k4 = f(t + dt, y + dt * k3)
        return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
