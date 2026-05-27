from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BehaviorSample:
    """Opis klasy BehaviorSample."""
    decision: str
    latency: float
    confidence: float
    decision_score: float


def map_behavior_state(x: Any, idx: dict[str, int], dt: float, step_index: int, decision_threshold: float, confidence_gain: float) -> BehaviorSample:
    """Map key module states into behavior readout (decision, latency, confidence)."""
    exec_level = float(x[idx["EXEC"]])
    val_level = float(x[idx["VAL"]])
    mot_level = float(x[idx["MOT"]])
    gw_level = float(x[idx["GW"]])

    decision_score = 0.34 * exec_level + 0.22 * val_level + 0.22 * mot_level + 0.22 * gw_level

    if decision_score >= decision_threshold:
        if val_level >= 0.66:
            decision = "reward-approach"
        elif val_level <= 0.34:
            decision = "avoid"
        else:
            decision = "explore"
    else:
        decision = "wait"

    confidence_raw = confidence_gain * (decision_score - decision_threshold)
    confidence = max(0.0, min(1.0, 0.5 + confidence_raw))

    latency = float((step_index + 1) * dt)

    return BehaviorSample(
        decision=decision,
        latency=latency,
        confidence=confidence,
        decision_score=decision_score,
    )
