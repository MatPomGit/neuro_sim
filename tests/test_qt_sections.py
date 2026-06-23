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
    assert (
        "self.scenario_combo.currentTextChanged.connect(self.on_scenario_changed)"
        in source
    )
    assert "self.scenario_config_combo.currentTextChanged.connect" in source
    assert "lambda _text: self.apply_scenario_yaml_config()" in source


def test_scenario_change_refreshes_details_and_automatic_duration() -> None:
    """Zmiana scenariusza automatycznie odświeża opis oraz sugerowany czas."""
    source = _method_source(QT_SECTIONS_PATH, "on_scenario_changed", "QtSections")

    assert "self.refresh_scenario_details()" in source
    assert "self.apply_suggested_duration(show_status=False)" in source


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
    assert "show_status and status_callback is not None" in source
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


def test_write_bound_control_blocks_signals_during_programmatic_sync() -> None:
    """Programowa synchronizacja kontrolek blokuje sygnały i przywraca ich stan."""
    from unittest.mock import MagicMock

    from brain_model.gui_state import GuiState
    from brain_model.qt_sections import ControlBinding, QtSections

    state = GuiState(seed="42")
    sections = QtSections(state, {})
    mock_control = MagicMock()
    mock_control.blockSignals.return_value = False
    sections.seed_edit = mock_control

    binding = ControlBinding("seed", "seed_edit", "line_edit")
    sections._write_bound_control(binding)

    mock_control.blockSignals.assert_any_call(True)
    mock_control.blockSignals.assert_any_call(False)
    mock_control.setText.assert_called_once_with("42")


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


def test_quick_start_has_lesson_and_yaml_selection() -> None:
    """Szybki start ma osobny wybór lekcji oraz konfiguracji YAML."""
    source = _method_source(QT_SECTIONS_PATH, "build_quick_start_section")

    assert "self.ready_lesson_combo = QComboBox()" in source
    assert "Lekcja" in source
    assert "self.scenario_config_combo = QComboBox()" in source
    assert "scenario_yaml_preset_labels()" in source
    assert "konfiguracja YAML" in source


def test_ready_lessons_point_to_yaml_labels() -> None:
    """Gotowe lekcje wskazują etykiety presetów YAML przez katalog lekcji."""
    source = QT_SECTIONS_PATH.read_text(encoding="utf-8")
    lesson_source = _method_source(QT_SECTIONS_PATH, "apply_ready_lesson")

    assert "load_lesson_catalog" in source
    assert "lesson_by_label" in source
    assert "READY_LESSON_PRESETS" not in source
    assert "label_for_scenario_yaml_path(lesson.scenario_config)" in lesson_source
    assert (
        "write_combo_box(self.scenario_config_combo, lesson_config_label)"
        in lesson_source
    )


def test_quick_start_lesson_preview_uses_yaml_catalog() -> None:
    """Podgląd lekcji pochodzi z katalogu YAML i zawiera ostrzeżenie kliniczne."""
    quick_start_source = _method_source(QT_SECTIONS_PATH, "build_quick_start_section")
    apply_source = _method_source(QT_SECTIONS_PATH, "apply_ready_lesson", "QtSections")
    format_source = _method_source(QT_SECTIONS_PATH, "format_lesson_preview")
    preview_source = _method_source(
        QT_SECTIONS_PATH, "refresh_lesson_preview", "QtSections"
    )
    module_source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    assert "self.lesson_preview_label" in quick_start_source
    assert (
        "Wynik jest interpretacją dydaktyczną modelu, nie diagnozą kliniczną"
        in module_source
    )
    assert "self.refresh_lesson_preview(lesson_id)" in apply_source
    assert "load_lesson_catalog()" in preview_source
    assert "lesson.learning_goal_pl" in format_source
    assert "lesson.level_pl" in format_source
    assert "lesson.estimated_duration_min" in format_source
    assert "lesson.pre_run_questions_pl" in format_source
    assert "lesson.scenario_config" in format_source
    assert "lesson.comparison_config" in format_source


