from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

CHANNELS: Tuple[str, ...] = ("visual", "auditory", "task_cue", "threat", "reward", "interoceptive")
SCENARIO_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class TimeWindow:
    start: float
    end: float

    def contains(self, t: float) -> bool:
        return self.start < t < self.end


@dataclass(frozen=True)
class Pulse:
    window: TimeWindow
    amplitude: float


@dataclass(frozen=True)
class ChannelProfile:
    baseline: float = 0.0
    pulses: List[Pulse] = field(default_factory=list)


@dataclass(frozen=True)
class StimulusPerturbation:
    channel: str
    window: TimeWindow
    delta: float
    mode: str = "add"


@dataclass(frozen=True)
class StimulusScenario:
    # Stała struktura scenariusza: zawsze te same pola.
    id: str
    name: str
    description: str
    schema_version: str = SCENARIO_SCHEMA_VERSION
    duration_hint: float = 45.0
    channels: Dict[str, ChannelProfile] = field(default_factory=dict)
    perturbations: List[StimulusPerturbation] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    phases: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def normalized_channels(self) -> Dict[str, ChannelProfile]:
        return {channel: self.channels.get(channel, ChannelProfile()) for channel in CHANNELS}

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.id,
            "scenario_name": self.name,
            "scenario_description": self.description,
            "schema_version": self.schema_version,
            "duration_hint": self.duration_hint,
            "tags": list(self.tags),
            "phases": list(self.phases),
            "events": list(self.events),
            "context": dict(self.context),
        }
