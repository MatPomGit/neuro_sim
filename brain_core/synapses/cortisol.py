from __future__ import annotations


def cortisol_effect(threat_signal: float, uncertainty_signal: float, serotonin_level: float, baseline: float) -> float:
    """Return cortisol level in [0, 1]."""
    raw = baseline + 0.50 * threat_signal + 0.35 * uncertainty_signal - 0.30 * serotonin_level
    return min(1.0, max(0.0, raw))