def test_advanced_options_can_open_first_simulation_tutorial() -> None:
    """Opcje zaawansowane zawierają przycisk wywołujący samouczek."""
    source = _method_source(QT_SECTIONS_PATH, "build_advanced_options_section")

    assert "QPushButton('Uruchom samouczek pierwszej symulacji')" in source
    assert "tutorial_callback = self.callbacks.get('show_tutorial')" in source
    assert "tutorial_button.clicked.connect(tutorial_callback)" in source
    assert "form.addRow('samouczek', tutorial_button)" in source


def test_qt_window_starts_tutorial_once_and_exposes_menu_action() -> None:
    """Główne okno pokazuje samouczek przy pierwszym starcie i z menu Pomoc."""
    constructor_source = _method_source(QT_APP_PATH, "__init__", "BrainModelQtWindow")
    menu_source = _method_source(QT_APP_PATH, "_build_menu", "BrainModelQtWindow")
    first_run_source = _method_source(
        QT_APP_PATH, "show_tutorial_on_first_run", "BrainModelQtWindow"
    )
    tutorial_source = _method_source(QT_APP_PATH, "show_tutorial", "BrainModelQtWindow")
    finish_source = _method_source(QT_APP_PATH, "finish_tutorial", "BrainModelQtWindow")
    advance_source = _method_source(
        QT_APP_PATH, "_advance_tutorial_from", "BrainModelQtWindow"
    )
    module_source = QT_APP_PATH.read_text(encoding="utf-8")

    assert "'show_tutorial': self.show_tutorial" in constructor_source
    assert "QTimer.singleShot(0, self.show_tutorial_on_first_run)" in constructor_source
    assert "Samouczek pierwszej symulacji" in menu_source
    assert "tutorial_action.triggered.connect(self.show_tutorial)" in menu_source
    assert "TUTORIAL_COMPLETED_SETTING" in module_source
    assert "settings.value(TUTORIAL_COMPLETED_SETTING, False, bool)" in first_run_source
    assert "self.tutorial_active = True" in tutorial_source
    assert "self.tutorial_step_index = 0" in tutorial_source
    assert "self.show_tutorial_step" in tutorial_source
    assert "TUTORIAL_STEPS[self.tutorial_step_index] != expected_step" in advance_source
    assert "self.tutorial_step_index += 1" in advance_source
    assert "setValue(TUTORIAL_COMPLETED_SETTING, True)" in finish_source



def test_tutorial_progress_is_driven_by_user_operations() -> None:
    """Samouczek przechodzi dalej po monitorowanych operacjach użytkownika."""
    app_source = QT_APP_PATH.read_text(encoding="utf-8")
    sections_source = QT_SECTIONS_PATH.read_text(encoding="utf-8")
    quick_start_source = _method_source(QT_SECTIONS_PATH, "build_quick_start_section")
    yaml_source = _method_source(QT_SECTIONS_PATH, "apply_scenario_yaml_config")
    duration_source = _method_source(QT_SECTIONS_PATH, "apply_suggested_duration")
    result_source = _method_source(QT_APP_PATH, "on_simulation_result", "BrainModelQtWindow")
    start_source = _method_source(QT_APP_PATH, "start_simulation", "BrainModelQtWindow")

    assert "tutorial_yaml_selected" in app_source
    assert "tutorial_yaml_applied" in app_source
    assert "tutorial_duration_applied" in app_source
    assert "self.on_tutorial_simulation_started()" in start_source
    assert "self.on_tutorial_simulation_finished()" in result_source
    assert (
        "self.apply_yaml_button = QPushButton('Zastosuj konfigurację YAML')"
        in quick_start_source
    )
    assert (
        "self.suggested_duration_button = QPushButton('Użyj sugerowanego czasu')"
        in quick_start_source
    )
    assert "self._notify_tutorial_yaml_selected()" in quick_start_source
    assert "tutorial_callback = self.callbacks.get('tutorial_yaml_applied')" in yaml_source
    assert "tutorial_callback = self.callbacks.get('tutorial_duration_applied')" in duration_source
    assert "def _notify_tutorial_yaml_selected" in sections_source
