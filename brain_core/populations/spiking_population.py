from __future__ import annotations

from dataclasses import dataclass

import numpy as np



@dataclass(frozen=True, slots=True)
class NeuralMassToSNNInput:
    """
    Kontrakt wejściowy: neural-mass → SNN.

    Atrybuty:
        excitatory_drive_hz (np.ndarray): Pobudzenie ekscytujące [Hz].
        inhibitory_drive_hz (np.ndarray): Pobudzenie hamujące [Hz].
        sync_dt (float): Krok synchronizacji [s].
    """
    excitatory_drive_hz: np.ndarray
    inhibitory_drive_hz: np.ndarray
    sync_dt: float



@dataclass(frozen=True, slots=True)
class SNNToNeuralMassOutput:
    """
    Kontrakt wyjściowy: SNN → neural-mass.

    Atrybuty:
        firing_rate_hz (np.ndarray): Częstość wyładowań [Hz].
        mean_membrane_potential_mv (np.ndarray): Średni potencjał błonowy [mV].
        sync_dt (float): Krok synchronizacji [s].
    """
    firing_rate_hz: np.ndarray
    mean_membrane_potential_mv: np.ndarray
    sync_dt: float



class Brian2SpikingPopulationAdapter:
    """
    Startowy adapter populacji SNN (brian2).

    Implementacja celowo uproszczona: kontrakt danych i deterministyczny backend
    fallback, aby umożliwić współsymulację bez opcjonalnej zależności.

    Atrybuty:
        region_names (list[str]): Nazwy regionów.
        dt (float): Krok symulacji [s].
        _firing_rate_hz (np.ndarray): Częstość wyładowań [Hz].
        _membrane_mv (np.ndarray): Potencjał błonowy [mV].
    """

    backend_name: str = "brian2"

    def __init__(self, region_names: list[str], dt: float = 0.001) -> None:
        """
        Inicjalizuje adapter SNN.

        Args:
            region_names (list[str]): Nazwy regionów.
            dt (float): Krok symulacji [s].

        Raises:
            ValueError: Jeśli region_names jest puste lub dt <= 0.
        """
        if not region_names:
            raise ValueError("region_names nie może być puste")
        if dt <= 0:
            raise ValueError("dt musi być > 0")

        self.region_names: list[str] = region_names
        self.dt: float = float(dt)
        self._firing_rate_hz: np.ndarray = np.zeros(len(region_names), dtype=float)
        self._membrane_mv: np.ndarray = np.full(len(region_names), -65.0, dtype=float)

    def step(self, signal: NeuralMassToSNNInput) -> SNNToNeuralMassOutput:
        """
        Wykonuje krok symulacji SNN na podstawie sygnału wejściowego.

        Args:
            signal (NeuralMassToSNNInput): Wejście z modelu neural-mass.

        Returns:
            SNNToNeuralMassOutput: Wyjście do modelu neural-mass.
        """
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
        """Waliduje kompletność i kształt kontraktu wejściowego NM->SNN."""
        if signal is None:
            raise ValueError("signal nie może być None")
        expected = (len(self.region_names),)
        if signal.excitatory_drive_hz.shape != expected or signal.inhibitory_drive_hz.shape != expected:
            raise ValueError("Rozmiar wejścia kontraktu NM->SNN nie pasuje do region_names")
        if signal.sync_dt <= 0:
            raise ValueError("sync_dt musi być > 0")
        if not np.all(np.isfinite(signal.excitatory_drive_hz)) or not np.all(np.isfinite(signal.inhibitory_drive_hz)):
            raise ValueError("Sygnały wejściowe muszą zawierać wyłącznie skończone wartości")
