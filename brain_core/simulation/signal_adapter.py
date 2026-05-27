from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from brain_core.populations.spiking_population import NeuralMassToSNNInput, SNNToNeuralMassOutput


@dataclass(frozen=True, slots=True)
class SNNPopulationMapping:
    """Mapowanie regionów modelu regionalnego na populacje SNN."""

    snn_region_names: tuple[str, ...]
    neural_mass_region_names: tuple[str, ...]

    def indices_in_neural_mass(self) -> np.ndarray:
        """Zwraca indeksy populacji SNN w wektorze regionów neural-mass."""
        index_by_name = {name: idx for idx, name in enumerate(self.neural_mass_region_names)}
        indices: list[int] = []
        for region in self.snn_region_names:
            if region not in index_by_name:
                raise ValueError(f"Region SNN '{region}' nie istnieje w regionach neural-mass")
            indices.append(index_by_name[region])
        return np.asarray(indices, dtype=int)


class CouplingSignalAdapter:
    """Adapter sygnału sprzęgającego między neural-mass i wybranym obwodem SNN.

    Kontrakt I/O:
    - wejście do SNN jest aktualizowane co ``sync_dt`` i ma jednostki Hz,
    - wyjście z SNN zwracane jest jako aktywność regionalna [0, 1],
    - mapowanie regionów opiera się wyłącznie o jawny słownik nazw.
    """

    MAX_FIRING_RATE_HZ = 100.0

    def __init__(self, mapping: SNNPopulationMapping, sync_dt: float):
        if sync_dt <= 0:
            raise ValueError("sync_dt musi być > 0")
        self.mapping = mapping
        self.sync_dt = float(sync_dt)
        self._indices = mapping.indices_in_neural_mass()

    def rate_to_spike_drive(self, excitatory_rate_hz: np.ndarray, inhibitory_rate_hz: np.ndarray) -> NeuralMassToSNNInput:
        """Konwersja aktywności regionalnej do pobudzenia SNN (Hz)."""
        self._validate_nm_vector(excitatory_rate_hz, "excitatory_rate_hz")
        self._validate_nm_vector(inhibitory_rate_hz, "inhibitory_rate_hz")
        return NeuralMassToSNNInput(
            excitatory_drive_hz=np.asarray(excitatory_rate_hz[self._indices], dtype=float),
            inhibitory_drive_hz=np.asarray(inhibitory_rate_hz[self._indices], dtype=float),
            sync_dt=self.sync_dt,
        )

    def spike_summary_to_regional_activity(self, snn_output: SNNToNeuralMassOutput, n_regions: int) -> np.ndarray:
        """Konwersja podsumowania SNN do znormalizowanej aktywności regionalnej [0, 1]."""
        if n_regions != len(self.mapping.neural_mass_region_names):
            raise ValueError(
                f"n_regions ({n_regions}) must match the number of neural mass regions "
                f"({len(self.mapping.neural_mass_region_names)}) in the mapping"
            )
        if snn_output.firing_rate_hz.shape != (len(self.mapping.snn_region_names),):
            raise ValueError("Niepoprawny rozmiar firing_rate_hz względem mapowania")
        if snn_output.sync_dt <= 0:
            raise ValueError("sync_dt na wyjściu SNN musi być > 0")

        regional_activity = np.zeros(n_regions, dtype=float)
        normalized = np.clip(snn_output.firing_rate_hz / self.MAX_FIRING_RATE_HZ, 0.0, 1.0)
        regional_activity[self._indices] = normalized
        return regional_activity

    def _validate_nm_vector(self, signal: np.ndarray, name: str) -> None:
        expected_shape = (len(self.mapping.neural_mass_region_names),)
        if signal.shape != expected_shape:
            raise ValueError(f"{name} musi mieć rozmiar {expected_shape}")
        if not np.all(np.isfinite(signal)):
            raise ValueError(f"{name} musi zawierać wyłącznie wartości skończone")
