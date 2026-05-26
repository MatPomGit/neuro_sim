from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class RegionWilsonCowanParams:
    tau_E: float = 0.02
    tau_I: float = 0.01
    w_EE: float = 12.0
    w_EI: float = 10.0
    w_IE: float = 10.0
    w_II: float = 2.0
    gain_E: float = 1.0
    gain_I: float = 1.0
    threshold_E: float = 0.0
    threshold_I: float = 0.0


class RegionWilsonCowanModel:
    """Wilson-Cowan model with separate E/I state per region."""

    def __init__(self, region_names: list[str], params: dict[str, RegionWilsonCowanParams]):
        if not region_names:
            raise ValueError("region_names nie może być puste")
        missing = [r for r in region_names if r not in params]
        if missing:
            raise ValueError(f"Brak parametrów dla regionów: {missing}")

        self.region_names = region_names
        self.params = params
        n = len(region_names)
        self.E = np.zeros(n, dtype=float)
        self.I = np.zeros(n, dtype=float)

    @staticmethod
    def _sigmoid(x: np.ndarray, gain: np.ndarray, threshold: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-gain * (x - threshold)))

    def step(self, dt: float, external_e: np.ndarray, external_i: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if dt <= 0:
            raise ValueError("dt musi być > 0")
        if external_e.shape != self.E.shape or external_i.shape != self.I.shape:
            raise ValueError("external_e/external_i muszą pasować rozmiarem do regionów")

        tau_E = np.array([self.params[r].tau_E for r in self.region_names], dtype=float)
        tau_I = np.array([self.params[r].tau_I for r in self.region_names], dtype=float)
        w_EE = np.array([self.params[r].w_EE for r in self.region_names], dtype=float)
        w_EI = np.array([self.params[r].w_EI for r in self.region_names], dtype=float)
        w_IE = np.array([self.params[r].w_IE for r in self.region_names], dtype=float)
        w_II = np.array([self.params[r].w_II for r in self.region_names], dtype=float)
        gain_E = np.array([self.params[r].gain_E for r in self.region_names], dtype=float)
        gain_I = np.array([self.params[r].gain_I for r in self.region_names], dtype=float)
        threshold_E = np.array([self.params[r].threshold_E for r in self.region_names], dtype=float)
        threshold_I = np.array([self.params[r].threshold_I for r in self.region_names], dtype=float)

        input_E = w_EE * self.E - w_EI * self.I + external_e
        input_I = w_IE * self.E - w_II * self.I + external_i

        dE = (-self.E + self._sigmoid(input_E, gain_E, threshold_E)) / tau_E
        dI = (-self.I + self._sigmoid(input_I, gain_I, threshold_I)) / tau_I

        self.E = np.clip(self.E + dt * dE, 0.0, 1.0)
        self.I = np.clip(self.I + dt * dI, 0.0, 1.0)
        return self.E.copy(), self.I.copy()
