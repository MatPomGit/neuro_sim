from __future__ import annotations

import numpy as np


class StructuralNetwork:
    """
    Skierowana sieć strukturalna połączeń między regionami.

    Attributes:
        region_names (list[str]): Nazwy regionów.
        connectivity (np.ndarray): Macierz połączeń [n_regions, n_regions].
    """

    def __init__(self, region_names: list[str], connectivity: np.ndarray):
        """
        Inicjalizuje sieć strukturalną.

        Args:
            region_names (list[str]): Nazwy regionów.
            connectivity (np.ndarray): Macierz połączeń [n_regions, n_regions].

        Raises:
            ValueError: Jeśli macierz ma nieprawidłowy rozmiar.
        """
        n = len(region_names)
        if connectivity.shape != (n, n):
            raise ValueError("connectivity musi mieć rozmiar [n_regions, n_regions]")
        self.region_names = region_names
        self.connectivity = connectivity.astype(float)

    def coupling(self, delayed_activity: np.ndarray) -> np.ndarray:
        """
        Oblicza sprzężenie sieciowe na podstawie opóźnionej aktywności.

        Args:
            delayed_activity (np.ndarray): Wektor aktywności [n_regions].

        Returns:
            np.ndarray: Wynik sprzężenia.

        Raises:
            ValueError: Jeśli wektor ma nieprawidłowy rozmiar.
        """
        if delayed_activity.shape != (len(self.region_names),):
            raise ValueError("delayed_activity musi mieć rozmiar [n_regions]")
        return self.connectivity @ delayed_activity
