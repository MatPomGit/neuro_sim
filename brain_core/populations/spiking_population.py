from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class NeuralMassToSNNInput:
    """Kontrakt wejściowy: neural-mass -> SNN."""

    excitatory_drive_hz: np.ndarray
    inhibitory_drive_hz: np.ndarray
    sync_dt: float


@dataclass(frozen=True, slots=True)
class SNNToNeuralMassOutput:
    """Kontrakt wyjściowy: SNN -> neural-mass."""

    firing_rate_hz: np.ndarray
    mean_membrane_potential_mv: np.ndarray
    sync_dt: float


class Brian2SpikingPopulationAdapter:
    """Startowy adapter SNN.

    Implementacja jest celowo lekka: kontrakt danych i deterministyczny backend
    fallback, aby można było uruchamiać współsymulację bez opcjonalnej zależności.
    """

    backend_name = "brian2"

    def __init__(self, region_names: list[str], dt: float = 0.001):
        if not region_names:
            raise ValueError("region_names nie może być puste")
        if dt <= 0:
            raise ValueError("dt musi być > 0")

        self.region_names = region_names
        self.dt = float(dt)
        self._firing_rate_hz = np.zeros(len(region_names), dtype=float)
        self._membrane_mv = np.full(len(region_names), -65.0, dtype=float)

    def step(self, signal: NeuralMassToSNNInput) -> SNNToNeuralMassOutput:
        self._validate_input(signal)

        # Deterministyczny backend startowy: szybka aproksymacja transferu NM -> SNN.
        # W kolejnym kroku można podmienić wnętrze na pełny obiekt brian2.Network.
        target_rate = np.clip(signal.excitatory_drive_hz - 0.5 * signal.inhibitory_drive_hz, 0.0, 200.0)
        alpha = min(1.0, signal.sync_dt / max(self.dt, 1e-9))
        self._firing_rate_hz = (1.0 - alpha) * self._firing_rate_hz + alpha * target_rate
        self._membrane_mv = -70.0 + 0.15 * self._firing_rate_hz

        return SNNToNeuralMassOutput(
            firing_rate_hz=self._firing_rate_hz.copy(),
            mean_membrane_potential_mv=self._membrane_mv.copy(),
            sync_dt=signal.sync_dt,
        )

    def _validate_input(self, signal: NeuralMassToSNNInput) -> None:
        expected = (len(self.region_names),)
        if signal.excitatory_drive_hz.shape != expected or signal.inhibitory_drive_hz.shape != expected:
            raise ValueError("Rozmiar wejścia kontraktu NM->SNN nie pasuje do region_names")
        if signal.sync_dt <= 0:
            raise ValueError("sync_dt musi być > 0")
