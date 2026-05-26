from __future__ import annotations


def dopamine_effect(reward_prediction_error: float, tonic_level: float) -> float:
    """Return phasic dopamine value in [0, 1]."""
    raw = tonic_level + 0.65 * reward_prediction_error
    return min(1.0, max(0.0, raw))
