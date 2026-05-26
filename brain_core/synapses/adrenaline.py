from __future__ import annotations


def adrenaline_effect(threat_signal: float, arousal_signal: float, noradrenaline_level: float, baseline: float) -> float:
    """Return adrenaline level in [0, 1]."""
    raw = baseline + 0.45 * threat_signal + 0.35 * arousal_signal + 0.20 * noradrenaline_level
    return min(1.0, max(0.0, raw))
