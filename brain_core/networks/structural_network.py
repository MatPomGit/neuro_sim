"""Reprezentacja strukturalnej sieci mózgu używana przez silnik symulacji."""

from __future__ import annotations

import numpy as np

from brain_core.data_contracts import (
    CONTRACT_B_NETWORKS_POPULATIONS,
    validate_regional_vector_contract,
    validate_square_matrix_contract,
)


class StructuralNetwork:
    """
    Skierowana sieć strukturalna połączeń między regionami.

    Attributes:
        region_names (list[str]): Nazwy regionów.
        connectivity (np.ndarray): Macierz połączeń [n_regions, n_regions].
    """

    def __init__(self, region_names: list[str], connectivity: np.ndarray) -> None:
        """
        Inicjalizuje sieć strukturalną.

        Args:
            region_names (list[str]): Nazwy regionów.
            connectivity (np.ndarray): Macierz połączeń [n_regions, n_regions].

        Raises:
            ValueError: Jeśli macierz ma nieprawidłowy rozmiar.
        """
        n = len(region_names)
        self.region_names: list[str] = list(region_names)
        self.connectivity: np.ndarray = validate_square_matrix_contract(
            connectivity,
            n,
            "StructuralNetwork.connectivity",
            CONTRACT_B_NETWORKS_POPULATIONS,
        )

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
        delayed_activity = validate_regional_vector_contract(
            delayed_activity, len(self.region_names), "delayed_activity"
        )
        return self.connectivity @ delayed_activity
