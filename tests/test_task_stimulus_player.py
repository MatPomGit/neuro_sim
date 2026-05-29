"""Testy regresyjne odtwarzacza bodźców zadań poznawczych."""

from brain_core.experiments.protocols import TrialStimulus
from brain_core.simulation.scheduler import TaskStimulusPlayer
from brain_core.simulation.state import SimulationState


def test_task_stimulus_player_sorts_stimuli_before_playback() -> None:
    """Weryfikuje, że nieposortowane wejście jest odtwarzane chronologicznie."""
    stimuli = [
        TrialStimulus(
            trial_id=2, onset_s=2.0, duration_s=0.5, payload={}, condition="late"
        ),
        TrialStimulus(
            trial_id=1, onset_s=1.0, duration_s=0.5, payload={}, condition="early"
        ),
    ]
    player = TaskStimulusPlayer(stimuli=stimuli)
    state = SimulationState(time=1.5)

    player.update(state, dt=0.1)

    assert [event["trial_id"] for event in state.metrics["trial_events"]] == [1]
    assert player.cursor == 1

    # Advance time to cover the second stimulus
    state.time = 2.5
    player.update(state, dt=0.1)

    assert [event["trial_id"] for event in state.metrics["trial_events"]] == [1, 2]
    assert player.cursor == 2


def test_task_stimulus_player_updates_regional_state() -> None:
    """Weryfikuje przekład bodźca na wejście regionalne stanu symulacji."""
    stimulus = TrialStimulus(
        trial_id=1,
        onset_s=0.0,
        duration_s=0.5,
        payload={},
        condition="incongruent",
        regional_input={"ACC": 1.35, "DLPFC": 0.675},
    )
    player = TaskStimulusPlayer(stimuli=[stimulus])
    state = SimulationState(time=0.0)

    player.update(state, dt=0.1)

    assert state.regions["ACC"].tolist() == [1.35]
    assert state.regions["DLPFC"].tolist() == [0.675]
    assert state.metrics["trial_events"][0]["regional_input"] == {
        "ACC": 1.35,
        "DLPFC": 0.675,
    }
