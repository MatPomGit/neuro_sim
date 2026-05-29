"""Statyczne testy sekcji formularza PySide6."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from brain_model.gui_state import GuiState

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_SECTIONS_PATH = REPO_ROOT / "brain_model" / "qt_sections.py"
QT_APP_PATH = REPO_ROOT / "brain_model" / "qt_app.py"


def _method_source(path: Path, method_name: str, class_name: str | None = None) -> str:
    """Zwróć znormalizowany kod źródłowy metody o podanej nazwie."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    search_root: ast.AST = tree
    if class_name is not None:
        search_root = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )
    method = next(
        node
        for node in ast.walk(search_root)
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )
    return ast.unparse(method)


def test_quick_start_has_suggested_duration_button() -> None:
    """Sekcja szybkiego startu zawiera przycisk użycia sugerowanego czasu."""
    source = _method_source(QT_SECTIONS_PATH, "build_quick_start_section")

    assert "QPushButton('Użyj sugerowanego czasu')" in source
    assert (
        "suggested_duration_button.clicked.connect(self.apply_suggested_duration)"
        in source
    )


def test_apply_suggested_duration_updates_controls_state_dt_and_status() -> None:
    """Obsługa przycisku pobiera scenariusz, odświeża T, dt, stan i status."""
    source = _method_source(QT_SECTIONS_PATH, "apply_suggested_duration")

    assert "current_scenario_id = self.scenario_combo.currentText()" in source
    assert "scenario = get_scenario(current_scenario_id)" in source
    assert "write_line_edit(self.T_edit, scenario.duration_hint)" in source
    assert "if read_check_box(self.auto_dt_check):" in source
    assert "self.on_auto_dt_toggled(True)" in source
    assert "self.state.T = read_line_edit(self.T_edit)" in source
    assert "self.state.dt = read_line_edit(self.dt_edit)" in source
    assert "Ustawiono sugerowany czas scenariusza." in source


def test_qt_window_provides_status_callback_to_sections() -> None:
    """Główne okno przekazuje sekcjom callback do neutralnego statusu użytkownika."""
    constructor_source = _method_source(QT_APP_PATH, "__init__", "BrainModelQtWindow")
    status_source = _method_source(QT_APP_PATH, "show_status", "BrainModelQtWindow")

    assert "'show_status': self.show_status" in constructor_source
    assert "self.status_label.setObjectName('statusLabel')" in status_source
    assert "self.status_label.setText(message)" in status_source


def _assigned_dict_node(tree: ast.Module, name: str) -> ast.Dict:
    """Zwróć węzeł słownika przypisany do stałej modułowej."""
    assignment = next(
        node
        for node in tree.body
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
        )
        or (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        )
    )
    if not isinstance(assignment.value, ast.Dict):
        raise AssertionError(f"{name} nie jest słownikiem modułowym")
    return assignment.value


def _control_binding_fields() -> set[str]:
    """Odczytaj statycznie pola `GuiState` obecne w `CONTROL_BINDINGS`."""
    tree = ast.parse(QT_SECTIONS_PATH.read_text(encoding="utf-8"))
    bindings = _assigned_dict_node(tree, "CONTROL_BINDINGS")
    state_fields: set[str] = set()
    for value in bindings.values:
        if not isinstance(value, ast.Tuple):
            continue
        for element in value.elts:
            if (
                isinstance(element, ast.Call)
                and isinstance(element.func, ast.Name)
                and element.func.id == "ControlBinding"
                and element.args
                and isinstance(element.args[0], ast.Constant)
                and isinstance(element.args[0].value, str)
            ):
                state_fields.add(element.args[0].value)
    return state_fields


def _omitted_gui_state_fields() -> set[str]:
    """Odczytaj statycznie świadomie pominięte pola stanu GUI."""
    tree = ast.parse(QT_SECTIONS_PATH.read_text(encoding="utf-8"))
    omissions = _assigned_dict_node(tree, "GUI_STATE_CONTROL_OMISSIONS")
    return {
        key.value
        for key in omissions.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def test_gui_state_fields_are_bound_or_consciously_omitted() -> None:
    """Każde pole `GuiState` ma mapowanie kontrolki albo jawne uzasadnienie pominięcia."""
    gui_state_fields = {field.name for field in fields(GuiState)}

    assert gui_state_fields == _control_binding_fields() | _omitted_gui_state_fields()


def test_control_bindings_keep_sync_sections_separate() -> None:
    """Mapowanie rozdziela szybki start i opcje zaawansowane zgodnie z KISS."""
    tree = ast.parse(QT_SECTIONS_PATH.read_text(encoding="utf-8"))
    bindings = _assigned_dict_node(tree, "CONTROL_BINDINGS")
    binding_groups = {
        key.value
        for key in bindings.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }

    assert binding_groups == {"quick_start", "advanced_options"}
    assert "sync_plot_selection_state_from_controls" in QT_SECTIONS_PATH.read_text(
        encoding="utf-8"
    )
    assert "sync_plot_selection_controls_from_state" in QT_SECTIONS_PATH.read_text(
        encoding="utf-8"
    )
