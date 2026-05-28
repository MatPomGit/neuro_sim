"""Neurovascular coupling helper for BOLD signal generation."""

from __future__ import annotations

import numpy as np



def neural_drive_from_activity(
    activity: np.ndarray,
    baseline: float = 0.0
) -> np.ndarray:
    """
    Przekształca aktywność neuronalną na nieujemny napęd naczyniowy.

    Args:
        activity (np.ndarray): Aktywność neuronalna.
        baseline (float): Poziom bazowy do odjęcia.

    Returns:
        np.ndarray: Napęd naczyniowy (nieujemny).
    """
    values = np.asarray(activity, dtype=float) - float(baseline)
    return np.maximum(values, 0.0)
