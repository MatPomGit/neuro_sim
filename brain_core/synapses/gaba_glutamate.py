from __future__ import annotations


def gaba_glutamate_effect(inhibition_drive: float, excitation_drive: float, gaba_tonic: float, glutamate_tonic: float) -> tuple[float, float]:
    """Compute GABA/Glutamate pair in [0, 1]."""
    gaba = min(1.0, max(0.0, gaba_tonic + 0.6 * inhibition_drive - 0.2 * excitation_drive))
    glutamate = min(1.0, max(0.0, glutamate_tonic + 0.6 * excitation_drive - 0.2 * inhibition_drive))
    return gaba, glutamate
