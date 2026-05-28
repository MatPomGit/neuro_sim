"""Statyczne testy spójności układu GUI."""

from __future__ import annotations

import ast
from pathlib import Path

GUI_LAYOUT_PATH = Path(__file__).resolve().parents[1] / "brain_model" / "gui_layout.py"


def _constant_int_keyword(call: ast.Call, name: str, default: int | None = None) -> int | None:
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
    tree = ast.parse(GUI_LAYOUT_PATH.read_text(encoding="utf-8"))
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
    tree = ast.parse(GUI_LAYOUT_PATH.read_text(encoding="utf-8"))
    body = _method_body(tree, "_add_labeled_entry")
    grid_calls = [node for stmt in body for node in ast.walk(stmt) if isinstance(node, ast.Call)]
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
    tree = ast.parse(GUI_LAYOUT_PATH.read_text(encoding="utf-8"))
    body = _method_body(tree, "_build_advanced_options_section")
    labels_to_rows: dict[str, int] = {}

    for call in [node for stmt in body for node in ast.walk(stmt) if isinstance(node, ast.Call)]:
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "_add_labeled_entry":
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
