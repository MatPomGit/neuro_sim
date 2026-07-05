"""Model populacji neuronów impulsowych dla eksperymentów sieciowych."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

DEMO_SNN_REGION_NAME = "HIP"


@dataclass(frozen=True, slots=True)
class NeuralMassToSNNInput:
    """Kontrakt wejściowy neural-mass → demonstracyjny obwód SNN HIP.

    Parameters
    ----------
    excitatory_drive_hz:
        Jednowymiarowy wektor pobudzenia ekscytującego dla obwodu ``HIP`` [Hz].
        W bieżącym pilotażu oczekiwany kształt to ``(1,)``.
    inhibitory_drive_hz:
        Jednowymiarowy wektor pobudzenia hamującego dla obwodu ``HIP`` [Hz].
        Wartości muszą być skończone i mieć ten sam kształt co pobudzenie
        ekscytujące.
    sync_dt:
        Krok synchronizacji neural-mass ↔ SNN [s], większy od zera.
    """

    excitatory_drive_hz: np.ndarray
    inhibitory_drive_hz: np.ndarray
    sync_dt: float


@dataclass(frozen=True, slots=True)
class SNNToNeuralMassOutput:
    """Kontrakt wyjściowy demonstracyjnego obwodu SNN HIP → neural-mass.

    Parameters
    ----------
    firing_rate_hz:
        Jednowymiarowy wektor częstości wyładowań lokalnego obwodu ``HIP`` [Hz].
        W bieżącym pilotażu oczekiwany kształt to ``(1,)``.
    mean_membrane_potential_mv:
        Jednowymiarowy wektor średniego potencjału błonowego [mV], używany w
        raporcie diagnostycznym i walidacji skończoności.
    sync_dt:
        Krok synchronizacji [s], przenoszony z wejścia bez zmiany jednostki.
    """

    firing_rate_hz: np.ndarray
    mean_membrane_potential_mv: np.ndarray
    sync_dt: float


class Brian2SpikingPopulationAdapter:
    """Deterministyczny adapter jednego demonstracyjnego obwodu SNN HIP.

    Implementacja celowo pozostaje mała: utrzymuje kontrakt danych dla pilotażu
    hipokampa i deterministyczny backend zastępczy, bez dodawania kolejnych
    backendów ani deklarowania pełnego modelu biologicznego.

    Atrybuty:
        region_names (list[str]): Jednoelementowa lista ``["HIP"]``.
        dt (float): Wewnętrzny krok adaptera [s].
        _firing_rate_hz (np.ndarray): Częstość wyładowań [Hz].
        _membrane_mv (np.ndarray): Potencjał błonowy [mV].
    """

    backend_name: str = "brian2"

    def __init__(self, region_names: Sequence[str], dt: float = 0.001) -> None:
        """
        Inicjalizuje adapter SNN.

        Args:
            region_names (Sequence[str]): Jednoelementowa sekwencja z nazwą ``HIP``.
            dt (float): Krok symulacji [s].

        Raises:
            ValueError: Jeśli region_names nie wskazuje dokładnie ``HIP`` lub dt <= 0.
        """
        region_names_list = list(region_names)
        if region_names_list != [DEMO_SNN_REGION_NAME]:
            raise ValueError(
                "Bieżący adapter SNN obsługuje wyłącznie jeden obwód "
                f"demonstracyjny: {DEMO_SNN_REGION_NAME}"
            )
        if dt <= 0:
            raise ValueError("dt musi być > 0")

        self.region_names: list[str] = region_names_list
        self.dt: float = float(dt)
        self._firing_rate_hz: np.ndarray = np.zeros(len(region_names_list), dtype=float)
        self._membrane_mv: np.ndarray = np.full(
            len(region_names_list), -65.0, dtype=float
        )

    def step(self, signal: NeuralMassToSNNInput) -> SNNToNeuralMassOutput:
        """Wykonuje deterministyczny krok demonstracyjnego obwodu SNN HIP.

        Args:
            signal (NeuralMassToSNNInput): Wejście z modelu neural-mass w Hz.

        Returns:
            SNNToNeuralMassOutput: Wyjście w Hz i mV z tym samym ``sync_dt``.
        """
        self._validate_input(signal)

        # Deterministyczny backend startowy: szybka aproksymacja transferu NM -> SNN.
        # W kolejnym kroku można podmienić wnętrze na pełny obiekt brian2.Network.
        target_rate = np.clip(
            signal.excitatory_drive_hz - 0.5 * signal.inhibitory_drive_hz, 0.0, 200.0
        )
        alpha = min(1.0, signal.sync_dt / max(self.dt, 1e-9))
        self._firing_rate_hz = (
            1.0 - alpha
        ) * self._firing_rate_hz + alpha * target_rate
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
        excitatory_drive_hz = np.asarray(signal.excitatory_drive_hz, dtype=float)
        inhibitory_drive_hz = np.asarray(signal.inhibitory_drive_hz, dtype=float)
        if (
            excitatory_drive_hz.shape != expected
            or inhibitory_drive_hz.shape != expected
        ):
            raise ValueError(
                "Rozmiar wejścia kontraktu NM->SNN nie pasuje do region_names"
            )
        if signal.sync_dt <= 0:
            raise ValueError("sync_dt musi być > 0")
        if not np.all(np.isfinite(excitatory_drive_hz)) or not np.all(
            np.isfinite(inhibitory_drive_hz)
        ):
            raise ValueError(
                "Sygnały wejściowe muszą zawierać wyłącznie skończone wartości"
            )
