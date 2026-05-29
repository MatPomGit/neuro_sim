"""Statyczne testy sekcji formularza PySide6."""

from __future__ import annotations

import ast
from pathlib import Path

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
    assert "self.T_edit.setText(str(scenario.duration_hint))" in source
    assert "if self.auto_dt_check.isChecked():" in source
    assert "self.on_auto_dt_toggled(True)" in source
    assert "self.state.T = self.T_edit.text()" in source
    assert "self.state.dt = self.dt_edit.text()" in source
    assert "Ustawiono sugerowany czas scenariusza." in source


def test_qt_window_provides_status_callback_to_sections() -> None:
    """Główne okno przekazuje sekcjom callback do neutralnego statusu użytkownika."""
    constructor_source = _method_source(QT_APP_PATH, "__init__", "BrainModelQtWindow")
    status_source = _method_source(QT_APP_PATH, "show_status", "BrainModelQtWindow")

    assert "'show_status': self.show_status" in constructor_source
    assert "self.status_label.setObjectName('statusLabel')" in status_source
    assert "self.status_label.setText(message)" in status_source
