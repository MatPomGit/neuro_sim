"""Statyczne testy spójności układu GUI."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUI_LAYOUT_PATH = REPO_ROOT / "brain_model" / "gui_layout.py"
GUI_SECTIONS_PATH = REPO_ROOT / "brain_model" / "gui_sections.py"
GUI_STYLES_PATH = REPO_ROOT / "brain_model" / "gui_styles.py"
GUI_FORMS_PATH = REPO_ROOT / "brain_model" / "gui_forms.py"
GUI_MENU_PATH = REPO_ROOT / "brain_model" / "gui_menu.py"
GUI_RESULTS_PATH = REPO_ROOT / "brain_model" / "gui_results.py"
QT_APP_PATH = REPO_ROOT / "brain_model" / "qt_app.py"
QT_SECTIONS_PATH = REPO_ROOT / "brain_model" / "qt_sections.py"


def _constant_int_keyword(
    call: ast.Call, name: str, default: int | None = None
) -> int | None:
    """Zwróć całkowitą wartość stałego argumentu nazwanego wywołania."""
    for keyword in call.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            if isinstance(value, int):
                return value
    return default


def _method_body(tree: ast.Module, method_name: str) -> list[ast.stmt]:
    """Znajdź ciało metody mixina GUI o podanej nazwie."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node.body
    raise AssertionError(f"Nie znaleziono metody {method_name!r}.")


def test_sim_frame_grid_cells_are_unique() -> None:
    """Sprawdź statycznie, że w self.sim_frame nie powtarzają się komórki siatki."""
    tree = ast.parse(GUI_SECTIONS_PATH.read_text(encoding="utf-8"))
    body = _method_body(tree, "_build_quick_start_section")
    sim_frame_widgets: set[str] = set()
    occupied_cells: dict[tuple[int, int], str] = {}

    for stmt in body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.value, ast.Call)
            and stmt.value.args
            and isinstance(stmt.value.args[0], ast.Attribute)
            and stmt.value.args[0].attr == "sim_frame"
        ):
            sim_frame_widgets.add(ast.unparse(stmt.targets[0]))

        for call in [node for node in ast.walk(stmt) if isinstance(node, ast.Call)]:
            if not isinstance(call.func, ast.Attribute) or call.func.attr != "grid":
                continue

            owner = call.func.value
            is_sim_frame_grid = (
                isinstance(owner, ast.Name)
                and owner.id in sim_frame_widgets
                or isinstance(owner, ast.Call)
                and owner.args
                and isinstance(owner.args[0], ast.Attribute)
                and owner.args[0].attr == "sim_frame"
            )
            if not is_sim_frame_grid:
                continue

            row = _constant_int_keyword(call, "row")
            column = _constant_int_keyword(call, "column")
            columnspan = _constant_int_keyword(call, "columnspan", 1)
            assert row is not None and column is not None and columnspan is not None

            widget_name = ast.unparse(owner)
            for occupied_column in range(column, column + columnspan):
                cell = (row, occupied_column)
                assert cell not in occupied_cells, (
                    f"Komórka self.sim_frame row={row}, column={occupied_column} jest użyta "
                    f"przez {occupied_cells[cell]} oraz {widget_name}."
                )
                occupied_cells[cell] = widget_name


def test_labeled_entry_helper_keeps_label_and_field_on_same_row() -> None:
    """Sprawdź, że pomocnik pól podpisanych używa tego samego row dla etykiety i pola."""
    tree = ast.parse(GUI_SECTIONS_PATH.read_text(encoding="utf-8"))
    body = _method_body(tree, "_add_labeled_entry")
    grid_calls = [
        node for stmt in body for node in ast.walk(stmt) if isinstance(node, ast.Call)
    ]
    row_arguments = [
        keyword.value.id
        for call in grid_calls
        if isinstance(call.func, ast.Attribute) and call.func.attr == "grid"
        for keyword in call.keywords
        if keyword.arg == "row" and isinstance(keyword.value, ast.Name)
    ]

    assert row_arguments == ["row", "row"]


def test_batch_and_sensitivity_options_use_consecutive_advanced_rows() -> None:
    """Sprawdź, że pola serii i wrażliwości zachowują kolejne wiersze w panelu zaawansowanym."""
    tree = ast.parse(GUI_SECTIONS_PATH.read_text(encoding="utf-8"))
    body = _method_body(tree, "_build_advanced_options_section")
    labels_to_rows: dict[str, int] = {}

    for call in [
        node for stmt in body for node in ast.walk(stmt) if isinstance(node, ast.Call)
    ]:
        if (
            not isinstance(call.func, ast.Attribute)
            or call.func.attr != "_add_labeled_entry"
        ):
            continue
        if len(call.args) < 3:
            continue
        parent, row_node, label_node = call.args[:3]
        if (
            isinstance(parent, ast.Attribute)
            and parent.attr == "advanced_options_frame"
            and isinstance(row_node, ast.Constant)
            and isinstance(row_node.value, int)
            and isinstance(label_node, ast.Constant)
            and isinstance(label_node.value, str)
        ):
            labels_to_rows[label_node.value] = row_node.value

    assert labels_to_rows["ziarna serii"] == 4
    assert labels_to_rows["scenariusze serii"] == 5
    assert labels_to_rows["parametry wrażliwości"] == 6
    assert labels_to_rows["delta wrażliwości"] == 7


