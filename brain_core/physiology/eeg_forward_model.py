
"""
Modele EEG (forward/inverse) oparte o macierz leadfield.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np



@dataclass(frozen=True)
class ForwardModelConfig:
    """
    Konfiguracja wariantów modelowania forward EEG.

    Attributes:
        sensor_noise_std (float): Odchylenie standardowe szumu sensorycznego.
        reference (str): Typ referencji ('none' | 'average').
    """
    sensor_noise_std: float = 0.0
    reference: str = "none"  # none | average



class EEGForwardModel:
    """
    Liniowy model forward EEG rzutujący źródła regionalne na sensory.

    Attributes:
        leadfield (np.ndarray): Macierz leadfield [n_sensors, n_sources].
        config (ForwardModelConfig): Konfiguracja modelu.
    """

    def __init__(self, leadfield: np.ndarray, config: ForwardModelConfig | None = None) -> None:
        """
        Inicjalizuje model forward EEG.

        Args:
            leadfield (np.ndarray): Macierz leadfield [n_sensors, n_sources].
            config (ForwardModelConfig | None): Konfiguracja modelu.

        Raises:
            ValueError: Jeśli leadfield ma nieprawidłowy kształt lub jest pusta.
        """
        lf = np.asarray(leadfield, dtype=float)
        if lf.ndim != 2:
            raise ValueError("Leadfield must be a 2D matrix [n_sensors, n_sources].")
        if lf.shape[0] == 0 or lf.shape[1] == 0:
            raise ValueError("Leadfield cannot be empty.")
        self.leadfield: np.ndarray = lf
        self.config: ForwardModelConfig = config or ForwardModelConfig()

    @property
    def n_sensors(self) -> int:
        """Liczba sensorów EEG."""
        return int(self.leadfield.shape[0])

    @property
    def n_sources(self) -> int:
        """Liczba źródeł regionalnych."""
        return int(self.leadfield.shape[1])

    def _apply_reference(self, eeg: np.ndarray) -> np.ndarray:
        """
        Nakłada referencję na sygnał EEG.

        Args:
            eeg (np.ndarray): Sygnał EEG.

        Returns:
            np.ndarray: Sygnał EEG po referencji.

        Raises:
            ValueError: Jeśli typ referencji jest nieobsługiwany.
        """
        if self.config.reference == "none":
            return eeg
        if self.config.reference == "average":
            if eeg.ndim == 1:
                return eeg - np.mean(eeg)
            return eeg - np.mean(eeg, axis=-1, keepdims=True)
        raise ValueError("Unsupported reference. Use 'none' or 'average'.")

    def project(self, source_activity: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
        """
        Rzutuje aktywność źródeł na sensory EEG.

        Args:
            source_activity (np.ndarray): Aktywność źródeł [n_sources] lub [n_samples, n_sources].
            rng (np.random.Generator | None): Generator losowy do szumu.

        Returns:
            np.ndarray: Sygnał EEG [n_sensors] lub [n_samples, n_sensors].

        Raises:
            ValueError: Jeśli wejście ma niepoprawny kształt.
        """
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
    """
    Rozwiązania odwrotne do odzyskiwania aktywności źródeł z przestrzeni sensorów EEG.

    Attributes:
        leadfield (np.ndarray): Macierz leadfield [n_sensors, n_sources].
    """

    def __init__(self, leadfield: np.ndarray) -> None:
        """
        Inicjalizuje solver odwrotny EEG.

        Args:
            leadfield (np.ndarray): Macierz leadfield [n_sensors, n_sources].

        Raises:
            ValueError: Jeśli leadfield ma nieprawidłowy kształt.
        """
        lf = np.asarray(leadfield, dtype=float)
        if lf.ndim != 2:
            raise ValueError("Leadfield must be a 2D matrix [n_sensors, n_sources].")
        self.leadfield: np.ndarray = lf

    def _solve(self, eeg: np.ndarray, operator: np.ndarray) -> np.ndarray:
        """
        Pomocnicza funkcja do rozwiązywania równań odwrotnych.

        Args:
            eeg (np.ndarray): Sygnał EEG [n_sensors] lub [n_samples, n_sensors].
            operator (np.ndarray): Macierz operatora odwrotnego.

        Returns:
            np.ndarray: Odtworzona aktywność źródeł.

        Raises:
            ValueError: Jeśli wejście ma niepoprawny kształt.
        """
        y = np.asarray(eeg, dtype=float)
        if y.ndim == 1:
            return operator @ y
        if y.ndim == 2:
            return y @ operator.T
        raise ValueError("eeg must have shape [n_sensors] or [n_samples, n_sensors].")

    def minimum_norm(self, eeg: np.ndarray, lam: float = 1e-2) -> np.ndarray:
        """
        Odwrotność minimum normy L2 (MNE, ridge).

        Args:
            eeg (np.ndarray): Sygnał EEG.
            lam (float): Parametr regularizacji.

        Returns:
            np.ndarray: Odtworzona aktywność źródeł.

        Raises:
            ValueError: Jeśli lam <= 0.
        """
        if lam <= 0:
            raise ValueError("lam must be > 0")
        g = self.leadfield
        inv = np.linalg.inv(g @ g.T + lam * np.eye(g.shape[0]))
        operator = g.T @ inv
        return self._solve(eeg, operator)

    def weighted_minimum_norm(
        self,
        eeg: np.ndarray,
        lam: float = 1e-2,
        depth: np.ndarray | None = None
    ) -> np.ndarray:
        """
        Odwrotność minimum normy z wagami głębokości (priorytet diagonalny).

        Args:
            eeg (np.ndarray): Sygnał EEG.
            lam (float): Parametr regularizacji.
            depth (np.ndarray | None): Wektory wag głębokości [n_sources].

        Returns:
            np.ndarray: Odtworzona aktywność źródeł.

        Raises:
            ValueError: Jeśli parametry są niepoprawne.
        """
        if lam <= 0:
            raise ValueError("lam must be > 0")
        g = self.leadfield
        n_sources = g.shape[1]
        d = np.ones(n_sources, dtype=float) if depth is None else np.asarray(depth, dtype=float)
        if d.shape != (n_sources,):
            raise ValueError("depth must have shape [n_sources]")
        if np.any(d <= 0):
            raise ValueError("depth weights must be positive")
        gw = g * d
        inv = np.linalg.inv(gw @ gw.T + lam * np.eye(g.shape[0]))
        operator = (d[:, None] * gw.T) @ inv
        return self._solve(eeg, operator)
