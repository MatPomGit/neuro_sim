"""Testy readoutu odpowiedzi trialowych ze stanu modelu."""

import numpy as np
import pytest

from brain_core.experiments.protocols import TrialStimulus
from brain_core.simulation.behavior_readout import read_trial_behavior


def _stimulus(condition: str = "go") -> TrialStimulus:
    """Zbuduj prosty bodziec testowy."""
    return TrialStimulus(
        trial_id=1,
        onset_s=0.2,
        duration_s=0.5,
        payload={},
        condition=condition,
    )


def test_readout_uses_first_decision_event_for_latency() -> None:
    """Latencja ma wynikać z pierwszego zdarzenia w oknie trialu."""
    time = np.array([0.0, 0.2, 0.3, 0.4, 0.7, 0.8])
    behavior = {
        "decision_event": np.array([False, False, True, True, False, False]),
        "decision_score": np.array([0.1, 0.2, 0.7, 0.9, 0.3, 0.1]),
    }

    result = read_trial_behavior("go_nogo", _stimulus(), "press", time, behavior)

    assert result.observed_response == "press"
    assert result.reaction_time_s == pytest.approx(0.1)
    assert result.peak_decision_score == pytest.approx(0.9)


def test_readout_returns_omission_without_decision_event() -> None:
    """Brak przekroczenia progu ma dawać brak odpowiedzi, nie sztuczny błąd RNG."""
    time = np.array([0.0, 0.2, 0.3, 0.4, 0.7])
    behavior = {
        "decision_event": np.zeros(5, dtype=bool),
        "decision_score": np.array([0.1, 0.2, 0.25, 0.3, 0.2]),
    }

    result = read_trial_behavior(
        "n_back", _stimulus("target"), "match", time, behavior
    )

    assert result.observed_response is None
    assert result.reaction_time_s is None
    assert result.peak_decision_score == pytest.approx(0.3)


def test_readout_for_stroop_preserves_expected_action_label() -> None:
    """Przy decyzji Stroop zachowuje etykietę oczekiwanej odpowiedzi tasku."""
    time = np.array([0.2, 0.3, 0.4])
    behavior = {
        "decision_event": np.array([False, True, False]),
        "decision_score": np.array([0.2, 0.8, 0.4]),
    }

    result = read_trial_behavior(
        "stroop", _stimulus("congruent"), "green", time, behavior
    )

    assert result.observed_response == "green"
    assert result.reaction_time_s == pytest.approx(0.1)
