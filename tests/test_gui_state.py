"""Testy stanu GUI i jawnego mapowania kontrolek PySide6."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from brain_model.gui_forms import RULE_FIELDS
from brain_model.gui_state import GuiState
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams
from brain_model.plasticity import (
    ConnectivityAdaptationConfig,
    PlasticityRuleConfig,
)

ROOT = Path(__file__).resolve().parents[1]
QT_APP_PATH = ROOT / "brain_model" / "qt_app.py"
QT_CONFIG_PATH = ROOT / "brain_model" / "qt_config.py"
QT_SECTIONS_PATH = ROOT / "brain_model" / "qt_sections.py"


def _qt_sections_tree() -> ast.Module:
    """Wczytaj AST modułu sekcji Qt bez importowania PySide6."""
    return ast.parse(QT_SECTIONS_PATH.read_text(encoding="utf-8"))


def _find_assignment_value(tree: ast.Module, name: str) -> ast.expr:
    """Znajdź wartość przypisaną do zmiennej o podanej nazwie (obsługuje Assign i AnnAssign)."""
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            if node.value is not None:
                return node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
    raise AssertionError(f"Nie znaleziono przypisania dla {name}")


def _qt_control_bindings() -> dict[str, list[tuple[str, str, str]]]:
    """Odczytaj stałe mapowanie kontrolek Qt bez tworzenia widżetów."""
    tree = _qt_sections_tree()
    value_node = _find_assignment_value(tree, "CONTROL_BINDINGS")
    if not isinstance(value_node, ast.Dict):
        raise AssertionError("CONTROL_BINDINGS nie jest literałem słownika.")

    bindings: dict[str, list[tuple[str, str, str]]] = {}
    for key_node, value_node in zip(assignment.value.keys, assignment.value.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            raise AssertionError("Nazwa grupy mapowania nie jest stałym tekstem.")
        if not isinstance(value_node, ast.Tuple):
            raise AssertionError("Grupa mapowania nie jest stałą krotką.")
        group_bindings: list[tuple[str, str, str]] = []
        for element in value_node.elts:
            if not isinstance(element, ast.Call) or len(element.args) != 3:
                raise AssertionError(
                    "Mapowanie kontrolki nie jest wywołaniem ControlBinding."
                )
            values = []
            for argument in element.args:
                if not isinstance(argument, ast.Constant) or not isinstance(
                    argument.value, str
                ):
                    raise AssertionError(
                        "Argument ControlBinding nie jest stałym tekstem."
                    )
                values.append(argument.value)
            group_bindings.append((values[0], values[1], values[2]))
        bindings[key_node.value] = group_bindings
    return bindings


def _qt_state_control_omissions() -> set[str]:
    """Odczytaj pola stanu celowo pomijane przez mapowanie kontrolek Qt."""
    tree = _qt_sections_tree()
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "GUI_STATE_CONTROL_OMISSIONS"
    )
    if not isinstance(assignment.value, ast.Dict):
        raise AssertionError("GUI_STATE_CONTROL_OMISSIONS nie jest literałem słownika.")
    omissions = set()
    for key_node in assignment.value.keys:
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            raise AssertionError("Pominięte pole stanu nie jest stałym tekstem.")
        omissions.add(key_node.value)
    return omissions


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


def test_qt_control_bindings_cover_editable_gui_state_fields() -> None:
    """Sprawdź, że edytowalne pola `GuiState` mają jawne powiązanie z kontrolką Qt."""
    bound_state_fields = {
        binding[0]
        for binding_group in _qt_control_bindings().values()
        for binding in binding_group
    }
    gui_state_fields = {field.name for field in fields(GuiState)}
    omitted_state_fields = _qt_state_control_omissions()

    assert bound_state_fields | omitted_state_fields == gui_state_fields
    assert bound_state_fields.isdisjoint(omitted_state_fields)


def test_qt_control_bindings_use_supported_control_kinds() -> None:
    """Sprawdź, że mapowanie kontrolek używa tylko obsługiwanych typów odczytu."""
    supported_kinds = {"line_edit", "check_box", "combo_box"}

    assert {
        binding[2]
        for binding_group in _qt_control_bindings().values()
        for binding in binding_group
    } <= supported_kinds


def test_qt_config_and_defaults_use_state_instead_of_hidden_forms() -> None:
    """Sprawdź statycznie, że konfiguracja i reset bazują na stanie GUI."""
    config_source = QT_CONFIG_PATH.read_text(encoding="utf-8")
    app_source = QT_APP_PATH.read_text(encoding="utf-8")

    assert "self.brain_form" not in config_source
    assert "self.osc_form" not in config_source
    assert "self.brain_form" not in app_source
    assert "self.osc_form" not in app_source
    assert "self.state.brain_params" in app_source
    assert "self.state.oscillator_params" in app_source


def test_qt_parameter_dialog_validates_before_accepting() -> None:
    """Sprawdź, że dialog Qt zatrzymuje okno przy błędzie walidacji formularza."""
    source = QT_APP_PATH.read_text(encoding="utf-8")
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


def test_qt_brain_dialog_preserves_current_plasticity_rules() -> None:
    """Sprawdź statycznie, że okno Qt nie nadpisuje ukrytych reguł domyślnymi wartościami."""
    source = QT_APP_PATH.read_text(encoding="utf-8")
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


def test_rule_fields_stay_out_of_saved_brain_config() -> None:
    """Sprawdź założenie listy pól zapisywanych dla BrainParams w konfiguracji GUI."""
    editable_fields = {
        field.name for field in fields(BrainParams) if field.name not in RULE_FIELDS
    }

    assert "dt" in editable_fields
    assert not set(RULE_FIELDS) & editable_fields


def test_qt_config_preserves_current_plasticity_rules() -> None:
    """Sprawdź, że zapis konfiguracji Qt nie przywraca domyślnych reguł plastyczności."""
    config_source = QT_CONFIG_PATH.read_text(encoding="utf-8")
    sections_source = QT_SECTIONS_PATH.read_text(encoding="utf-8")
    current_params = BrainParams(
        semantic_rule=PlasticityRuleConfig(False, 0.111, 0.222),
        value_rule=PlasticityRuleConfig(False, 0.333, 0.444),
        connectivity_adaptation=ConnectivityAdaptationConfig(False, 0.555, 0.666),
    )

    assert current_params.semantic_rule.enabled is False
    assert "RULE_FIELDS" in config_source
    assert "exclude=set(RULE_FIELDS)" in config_source
    assert "GUI_STATE_CONTROL_OMISSIONS" in sections_source
    assert "semantic_rule=self.brain_defaults.semantic_rule" not in config_source
    assert "value_rule=self.brain_defaults.value_rule" not in config_source
    assert (
        "connectivity_adaptation=self.brain_defaults.connectivity_adaptation"
        not in config_source
    )
