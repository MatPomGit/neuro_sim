from __future__ import annotations

from typing import Any, Callable, Dict

from .scenarios import StimulusScenario, get_scenario
from .scenarios.types import CHANNELS

StimulusFn = Callable[[float], Dict[str, float]]


def build_stimulus_fn(scenario: StimulusScenario) -> StimulusFn:
    """Build a time-dependent stimulus function from a stable scenario schema."""

    normalized = scenario.normalized_channels()

    def stimulus(t: float) -> Dict[str, float]:
        """Zwróć amplitudy kanałów bodźca dla czasu ``t`` w sekundach.

        Wynikiem jest słownik ``{kanał: amplituda}`` dla wszystkich kanałów
        scenariusza. Puls aktywny w oknie czasowym nadpisuje baseline maksimum,
        a perturbacje dodają lub ustawiają wartość. Nieobsługiwany tryb zgłasza
        ``ValueError``.
        """
        u = {channel: normalized[channel].baseline for channel in CHANNELS}

        for channel in CHANNELS:
            profile = normalized[channel]
            for pulse in profile.pulses:
                if pulse.window.contains(t):
                    u[channel] = max(u[channel], pulse.amplitude)

        for perturbation in scenario.perturbations:
            if perturbation.window.contains(t):
                if perturbation.mode == "add":
                    u[perturbation.channel] = (
                        u.get(perturbation.channel, 0.0) + perturbation.delta
                    )
                elif perturbation.mode == "set":
                    u[perturbation.channel] = perturbation.delta
                else:
                    raise ValueError(
                        f"Nieobsługiwany tryb perturbacji: {perturbation.mode}"
                    )

        return u

    return stimulus


def resolve_stimulus_scenario(
    scenario_id: str | None = None, scenario: StimulusScenario | None = None
) -> Any:
    """Zwróć obiekt scenariusza bodźców z obiektu lub identyfikatora.

    Jeśli przekazano ``scenario``, jest zwracany bez zmian. W przeciwnym razie
    ładowany jest scenariusz ``scenario_id`` albo domyślny ``reward-learning``.
    """
    if scenario is not None:
        return scenario
    return get_scenario(scenario_id or "reward-learning")
