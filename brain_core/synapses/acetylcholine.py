from __future__ import annotations


def acetylcholine_effect(attention_drive: float, novelty_drive: float, baseline: float) -> float:
    """Return acetylcholine level in [0, 1]."""
    raw = baseline + 0.5 * attention_drive + 0.3 * novelty_drive
    return min(1.0, max(0.0, raw))
