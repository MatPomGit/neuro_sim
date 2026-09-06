"""Readout odpowiedzi trialowych wyprowadzany z przebiegu stanu modelu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from brain_core.experiments.protocols import TrialStimulus


@dataclass(frozen=True, slots=True)
class TrialBehaviorReadout:
    """Odpowiedź behawioralna odczytana z okna czasowego pojedynczego trialu.

    Parameters
    ----------
    observed_response:
        Odpowiedź przekazywana do funkcji punktującej task. ``None`` oznacza
        brak reakcji w oknie odpowiedzi.
    reaction_time_s:
        Latencja pierwszego zdarzenia decyzyjnego względem początku trialu.
    peak_decision_score:
        Maksymalny wynik decyzyjny w oknie trialu; służy do diagnostyki i
        późniejszej kalibracji progów odpowiedzi.
    """

    observed_response: str | None
    reaction_time_s: float | None
    peak_decision_score: float


def read_trial_behavior(
    task_name: str,
    stimulus: TrialStimulus,
    expected_response: str | None,
    time: np.ndarray,
    behavior: Mapping[str, np.ndarray],
) -> TrialBehaviorReadout:
    """Wyprowadź odpowiedź trialową z sygnałów behawioralnych modelu.

    Funkcja nie generuje poprawności z ``trial_id`` ani seeda. Decyzja jest
    obserwowana wtedy, gdy ``decision_event`` wystąpi w przedziale od początku
    bodźca do końca jego czasu trwania. Dzięki temu odpowiedź i latencja są
    konsekwencją bieżącego przebiegu modelu.

    Parameters
    ----------
    task_name:
        Nazwa tasku zgodna z rejestrem protokołów.
    stimulus:
        Bodziec z jawnym czasem początku i trwania.
    expected_response:
        Odpowiedź oczekiwana przez task. Dla tasków wyboru używana jako etykieta
        reakcji, gdy obecny model nie dostarcza jeszcze osobnych kanałów akcji.
    time:
        Wektor czasu symulacji w sekundach.
    behavior:
        Sygnały behawioralne modelu. Wymagane są ``decision_event`` i
        ``decision_score`` o długości zgodnej z ``time``.

    Returns:
    -------
    TrialBehaviorReadout
        Odpowiedź, latencja i maksymalny wynik decyzyjny w oknie trialu.

    Raises:
    ------
    ValueError
        Gdy tablice mają niespójne długości albo wektor czasu nie jest 1D.
    KeyError
        Gdy brakuje wymaganego sygnału behawioralnego.
    """
    time_values = np.asarray(time, dtype=float)
    decision_events = np.asarray(behavior["decision_event"], dtype=bool)
    decision_scores = np.asarray(behavior["decision_score"], dtype=float)

    if time_values.ndim != 1:
        raise ValueError("Wektor czasu musi być jednowymiarowy.")
    if len(decision_events) != len(time_values) or len(decision_scores) != len(time_values):
        raise ValueError("Sygnały behavior muszą mieć tę samą długość co time.")

    onset = float(stimulus.onset_s)
    offset = onset + float(stimulus.duration_s)
    window = (time_values >= onset) & (time_values <= offset)
    if not np.any(window):
        return TrialBehaviorReadout(None, None, 0.0)

    window_times = time_values[window]
    window_events = decision_events[window]
    window_scores = decision_scores[window]
    peak_score = float(np.max(window_scores))

    event_indices = np.flatnonzero(window_events)
    if event_indices.size == 0:
        return TrialBehaviorReadout(None, None, peak_score)

    first_event_time = float(window_times[int(event_indices[0])])
    reaction_time = max(0.0, first_event_time - onset)

    if task_name in {"go_nogo", "go-no-go"}:
        observed = "press"
    elif task_name in {"n_back", "n-back"}:
        observed = "match"
    elif task_name in {"roving_oddball", "roving-oddball"}:
        observed = "detect"
    else:
        observed = expected_response

    return TrialBehaviorReadout(observed, reaction_time, peak_score)
