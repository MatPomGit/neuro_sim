"""Pomocnicze funkcje raportowania końcowego eksperymentu."""

from __future__ import annotations

import numpy as np

from brain_core.analysis.signal_metrics import comparative_report


def final_experiment_report(
    eeg_simulated: np.ndarray,
    eeg_target: np.ndarray,
    fmri_simulated: np.ndarray,
    fmri_target: np.ndarray,
    behavior_simulated: np.ndarray,
    behavior_target: np.ndarray,
) -> dict[str, dict[str, float]]:
    """Buduje raport porównawczy dla sygnałów EEG, fMRI i zachowania."""
    return {
        "eeg": comparative_report(eeg_simulated, eeg_target),
        "fmri": comparative_report(fmri_simulated, fmri_target),
        "behavior": comparative_report(behavior_simulated, behavior_target),
    }
