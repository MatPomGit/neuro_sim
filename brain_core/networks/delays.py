"""Obliczenia opóźnień przewodzenia w sieciach połączeń mózgowych."""

from __future__ import annotations

import numpy as np

from brain_core.data_contracts import (
    CONTRACT_B_NETWORKS_POPULATIONS,
    validate_delay_steps_contract,
    validate_regional_vector_contract,
    validate_square_matrix_contract,
)


class DelayBuffer:
    """
    Bufor pierścieniowy do obsługi opóźnień między połączeniami (per-connection delay).

    Atrybuty:
        delays_steps (np.ndarray): Macierz opóźnień [n_regions, n_regions].
        max_delay (int): Największe opóźnienie w krokach.
        _history (np.ndarray): Historia aktywności [max_delay+1, n_regions].
        _cursor (int): Indeks aktualnej pozycji w buforze.
    """

    def __init__(self, n_regions: int, delays_steps: np.ndarray) -> None:
        """
        Inicjalizuje bufor opóźnień.

        Args:
            n_regions (int): Liczba regionów.
            delays_steps (np.ndarray): Macierz opóźnień [n_regions, n_regions].

        Raises:
            ValueError: Jeśli macierz ma nieprawidłowy rozmiar lub zawiera wartości ujemne.
        """
        self.delays_steps: np.ndarray = validate_delay_steps_contract(
            delays_steps, n_regions
        )
        self.max_delay: int = int(np.max(self.delays_steps))
        self._history: np.ndarray = np.zeros(
            (self.max_delay + 1, n_regions), dtype=float
        )
        self._cursor: int = 0

    def push(self, activity: np.ndarray) -> None:
        """
        Dodaje nową aktywność do bufora.

        Args:
            activity (np.ndarray): Wektor aktywności [n_regions].

        Raises:
            ValueError: Jeśli wektor ma nieprawidłowy rozmiar.
        """
        activity = validate_regional_vector_contract(
            activity, self._history.shape[1], "activity"
        )
        self._cursor = (self._cursor + 1) % self._history.shape[0]
        self._history[self._cursor] = activity

    def delayed_activity_matrix(self) -> np.ndarray:
        """
        Zwraca macierz aktywności z uwzględnieniem opóźnień dla każdej pary połączeń.

        Returns:
            np.ndarray: Macierz [n_regions, n_regions] z opóźnioną aktywnością.
        """
        n = self._history.shape[1]
        out = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(n):
                delay = self.delays_steps[i, j]
                idx = (self._cursor - delay) % self._history.shape[0]
                out[i, j] = self._history[idx, j]
        return out


def delayed_coupling(
    connectivity: np.ndarray, delayed_matrix: np.ndarray
) -> np.ndarray:
    """
    Oblicza sprzężenie z uwzględnieniem opóźnień: coupling_i(t) = Σ_j C_ij * activity_j(t-delay_ij).

    Args:
        connectivity (np.ndarray): Macierz połączeń [n_regions, n_regions].
        delayed_matrix (np.ndarray): Macierz opóźnionej aktywności [n_regions, n_regions].

    Returns:
        np.ndarray: Wektor sprzężenia [n_regions].

    Raises:
        ValueError: Jeśli macierze mają różne rozmiary.
    """
    try:
        connectivity_arr = np.asarray(connectivity, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{CONTRACT_B_NETWORKS_POPULATIONS}: connectivity musi być macierzą numeryczną."
        ) from error
    if (
        connectivity_arr.ndim != 2
        or connectivity_arr.shape[0] != connectivity_arr.shape[1]
    ):
        raise ValueError(
            f"{CONTRACT_B_NETWORKS_POPULATIONS}: connectivity musi być kwadratową macierzą 2D."
        )
    n_regions = connectivity_arr.shape[0]
    connectivity_arr = validate_square_matrix_contract(
        connectivity_arr, n_regions, "connectivity", CONTRACT_B_NETWORKS_POPULATIONS
    )
    delayed_arr = validate_square_matrix_contract(
        delayed_matrix, n_regions, "delayed_matrix", CONTRACT_B_NETWORKS_POPULATIONS
    )
    return np.sum(connectivity_arr * delayed_arr, axis=1)
