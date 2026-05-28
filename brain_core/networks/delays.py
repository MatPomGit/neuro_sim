from __future__ import annotations

import numpy as np



class DelayBuffer:
    """
    Bufor pierścieniowy do obsługi opóźnień między połączeniami (per-connection delay).

    Atrybuty:
        delays_steps (np.ndarray): Macierz opóźnień [n_regions, n_regions].
        max_delay (int): Największe opóźnienie w krokach.
        _history (np.ndarray): Historia aktywności [max_delay+1, n_regions].
        _cursor (int): Indeks aktualnej pozycji w buforze.
    """

    def __init__(self, n_regions: int, delays_steps: np.ndarray):
        """
        Inicjalizuje bufor opóźnień.

        Args:
            n_regions (int): Liczba regionów.
            delays_steps (np.ndarray): Macierz opóźnień [n_regions, n_regions].

        Raises:
            ValueError: Jeśli macierz ma nieprawidłowy rozmiar lub zawiera wartości ujemne.
        """
        if delays_steps.shape != (n_regions, n_regions):
            raise ValueError("delays_steps musi mieć rozmiar [n_regions, n_regions]")
        if np.any(delays_steps < 0):
            raise ValueError("delays_steps nie może zawierać wartości ujemnych")

        self.delays_steps: np.ndarray = delays_steps.astype(int)
        self.max_delay: int = int(np.max(self.delays_steps))
        self._history: np.ndarray = np.zeros((self.max_delay + 1, n_regions), dtype=float)
        self._cursor: int = 0

    def push(self, activity: np.ndarray) -> None:
        """
        Dodaje nową aktywność do bufora.

        Args:
            activity (np.ndarray): Wektor aktywności [n_regions].

        Raises:
            ValueError: Jeśli wektor ma nieprawidłowy rozmiar.
        """
        if activity.shape != (self._history.shape[1],):
            raise ValueError("activity musi mieć rozmiar [n_regions]")
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


def delayed_coupling(connectivity: np.ndarray, delayed_matrix: np.ndarray) -> np.ndarray:
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
    if connectivity.shape != delayed_matrix.shape:
        raise ValueError("connectivity i delayed_matrix muszą mieć ten sam rozmiar [n_regions, n_regions]")
    return np.sum(connectivity * delayed_matrix, axis=1)