def test_configure_styles_defines_guiding_gui_styles() -> None:
    """Sprawdź, że GUI definiuje i stosuje kluczowe style prowadzące uwagę."""
    tree = ast.parse(GUI_STYLES_PATH.read_text(encoding="utf-8"))
    source = GUI_STYLES_PATH.read_text(encoding="utf-8")
    configure_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "configure_styles"
    )

    assert configure_node.returns is not None
    assert "Primary.TButton" in source
    assert "QuickStart.TLabelframe" in source
    assert "ScenarioInfo.TLabel" in source
    assert "Status.Horizontal.TProgressbar" in source
    assert "Advanced.TButton" in source
    assert "Warning.Status.TLabel" in source


def test_bottom_bar_has_close_button_on_the_right() -> None:
    """Sprawdź, że dolny pasek akcji zawiera prawostronny przycisk zamykania okna."""
    tree = ast.parse(GUI_LAYOUT_PATH.read_text(encoding="utf-8"))
    body = _method_body(tree, "_build_layout")

    for call in [
        node for stmt in body for node in ast.walk(stmt) if isinstance(node, ast.Call)
    ]:
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "pack":
            continue
        button_call = call.func.value
        if not isinstance(button_call, ast.Call):
            continue
        if (
            not isinstance(button_call.func, ast.Attribute)
            or button_call.func.attr != "Button"
        ):
            continue
        if not button_call.args or ast.unparse(button_call.args[0]) != "bottom":
            continue
        button_keywords = {
            keyword.arg: keyword.value for keyword in button_call.keywords
        }
        pack_keywords = {keyword.arg: keyword.value for keyword in call.keywords}
        if (
            isinstance(button_keywords.get("text"), ast.Constant)
            and button_keywords["text"].value == "Zamknij"
            and ast.unparse(button_keywords.get("command")) == "self.destroy"
            and isinstance(pack_keywords.get("side"), ast.Constant)
            and pack_keywords["side"].value == "right"
        ):
            return

    raise AssertionError(
        "Nie znaleziono prawostronnego przycisku 'Zamknij' w dolnym pasku."
    )


def test_user_visible_help_and_behavior_labels_are_polish() -> None:
    """Sprawdź, że główne etykiety pomocy i zachowania są po polsku."""
    menu_source = GUI_MENU_PATH.read_text(encoding="utf-8")
    results_source = GUI_RESULTS_PATH.read_text(encoding="utf-8")

    assert 'label="Pomoc"' in menu_source
    assert 'label="Ustawienia"' in menu_source
    assert 'label="Help"' not in menu_source
    assert 'add_plot("Zachowanie"' in results_source
    assert 'add_plot("Behavior"' not in results_source


def test_advanced_command_values_are_displayed_in_polish() -> None:
    """Sprawdź, że techniczne komendy run/batch mają polskie etykiety w GUI."""
    from brain_model.gui_forms import COMMAND_LABELS

    assert COMMAND_LABELS == {"run": "uruchom", "batch": "seria uruchomień"}

    sections_source = GUI_SECTIONS_PATH.read_text(encoding="utf-8")
    assert "values=list(COMMAND_LABELS.values())" in sections_source
    assert 'values=["run", "batch"]' not in sections_source


def test_run_simulation_button_is_not_duplicated() -> None:
    """Sprawdź, że GUI pokazuje jeden główny przycisk uruchamiania symulacji."""
    legacy_button_count = GUI_LAYOUT_PATH.read_text(encoding="utf-8").count(
        'text="Uruchom symulację"'
    ) + GUI_SECTIONS_PATH.read_text(encoding="utf-8").count('text="Uruchom symulację"')
    qt_button_count = QT_APP_PATH.read_text(encoding="utf-8").count(
        'QPushButton("Uruchom symulację")'
    ) + QT_SECTIONS_PATH.read_text(encoding="utf-8").count(
        'QPushButton("Uruchom symulację")'
    )

    assert legacy_button_count == 1
    assert qt_button_count == 1


def test_qt_settings_menu_opens_parameter_dialogs() -> None:
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
    legacy_menu_source = GUI_MENU_PATH.read_text(encoding="utf-8")

    assert "class QtDataclassParameterDialog" in source
    assert 'label="Parametry modelu i oscylatorów..."' in legacy_menu_source


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
