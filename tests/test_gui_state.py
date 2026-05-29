"""Testy stanu GUI niezależnego od niewidocznych formularzy."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from brain_model.gui_forms import RULE_FIELDS, ParameterForm
from brain_model.gui_state import GuiState
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams
from brain_model.plasticity import (
    ConnectivityAdaptationConfig,
    PlasticityRuleConfig,
)

ROOT = Path(__file__).resolve().parents[1]
GUI_APP_PATH = ROOT / "brain_model" / "gui_app.py"
GUI_CONFIG_PATH = ROOT / "brain_model" / "gui_config.py"
GUI_LAYOUT_PATH = ROOT / "brain_model" / "gui_layout.py"
GUI_SECTIONS_PATH = ROOT / "brain_model" / "gui_sections.py"


def test_gui_state_keeps_editable_domains_outside_widgets() -> None:
    """Sprawdź, że stan GUI obejmuje parametry, wykresy i ustawienia serii."""
    state = GuiState()

    assert isinstance(state.brain_params, BrainParams)
    assert isinstance(state.oscillator_params, WilsonCowanParams)
    assert state.batch_seeds == "7,11,19"
    assert state.batch_scenarios == "reward-learning"
    assert state.sensitivity_params == "noise,gw_threshold"
    assert state.sensitivity_delta == "0.1"
    assert state.plots == {}


def test_main_window_does_not_create_hidden_parameter_forms() -> None:
    """Sprawdź statycznie, że główne okno nie używa niewidocznych ParameterForm."""
    source = GUI_APP_PATH.read_text(encoding="utf-8")

    assert "ParameterForm" not in source
    assert "GuiState" in source
    assert "self.state = GuiState" in source


def test_config_and_defaults_use_state_instead_of_hidden_forms() -> None:
    """Sprawdź statycznie, że konfiguracja i reset bazują na stanie GUI."""
    config_source = GUI_CONFIG_PATH.read_text(encoding="utf-8")
    layout_source = GUI_LAYOUT_PATH.read_text(encoding="utf-8")

    assert "self.brain_form" not in config_source
    assert "self.osc_form" not in config_source
    assert "self.brain_form.reset" not in layout_source
    assert "self.osc_form.reset" not in layout_source
    assert "self.state.brain_params" in layout_source
    assert "self.state.oscillator_params" in layout_source


def test_advanced_settings_save_reports_invalid_values() -> None:
    """Sprawdź, że zapis parametrów zaawansowanych pokazuje błąd walidacji."""
    source = GUI_SECTIONS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    save_and_close = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "save_and_close"
    )
    value_error_handlers = [
        handler
        for node in ast.walk(save_and_close)
        if isinstance(node, ast.Try)
        for handler in node.handlers
        if isinstance(handler.type, ast.Name) and handler.type.id == "ValueError"
    ]

    assert value_error_handlers
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "showerror"
        and ast.unparse(node.func.value) == "messagebox"
        and "Nie udało się zapisać parametrów zaawansowanych" in ast.unparse(node)
        for handler in value_error_handlers
        for node in ast.walk(handler)
    )
    assert any(
        isinstance(stmt, ast.Return)
        for handler in value_error_handlers
        for stmt in handler.body
    )


def test_advanced_settings_preserve_current_plasticity_rules() -> None:
    """Sprawdź, że zapis zaawansowanych pól nie przywraca domyślnych reguł plastyczności."""
    config_source = GUI_CONFIG_PATH.read_text(encoding="utf-8")
    sections_source = GUI_SECTIONS_PATH.read_text(encoding="utf-8")
    layout_source = GUI_LAYOUT_PATH.read_text(encoding="utf-8")

    assert "gui.state.brain_params" in sections_source
    assert (
        "gui.brain_defaults"
        not in sections_source.split("brain = ParameterForm", 1)[1].split(
            "include_fields", 1
        )[0]
    )
    assert "semantic_rule=self.brain_defaults.semantic_rule" not in config_source
    assert "value_rule=self.brain_defaults.value_rule" not in config_source
    assert (
        "connectivity_adaptation=self.brain_defaults.connectivity_adaptation"
        not in config_source
    )
    assert "semantic_rule=self.brain_defaults.semantic_rule" not in layout_source
    assert "value_rule=self.brain_defaults.value_rule" not in layout_source
    assert (
        "connectivity_adaptation=self.brain_defaults.connectivity_adaptation"
        not in layout_source
    )


def test_parameter_form_values_copy_excluded_fields_from_current_defaults() -> None:
    """Sprawdź, że ukryte pola formularza Tk są kopiowane z bieżącego stanu modelu."""

    class FakeVar:
        """Minimalna zmienna testowa zgodna z metodą get formularza."""

        def __init__(self, value: object) -> None:
            """Zapamiętaj wartość zwracaną przez get."""
            self.value = value

        def get(self) -> object:
            """Zwróć wartość formularza używaną w teście bez uruchamiania Tk."""
            return self.value

    current_params = BrainParams(
        semantic_rule=PlasticityRuleConfig(False, 0.111, 0.222),
        value_rule=PlasticityRuleConfig(False, 0.333, 0.444),
        connectivity_adaptation=ConnectivityAdaptationConfig(False, 0.555, 0.666),
    )
    form = ParameterForm.__new__(ParameterForm)
    form.dataclass_type = BrainParams
    form.defaults = current_params
    form.include_fields = {"noise"}
    form.vars = {"noise": FakeVar("0.123")}

    params = form.values()

    assert params.noise == 0.123
    assert params.semantic_rule == current_params.semantic_rule
    assert params.value_rule == current_params.value_rule
    assert params.connectivity_adaptation == current_params.connectivity_adaptation


def test_qt_brain_dialog_preserves_current_plasticity_rules() -> None:
    """Sprawdź statycznie, że okno Qt nie nadpisuje ukrytych reguł domyślnymi wartościami."""
    source = (ROOT / "brain_model" / "qt_app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "open_brain_params_dialog"
    )
    method_source = ast.unparse(method)

    assert "replace(edited_params, dt=current_dt)" in method_source
    assert "semantic_rule=self.brain_defaults.semantic_rule" not in method_source
    assert "value_rule=self.brain_defaults.value_rule" not in method_source
    assert (
        "connectivity_adaptation=self.brain_defaults.connectivity_adaptation"
        not in method_source
    )


def test_qt_parameter_dialog_validates_before_accepting() -> None:
    """Sprawdź, że dialog Qt zatrzymuje okno przy błędzie walidacji formularza."""
    source = (ROOT / "brain_model" / "qt_app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    accept_method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "accept"
    )
    accept_source = ast.unparse(accept_method)

    assert "self.values()" in accept_source
    assert "QMessageBox.critical" in accept_source
    assert "return" in accept_source
    assert "super().accept()" in accept_source


def test_rule_fields_stay_out_of_saved_brain_config() -> None:
    """Sprawdź założenie listy pól zapisywanych dla BrainParams w konfiguracji GUI."""
    editable_fields = {
        field.name for field in fields(BrainParams) if field.name not in RULE_FIELDS
    }

    assert "dt" in editable_fields
    assert not set(RULE_FIELDS) & editable_fields
