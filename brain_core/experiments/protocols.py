from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProtocolPhase(str, Enum):
    TRAIN = "train"
    TEST = "test"


@dataclass(frozen=True, slots=True)
class ProtocolStep:
    phase: ProtocolPhase
    duration_s: float
    label: str = ""


@dataclass(frozen=True, slots=True)
class ExperimentProtocol:
    name: str
    steps: tuple[ProtocolStep, ...]

    def total_duration(self, phase: ProtocolPhase | None = None) -> float:
        if phase is None:
            return sum(step.duration_s for step in self.steps)
        return sum(step.duration_s for step in self.steps if step.phase == phase)


def default_train_test_protocol() -> ExperimentProtocol:
    return ExperimentProtocol(
        name="default_train_test",
        steps=(
            ProtocolStep(phase=ProtocolPhase.TRAIN, duration_s=30.0, label="train_baseline"),
            ProtocolStep(phase=ProtocolPhase.TRAIN, duration_s=30.0, label="train_perturbed"),
            ProtocolStep(phase=ProtocolPhase.TEST, duration_s=20.0, label="test_recall"),
        ),
    )
