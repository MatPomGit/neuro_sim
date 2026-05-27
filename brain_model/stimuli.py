from __future__ import annotations

from typing import Callable, Dict

from .scenarios import StimulusScenario, get_scenario
from .scenarios.types import CHANNELS
from typing import Any

StimulusFn = Callable[[float], Dict[str, float]]


def build_stimulus_fn(scenario: StimulusScenario) -> StimulusFn:
    """Build a time-dependent stimulus function from a stable scenario schema."""

    normalized = scenario.normalized_channels()

    def stimulus(t: float) -> Dict[str, float]:
        """Opis funkcji stimulus."""
        u = {channel: normalized[channel].baseline for channel in CHANNELS}

        for channel in CHANNELS:
            profile = normalized[channel]
            for pulse in profile.pulses:
                if pulse.window.contains(t):
                    u[channel] = max(u[channel], pulse.amplitude)

        for perturbation in scenario.perturbations:
            if perturbation.window.contains(t):
                if perturbation.mode == "add":
                    u[perturbation.channel] = u.get(perturbation.channel, 0.0) + perturbation.delta
                elif perturbation.mode == "set":
                    u[perturbation.channel] = perturbation.delta
                else:
                    raise ValueError(f"Nieobsługiwany tryb perturbacji: {perturbation.mode}")

        return u

    return stimulus


def resolve_stimulus_scenario(scenario_id: str | None = None, scenario: StimulusScenario | None = None) -> Any:
    """Opis funkcji resolve_stimulus_scenario."""
    if scenario is not None:
        return scenario
    return get_scenario(scenario_id or "reward-learning")
