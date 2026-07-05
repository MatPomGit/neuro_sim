"""Budowanie funkcji bodźców czasowych na podstawie scenariuszy eksperymentalnych."""

from __future__ import annotations

from typing import Any, Callable, Dict

from .scenarios import StimulusScenario, get_scenario
from .scenarios.types import CHANNELS

StimulusFn = Callable[[float], Dict[str, float]]


def build_stimulus_fn(scenario: StimulusScenario) -> StimulusFn:
    """Zbuduj funkcję bodźca zależną od czasu dla stabilnego schematu scenariusza.

    Parameters
    ----------
    scenario:
        Scenariusz z kanałami bodźców, pulsami i perturbacjami opisanymi
        w sekundach oraz bezwymiarowych amplitudach.

    Returns:
    -------
    StimulusFn
        Funkcja ``stimulus(t)``, która dla czasu ``t`` w sekundach zwraca
        słownik amplitud kanałów ``{channel: amplitude}`` w skali scenariusza.

    Raises:
    ------
    ValueError
        Zgłaszany dopiero podczas wywołania zwróconej funkcji, jeśli aktywna
        perturbacja używa trybu innego niż ``"add"`` albo ``"set"``.
    """

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

    Parameters
    ----------
    scenario_id:
        Identyfikator scenariusza do załadowania; ``None`` oznacza domyślny
        scenariusz ``"reward-learning"``.
    scenario:
        Gotowy obiekt scenariusza. Jeśli jest podany, ma pierwszeństwo nad
        ``scenario_id`` i nie jest kopiowany.

    Returns:
    -------
    StimulusScenario
        Scenariusz wejściowy albo scenariusz odczytany z rejestru.

    Raises:
    ------
    KeyError
        Może zostać propagowany z ``get_scenario`` dla nieznanego
        identyfikatora scenariusza.
    """
    if scenario is not None:
        return scenario
    return get_scenario(scenario_id or "reward-learning")
