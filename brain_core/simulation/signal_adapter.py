from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from brain_core.populations.spiking_population import (
    NeuralMassToSNNInput,
    SNNToNeuralMassOutput,
)

SNNCouplingMode = Literal["report_only", "closed_loop"]
ALLOWED_SNN_COUPLING_MODES: tuple[str, ...] = ("report_only", "closed_loop")
DEMO_SNN_REGION_NAME = "HIP"


@dataclass(frozen=True, slots=True)
class ClosedLoopCouplingDrive:
    """Opisuje opóźniony sygnał sprzężenia SNN -> neural-mass.

    Parameters
    ----------
    drive:
        Wektor wejścia dodawanego do równań neural-mass w kolejnym kroku.
    regional_activity:
        Znormalizowana aktywność SNN po mapowaniu na regiony neural-mass.
    max_abs_amplitude:
        Maksymalna bezwzględna amplituda pojedynczej składowej sprzężenia.
    """

    drive: np.ndarray
    regional_activity: np.ndarray
    max_abs_amplitude: float


@dataclass(frozen=True, slots=True)
class SNNPopulationMapping:
    """Mapowanie jednego demonstracyjnego obwodu SNN HIP na neural-mass.

    Parameters
    ----------
    snn_region_names:
        Jednoelementowa krotka z nazwą mapowanego obwodu SNN. W bieżącym
        pilotażu dozwolony jest wyłącznie region ``HIP``.
    neural_mass_region_names:
        Nazwy regionów neural-mass w kolejności kolumn sygnału. Krotka musi
        zawierać ``HIP``, aby mapowanie było jawne i nazwane.

    Raises
    ------
    ValueError
        Gdy konfiguracja próbuje mapować więcej niż jeden obwód SNN albo region
        inny niż demonstracyjny hipokamp ``HIP``.
    """

    snn_region_names: tuple[str, ...]
    neural_mass_region_names: tuple[str, ...]

    def __post_init__(self) -> None:
        """Waliduje, że pilotaż SNN obejmuje dokładnie jeden obwód HIP."""
        if self.snn_region_names != (DEMO_SNN_REGION_NAME,):
            raise ValueError(
                "Bieżący pilotaż SNN obsługuje dokładnie jeden obwód "
                f"demonstracyjny: {DEMO_SNN_REGION_NAME}"
            )

    def indices_in_neural_mass(self) -> np.ndarray:
        """Zwraca indeks obwodu HIP w wektorze regionów neural-mass."""
        index_by_name = {
            name: idx for idx, name in enumerate(self.neural_mass_region_names)
        }
        indices: list[int] = []
        for region in self.snn_region_names:
            if region not in index_by_name:
                raise ValueError(
                    f"Region SNN '{region}' nie istnieje w regionach neural-mass"
                )
            indices.append(index_by_name[region])
        return np.asarray(indices, dtype=int)


