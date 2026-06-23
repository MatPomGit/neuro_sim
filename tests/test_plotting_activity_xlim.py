"""Testy synchronizacji osi czasu wykresu aktywności i bodźców."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from brain_model.plotting import draw_activity_with_stimulus_channels
from brain_model.scenarios import get_scenario


def test_activity_xlim_synchronization_does_not_recurse() -> None:
    """Sprawdź, że zmiana zakresu osi X nie wywołuje rekurencji Matplotlib."""
    time = np.linspace(0.0, 1.0, 20)
    idx = {"VIS": 0, "ATT": 1}
    activity = np.column_stack((time, 1.0 - time))
    scenario = get_scenario("reward-learning")
    fig, ax = plt.subplots()

    activity_ax, stimulus_ax = draw_activity_with_stimulus_channels(
        ax=ax,
        time=time,
        activity=activity,
        names=list(idx),
        idx=idx,
        scenario=scenario,
    )

    activity_ax.set_xlim(0.2, 0.8)

    assert activity_ax.get_xlim() == stimulus_ax.get_xlim()
    plt.close(fig)
