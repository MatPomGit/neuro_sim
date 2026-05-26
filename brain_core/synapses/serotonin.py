from __future__ import annotations


def serotonin_effect(threat_signal: float, satiety_signal: float, baseline: float) -> float:
    """Return serotonin balance in [0, 1]."""
    raw = baseline + 0.45 * satiety_signal - 0.35 * threat_signal
    return min(1.0, max(0.0, raw))
