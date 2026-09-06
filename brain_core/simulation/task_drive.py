"""Adapter sekwencji triali do kanałów wejściowych modelu poznawczego."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from brain_core.experiments.protocols import TrialStimulus

StimulusChannels = dict[str, float]
StimulusFn = Callable[[float], StimulusChannels]

_CHANNELS = (
    "visual",
    "auditory",
    "interoceptive",
    "reward",
    "threat",
    "task_cue",
)


def _empty_drive() -> StimulusChannels:
    """Zwróć zerowy wektor kanałów wejściowych modelu."""
    return {name: 0.0 for name in _CHANNELS}


def _condition_gain(condition: str) -> float:
    """Wyznacz względną siłę napędu dla warunku eksperymentalnego."""
    return {
        "incongruent": 1.35,
        "nogo": 1.30,
        "target": 1.25,
        "deviant": 1.40,
        "standard": 0.80,
    }.get(condition, 1.0)


def build_task_stimulus_fn(
    task_name: str,
    stimuli: Sequence[TrialStimulus],
) -> StimulusFn:
    """Zbuduj funkcję bodźca modelu z tej samej sekwencji co scheduler triali.

    Adapter jest celowo prosty. Zadania wzrokowe pobudzają kanał ``visual``,
    roving oddball kanał ``auditory``, a każdy aktywny trial ustawia
    ``task_cue``. Pozostałe kanały pozostają zerowe. Dzięki temu dynamika modelu
    i późniejsze wyniki trialowe odnoszą się do tej samej osi czasu bodźców.

    Parameters
    ----------
    task_name:
        Nazwa zadania zgodna z rejestrem protokołów.
    stimuli:
        Uporządkowana sekwencja bodźców z czasem początku i trwania.

    Returns:
    -------
    StimulusFn
        Funkcja ``f(t)`` zwracająca komplet kanałów wejściowych modelu.
    """
    frozen_stimuli = tuple(stimuli)
    auditory_task = task_name in {"roving_oddball", "roving-oddball"}

    def stimulus_at_time(time_s: float) -> StimulusChannels:
        drive = _empty_drive()
        for stimulus in frozen_stimuli:
            onset = float(stimulus.onset_s)
            offset = onset + float(stimulus.duration_s)
            if onset <= time_s < offset:
                gain = _condition_gain(stimulus.condition)
                drive["task_cue"] = gain
                if auditory_task:
                    drive["auditory"] = gain
                else:
                    drive["visual"] = gain
                return drive
        return drive

    return stimulus_at_time
