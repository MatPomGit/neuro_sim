"""Statyczne testy spójności układu desktopowego GUI PySide6."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_GUI_PATH = REPO_ROOT / "main_gui.py"
GUI_ENTRYPOINT_PATH = REPO_ROOT / "brain_model" / "gui.py"
GUI_FORMS_PATH = REPO_ROOT / "brain_model" / "gui_forms.py"
QT_APP_PATH = REPO_ROOT / "brain_model" / "qt_app.py"
QT_SECTIONS_PATH = REPO_ROOT / "brain_model" / "qt_sections.py"
QT_GUI_PATHS = tuple(sorted((REPO_ROOT / "brain_model").glob("qt_*.py")))
DESKTOP_GUI_PATHS = (MAIN_GUI_PATH, GUI_ENTRYPOINT_PATH, *QT_GUI_PATHS)


def _imported_module_names(tree: ast.Module) -> set[str]:
    """Zwróć nazwy modułów importowanych bezpośrednio przez plik Python."""
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module.split(".", 1)[0])
    return imported_modules


def test_desktop_gui_modules_do_not_import_tkinter() -> None:
    """Sprawdź statycznie, że aktywne moduły desktopowego GUI nie importują Tkinter."""
    offenders = []
    for path in DESKTOP_GUI_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if "tkinter" in _imported_module_names(tree):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == []


def test_gui_entrypoint_delegates_to_pyside6_window() -> None:
    """Sprawdź, że publiczny punkt wejścia GUI wskazuje implementację PySide6."""
    source = GUI_ENTRYPOINT_PATH.read_text(encoding="utf-8")
    main_source = MAIN_GUI_PATH.read_text(encoding="utf-8")

    assert "from .qt_app import BrainModelGUI, BrainModelQtWindow, run_gui" in source
    assert "from brain_model.gui import run_gui" in main_source
    assert "tkinter" not in source


def test_qt_layout_uses_tabs_and_polish_section_titles() -> None:
    """Sprawdź statycznie główne kontenery i polskie tytuły sekcji Qt."""
    app_source = QT_APP_PATH.read_text(encoding="utf-8")
    sections_source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    assert "QTabWidget" in app_source
    assert 'self.tabs.addTab(config_tab, "Konfiguracja")' in app_source
    assert 'self.tabs.addTab(plots_tab, "Wykresy")' in app_source
    assert 'QGroupBox("Szybki start")' in sections_source
    assert 'QGroupBox("Opcje zaawansowane")' in sections_source
    assert 'QGroupBox("Wyniki i wykresy")' in sections_source


def test_qt_quick_start_controls_are_bound_to_gui_state() -> None:
    """Sprawdź jawne mapowanie kontrolek szybkiego startu do pól stanu GUI."""
    source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    assert 'ControlBinding("scenario", "scenario_combo", "combo_box")' in source
    assert 'ControlBinding("T", "T_edit", "line_edit")' in source
    assert 'ControlBinding("save_results", "save_results_check", "check_box")' in source
    assert 'layout.addRow("scenariusz", self.scenario_combo)' in source
    assert 'layout.addRow("czas symulacji [s]", self.T_edit)' in source
    assert 'QCheckBox("Zapisz wyniki po symulacji")' in source


def test_qt_advanced_controls_are_bound_to_gui_state() -> None:
    """Sprawdź jawne mapowanie opcji zaawansowanych do pól stanu GUI."""
    source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    expected_bindings = {
        'ControlBinding("seed", "seed_edit", "line_edit")',
        'ControlBinding("dt", "dt_edit", "line_edit")',
        'ControlBinding("auto_dt", "auto_dt_check", "check_box")',
        'ControlBinding("command", "command_combo", "combo_box")',
        'ControlBinding("batch_seeds", "batch_seeds_edit", "line_edit")',
        'ControlBinding("batch_scenarios", "batch_scenarios_edit", "line_edit")',
        'ControlBinding("sensitivity_params", "sensitivity_edit", "line_edit")',
        'ControlBinding("sensitivity_delta", "sensitivity_delta_edit", "line_edit")',
    }

    for binding in expected_bindings:
        assert binding in source
    assert 'form.addRow("ziarna serii", self.batch_seeds_edit)' in source
    assert 'form.addRow("scenariusze serii", self.batch_scenarios_edit)' in source
    assert 'form.addRow("parametry wrażliwości", self.sensitivity_edit)' in source
    assert 'form.addRow("delta wrażliwości", self.sensitivity_delta_edit)' in source


def test_qt_menu_opens_parameter_dialogs() -> None:
    """Sprawdź, że górne menu ustawień otwiera okna parametrów modelu."""
    source = QT_APP_PATH.read_text(encoding="utf-8")

    assert 'menu_bar.addMenu("Ustawienia")' in source
    assert 'settings_menu.addAction("Parametry globalne modelu...")' in source
    assert 'settings_menu.addAction("Parametry oscylatorów...")' in source
    assert (
        "brain_params_action.triggered.connect(self.open_brain_params_dialog)" in source
    )
    assert (
        "oscillator_params_action.triggered.connect(self.open_oscillator_params_dialog)"
        in source
    )
    assert "class QtDataclassParameterDialog" in source


def test_parameter_forms_use_polish_labels() -> None:
    """Sprawdź, że okna parametrów korzystają ze słownika polskich etykiet."""
    forms_source = GUI_FORMS_PATH.read_text(encoding="utf-8")
    qt_source = QT_APP_PATH.read_text(encoding="utf-8")

    assert "PARAMETER_LABELS" in forms_source
    assert '"gw_threshold": "próg globalnej przestrzeni roboczej"' in forms_source
    assert '"cognitive_drive_gain": "wzmocnienie napędu poznawczego"' in forms_source
    assert "PARAMETER_LABELS.get(field.name, field.name)" in qt_source


def test_qt_plot_checkboxes_are_hidden_behind_customization_panel() -> None:
    """Sprawdź, że Qt pokazuje presety i zwija szczegółowe wybory wykresów."""
    source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    assert "QToolButton" in source
    assert 'setText("Dostosuj wykresy")' in source
    assert "setCheckable(True)" in source
    assert "toggle_plot_details" in source
    assert "self.plot_details_group.setVisible(checked)" in source
    assert 'QRadioButton("Niestandardowe"' in source
    assert "custom_button.setVisible(False)" in source
    assert "Aktywny zestaw: Niestandardowe" in source


def test_qt_start_button_is_defined_once() -> None:
    """Sprawdź, że aktywne GUI Qt pokazuje jeden główny przycisk uruchamiania."""
    qt_button_count = QT_APP_PATH.read_text(encoding="utf-8").count(
        'QPushButton("Uruchom symulację")'
    ) + QT_SECTIONS_PATH.read_text(encoding="utf-8").count(
        'QPushButton("Uruchom symulację")'
    )

    assert qt_button_count == 1
