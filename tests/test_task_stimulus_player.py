"""Testy regresyjne odtwarzacza bodźców zadań poznawczych."""

from brain_core.experiments.protocols import TrialStimulus
from brain_core.simulation.scheduler import TaskStimulusPlayer
from brain_core.simulation.state import SimulationState


def test_task_stimulus_player_sorts_stimuli_before_playback() -> None:
    """Weryfikuje, że nieposortowane wejście jest odtwarzane chronologicznie."""
    stimuli = [
        TrialStimulus(trial_id=2, onset_s=2.0, duration_s=0.5, payload={}, condition="late"),
        TrialStimulus(trial_id=1, onset_s=1.0, duration_s=0.5, payload={}, condition="early"),
    ]
    player = TaskStimulusPlayer(stimuli=stimuli)
    state = SimulationState(time=1.5)

    player.update(state, dt=0.1)

    assert [event["trial_id"] for event in state.metrics["trial_events"]] == [1]
    assert player.cursor == 1
