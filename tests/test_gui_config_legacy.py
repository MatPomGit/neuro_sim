"""Testy regresji konfiguracji legacy GUI tkinter."""

from __future__ import annotations

import pytest

from brain_model.gui_config import GuiConfigMixin
from brain_model.gui_state import GuiState


class LegacyConfigHarness(GuiConfigMixin):
    """Minimalny obiekt testowy dla metod konfiguracji legacy GUI."""

    def __init__(self) -> None:
        """Utwórz stan bez inicjalizacji widżetów tkinter."""
        self.state = GuiState()
        self.plot_vars = {"activity": object()}
        self.controls_synced = False
        self.scenario_refreshed = False
        self.auto_dt_toggled = False

    def _sync_controls_from_state(self) -> None:
        """Zanotuj atomowe zatwierdzenie stanu bez dotykania tkinter."""
        self.controls_synced = True

    def _refresh_scenario_details(self) -> None:
        """Zanotuj odświeżenie opisu scenariusza bez dotykania tkinter."""
        self.scenario_refreshed = True

    def _on_auto_dt_toggle(self) -> None:
        """Zanotuj odświeżenie trybu automatycznego kroku bez dotykania tkinter."""
        self.auto_dt_toggled = True


@pytest.mark.parametrize("invalid_dt", ["abc", "0", "-0.01"])
def test_legacy_config_rejects_invalid_dt_without_partial_state(
    invalid_dt: str,
) -> None:
    """Niepoprawne dt przerywa wczytywanie przed mutacją pozostałego stanu."""
    gui = LegacyConfigHarness()
    original_state = GuiState()

    with pytest.raises(ValueError) as error_info:
        gui._apply_config(
            {
                "T": "99.0",
                "dt": invalid_dt,
                "seed": "123",
                "brain_params": {"noise": "0.5"},
                "plots": {"activity": True},
            }
        )

    assert str(invalid_dt) in str(error_info.value)
    assert "Niepoprawna wartość dt" in str(error_info.value)
    assert gui.state == original_state
    assert gui.controls_synced is False
    assert gui.scenario_refreshed is False
    assert gui.auto_dt_toggled is False


def test_legacy_config_applies_positive_finite_dt_atomically() -> None:
    """Poprawne dt aktualizuje tekst stanu i liczbowy parametr modelu razem."""
    gui = LegacyConfigHarness()

    gui._apply_config(
        {
            "T": "24.0",
            "dt": "0.01",
            "seed": "123",
            "brain_params": {"noise": "0.5"},
            "plots": {"activity": True},
        }
    )

    assert gui.state.T == "24.0"
    assert gui.state.dt == "0.01"
    assert gui.state.seed == "123"
    assert gui.state.brain_params.dt == 0.01
    assert gui.state.brain_params.noise == 0.5
    assert gui.state.plots == {"activity": True}
    assert gui.controls_synced is True
    assert gui.scenario_refreshed is True
    assert gui.auto_dt_toggled is True
