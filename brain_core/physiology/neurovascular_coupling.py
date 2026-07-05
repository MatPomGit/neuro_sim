"""Pomocnicze przekształcenia neuro-naczyniowe do generowania BOLD proxy."""

from __future__ import annotations

import numpy as np


def neural_drive_from_activity(
    activity: np.ndarray, baseline: float = 0.0
) -> np.ndarray:
    """
    Przekształca aktywność neuronalną na nieujemny napęd naczyniowy.

    Args:
        activity (np.ndarray): Aktywność neuronalna w jednostkach proxy modelu.
        baseline (float): Poziom bazowy w tej samej jednostce proxy, odejmowany
            przed obcięciem wartości ujemnych.

    Returns:
        np.ndarray: Nieujemny napęd naczyniowy/BOLD proxy w względnych
        jednostkach aktywności po odjęciu baseline.

    Notes:
    -----
    Funkcja opisuje metodologiczny etap sprzężenia neuro-naczyniowego: ujemne
    odchylenia od baseline nie zwiększają napędu BOLD, dlatego wynik należy
    interpretować jako uproszczony sygnał wejściowy do HRF.
    """
    values = np.asarray(activity, dtype=float) - float(baseline)
    return np.maximum(values, 0.0)
