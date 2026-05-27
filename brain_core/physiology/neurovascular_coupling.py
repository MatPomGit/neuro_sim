"""Neurovascular coupling helper for BOLD signal generation."""

from __future__ import annotations

import numpy as np


def neural_drive_from_activity(activity: np.ndarray, baseline: float = 0.0) -> np.ndarray:
    """Convert neural activity into non-negative vascular drive."""
    values = np.asarray(activity, dtype=float) - float(baseline)
    return np.maximum(values, 0.0)
