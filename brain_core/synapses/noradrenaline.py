from __future__ import annotations


def noradrenaline_effect(prediction_error: float, threat_signal: float, tonic_level: float) -> float:
    """Return noradrenaline level in [0, 1]."""
    raw = tonic_level + 0.45 * prediction_error + 0.35 * threat_signal
    return min(1.0, max(0.0, raw))
