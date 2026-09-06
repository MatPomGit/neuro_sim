"""Testy adaptera sekwencji triali do kanałów modelu poznawczego."""

from brain_core.experiments.protocols import TrialStimulus
from brain_core.simulation.task_drive import build_task_stimulus_fn


def test_visual_task_drives_visual_and_task_cue_channels() -> None:
    """Stroop powinien pobudzać kanał wzrokowy w czasie aktywnego trialu."""
    stimulus = TrialStimulus(0, 0.5, 1.0, {}, "incongruent")
    drive = build_task_stimulus_fn("stroop", [stimulus])

    assert drive(0.25) == {
        "visual": 0.0,
        "auditory": 0.0,
        "interoceptive": 0.0,
        "reward": 0.0,
        "threat": 0.0,
        "task_cue": 0.0,
    }
    active = drive(0.75)
    assert active["visual"] == 1.35
    assert active["auditory"] == 0.0
    assert active["task_cue"] == 1.35


def test_roving_oddball_drives_auditory_channel() -> None:
    """Roving oddball powinien pobudzać kanał słuchowy tej samej sekwencji."""
    stimulus = TrialStimulus(0, 0.2, 0.3, {}, "deviant")
    drive = build_task_stimulus_fn("roving_oddball", [stimulus])

    active = drive(0.3)
    assert active["auditory"] == 1.4
    assert active["visual"] == 0.0
    assert active["task_cue"] == 1.4


def test_drive_is_zero_after_trial_offset() -> None:
    """Po końcu trialu adapter nie może pozostawiać ukrytego pobudzenia."""
    stimulus = TrialStimulus(0, 0.2, 0.3, {}, "standard")
    drive = build_task_stimulus_fn("roving_oddball", [stimulus])

    assert all(value == 0.0 for value in drive(0.5).values())
