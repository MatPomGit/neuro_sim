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

    @property
    def _tau_E(self) -> np.ndarray:
        return np.array([self.params[r].tau_E for r in self.region_names], dtype=float)

    @property
    def _tau_I(self) -> np.ndarray:
        return np.array([self.params[r].tau_I for r in self.region_names], dtype=float)

    @property
    def _w_EE(self) -> np.ndarray:
        return np.array([self.params[r].w_EE for r in self.region_names], dtype=float)

    @property
    def _w_EI(self) -> np.ndarray:
        return np.array([self.params[r].w_EI for r in self.region_names], dtype=float)

    @property
    def _w_IE(self) -> np.ndarray:
        return np.array([self.params[r].w_IE for r in self.region_names], dtype=float)

    @property
    def _w_II(self) -> np.ndarray:
        return np.array([self.params[r].w_II for r in self.region_names], dtype=float)

    @property
    def _gain_E(self) -> np.ndarray:
        return np.array([self.params[r].gain_E for r in self.region_names], dtype=float)

    @property
    def _gain_I(self) -> np.ndarray:
        return np.array([self.params[r].gain_I for r in self.region_names], dtype=float)

    @property
    def _threshold_E(self) -> np.ndarray:
        return np.array([self.params[r].threshold_E for r in self.region_names], dtype=float)

    @property
    def _threshold_I(self) -> np.ndarray:
        return np.array([self.params[r].threshold_I for r in self.region_names], dtype=float)

    @staticmethod
    def _sigmoid(x: np.ndarray, gain: np.ndarray, threshold: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-gain * (x - threshold)))

    @staticmethod
    def neuromodulation_vector(neuromodulators: dict[str, np.ndarray]) -> np.ndarray:
        """Return vector [DA, NA, ACh, 5HT, GABA, Glu, CORT, ADR] per region."""
        return np.column_stack(
            [
                neuromodulators["dopamine"],
                neuromodulators["noradrenaline"],
                neuromodulators["acetylcholine"],
                neuromodulators["serotonin"],
                neuromodulators["gaba"],
                neuromodulators["glutamate"],
                neuromodulators["cortisol"],
                neuromodulators["adrenaline"],
            ]
        )

    def step(
        self,
        dt: float,
        external_e: np.ndarray,
        external_i: np.ndarray,
        neuromodulators: dict[str, np.ndarray] | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if dt <= 0:
            raise ValueError("dt musi być > 0")
        if external_e.shape != self.E.shape or external_i.shape != self.I.shape:
            raise ValueError("external_e/external_i muszą pasować rozmiarem do regionów")

        tau_E = self._tau_E
        tau_I = self._tau_I
        w_EE = self._w_EE
        w_EI = self._w_EI
        w_IE = self._w_IE
        w_II = self._w_II
        gain_E = self._gain_E
        gain_I = self._gain_I
        threshold_E = self._threshold_E
        threshold_I = self._threshold_I

        if neuromodulators is not None:
            nvec = self.neuromodulation_vector(neuromodulators)
            da, na, ach, ser, gaba, glu, cort, adr = [nvec[:, i] for i in range(8)]
            gain_E = gain_E * (1.0 + 0.35 * ach + 0.20 * da + 0.25 * na - 0.15 * ser)
            gain_I = gain_I * (1.0 + 0.30 * gaba + 0.10 * cort)
            threshold_E = threshold_E - 0.25 * glu + 0.20 * gaba - 0.10 * ach + 0.10 * cort
            threshold_I = threshold_I - 0.15 * glu + 0.15 * ser + 0.10 * adr
            w_EI = w_EI * (1.0 + 0.4 * gaba)
            w_IE = w_IE * (1.0 + 0.35 * glu)
            external_e = external_e + 0.08 * da + 0.10 * na + 0.07 * ach - 0.07 * ser + 0.06 * adr
            external_i = external_i + 0.10 * gaba - 0.05 * glu + 0.04 * cort
            tau_E = tau_E * (1.0 - 0.20 * ach + 0.08 * ser + 0.08 * cort)
            tau_I = tau_I * (1.0 - 0.15 * gaba + 0.05 * glu + 0.05 * adr)
            noise_scale = np.maximum(0.0, 0.03 + 0.05 * na + 0.03 * adr + 0.02 * da - 0.05 * gaba)
            external_e = external_e + np.random.normal(0.0, noise_scale, size=self.E.shape)

        input_E = w_EE * self.E - w_EI * self.I + external_e
        input_I = w_IE * self.E - w_II * self.I + external_i

        dE = (-self.E + self._sigmoid(input_E, gain_E, threshold_E)) / tau_E
        dI = (-self.I + self._sigmoid(input_I, gain_I, threshold_I)) / tau_I

        self.E = np.clip(self.E + dt * dE, 0.0, 1.0)
        self.I = np.clip(self.I + dt * dI, 0.0, 1.0)
        return self.E.copy(), self.I.copy()
