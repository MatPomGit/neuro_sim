"""Testy zapisu i odczytu konfiguracji GUI Qt."""

from __future__ import annotations

from brain_model.gui_state import GuiState
from brain_model.qt_config import apply_config_to_state, state_to_config


def test_qt_config_preserves_individual_plot_choices() -> None:
    """Sprawdź, że konfiguracja JSON zachowuje pojedyncze wybory wykresów."""
    state = GuiState()
    state.plots = {
        "activity": True,
        "behavior": False,
        "diagnostics": True,
        "scenario_timeline": False,
    }

    config = state_to_config(state)
    loaded_state = apply_config_to_state(GuiState(), config)

    assert config["plots"] == state.plots
    assert loaded_state.plots == state.plots