class CouplingSignalAdapter:
    """Adapter sygnału sprzęgającego neural-mass z demonstracyjnym SNN HIP.

    Kontrakt I/O:
    - obsługiwany jest dokładnie jeden lokalny obwód demonstracyjny ``HIP``,
    - wejście do SNN jest aktualizowane co ``sync_dt`` i ma jednostki Hz,
    - wyjście z SNN zwracane jest jako aktywność regionalna ``fraction`` [0, 1],
    - sprzężenie closed-loop jest ograniczone amplitudowo i stosowane jako
      wejście porównawcze, nie jako pełny model biologiczny,
    - mapowanie regionów opiera się wyłącznie o jawne nazwy, bez dopasowania po
      niezwalidowanym indeksie.
    """

    MAX_FIRING_RATE_HZ: float = 100.0

    def __init__(self, mapping: SNNPopulationMapping, sync_dt: float) -> None:
        """Inicjalizuje adapter z jawnym mapowaniem regionów i krokiem synchronizacji."""
        if sync_dt <= 0:
            raise ValueError("sync_dt musi być > 0")
        self.mapping: SNNPopulationMapping = mapping
        self.sync_dt: float = float(sync_dt)
        self._indices: np.ndarray = mapping.indices_in_neural_mass()

    def rate_to_spike_drive(
        self, excitatory_rate_hz: np.ndarray, inhibitory_rate_hz: np.ndarray
    ) -> NeuralMassToSNNInput:
        """Konwertuje regionalne częstości neural-mass [Hz] na wejście SNN HIP."""
        exc_arr = np.asarray(excitatory_rate_hz)
        inh_arr = np.asarray(inhibitory_rate_hz)
        self._validate_nm_vector(exc_arr, "excitatory_rate_hz")
        self._validate_nm_vector(inh_arr, "inhibitory_rate_hz")
        return NeuralMassToSNNInput(
            excitatory_drive_hz=np.asarray(exc_arr[self._indices], dtype=float),
            inhibitory_drive_hz=np.asarray(inh_arr[self._indices], dtype=float),
            sync_dt=self.sync_dt,
        )

    def spike_summary_to_regional_activity(
        self, snn_output: SNNToNeuralMassOutput, n_regions: int
    ) -> np.ndarray:
        """Konwertuje wyjście SNN HIP [Hz] na aktywność regionalną ``fraction``."""
        if n_regions != len(self.mapping.neural_mass_region_names):
            raise ValueError(
                f"n_regions ({n_regions}) must match the number of neural mass regions "
                f"({len(self.mapping.neural_mass_region_names)}) in the mapping"
            )
        expected_shape = (len(self.mapping.snn_region_names),)
        if snn_output.firing_rate_hz.shape != expected_shape:
            raise ValueError("Niepoprawny rozmiar firing_rate_hz względem mapowania")
        if snn_output.mean_membrane_potential_mv.shape != expected_shape:
            raise ValueError(
                "Niepoprawny rozmiar mean_membrane_potential_mv względem mapowania"
            )
        if snn_output.sync_dt <= 0:
            raise ValueError("sync_dt na wyjściu SNN musi być > 0")
        if not np.isclose(float(snn_output.sync_dt), self.sync_dt):
            raise ValueError("sync_dt na wyjściu SNN musi odpowiadać sync_dt adaptera")
        if not np.all(np.isfinite(snn_output.firing_rate_hz)) or not np.all(
            np.isfinite(snn_output.mean_membrane_potential_mv)
        ):
            raise ValueError("Wyjście SNN musi zawierać wyłącznie wartości skończone")

        regional_activity = np.zeros(n_regions, dtype=float)
        normalized = np.clip(
            snn_output.firing_rate_hz / self.MAX_FIRING_RATE_HZ, 0.0, 1.0
        )
        regional_activity[self._indices] = normalized
        return regional_activity

    def spike_summary_to_closed_loop_drive(
        self,
        snn_output: SNNToNeuralMassOutput,
        n_regions: int,
        coupling_gain: np.ndarray | float,
        max_abs_amplitude: float,
    ) -> ClosedLoopCouplingDrive:
        """Buduje ograniczone wejście SNN dla kolejnego kroku neural-mass.

        Parameters
        ----------
        snn_output:
            Podsumowanie aktywności SNN dla mapowanych regionów.
        n_regions:
            Liczba regionów w modelu neural-mass.
        coupling_gain:
            Skalar albo wektor wzmocnień dla populacji SNN.
        max_abs_amplitude:
            Górne ograniczenie bezwzględnej amplitudy wejścia zwrotnego.

        Returns
        -------
        ClosedLoopCouplingDrive
            Wektor wejścia, który należy zastosować dopiero w następnym kroku
            neural-mass, oraz aktywność regionalna użyta do jego wyznaczenia.

        Raises
        ------
        ValueError
            Gdy wzmocnienie lub amplituda są niepoprawne.
        """
        if not np.isfinite(max_abs_amplitude) or max_abs_amplitude <= 0:
            raise ValueError("max_abs_amplitude musi być skończoną liczbą > 0")

        regional_activity = self.spike_summary_to_regional_activity(
            snn_output=snn_output,
            n_regions=n_regions,
        )
        gain_arr = np.asarray(coupling_gain, dtype=float)
        if gain_arr.ndim == 0:
            mapped_gain = np.full(len(self._indices), float(gain_arr), dtype=float)
        elif gain_arr.shape == (len(self._indices),):
            mapped_gain = gain_arr
        else:
            raise ValueError(
                "coupling_gain musi być skalarem albo wektorem regionów SNN"
            )
        if not np.all(np.isfinite(mapped_gain)) or np.any(mapped_gain < 0.0):
            raise ValueError("coupling_gain musi zawierać skończone wartości >= 0")

        drive = np.zeros(n_regions, dtype=float)
        centered_activity = regional_activity[self._indices] - 0.5
        drive[self._indices] = np.clip(
            mapped_gain * centered_activity,
            -max_abs_amplitude,
            max_abs_amplitude,
        )
        return ClosedLoopCouplingDrive(
            drive=drive,
            regional_activity=regional_activity,
            max_abs_amplitude=float(max_abs_amplitude),
        )

    def _validate_nm_vector(self, signal: np.ndarray, name: str) -> None:
        """Waliduje kształt i skończoność wektora sygnału neural-mass."""
        signal_arr = np.asarray(signal)
        expected_shape = (len(self.mapping.neural_mass_region_names),)
        if signal_arr.shape != expected_shape:
            raise ValueError(f"{name} musi mieć rozmiar {expected_shape}")
        if not np.all(np.isfinite(signal_arr)):
            raise ValueError(f"{name} musi zawierać wyłącznie wartości skończone")
