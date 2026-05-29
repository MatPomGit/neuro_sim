"""Statyczne testy presetów wykresów w GUI PySide6."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_SECTIONS_PATH = REPO_ROOT / "brain_model" / "qt_sections.py"


def _method_node(method_name: str) -> ast.FunctionDef:
    """Znajdź metodę QtSections o podanej nazwie w źródle modułu."""
    tree = ast.parse(QT_SECTIONS_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    raise AssertionError(f"Nie znaleziono metody {method_name!r}.")


def _constant_string_set(node: ast.AST) -> set[str]:
    """Odczytaj literał set[str] z węzła AST."""
    if not isinstance(node, ast.Set):
        raise AssertionError("Oczekiwano literału set[str].")
    values: set[str] = set()
    for element in node.elts:
        if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
            raise AssertionError("Preset zawiera wartość inną niż stały tekst.")
        values.add(element.value)
    return values


def _preset_return_set(preset_name: str) -> set[str]:
    """Zwróć statycznie zdefiniowany zestaw kluczy dla wskazanego presetu."""
    method = _method_node("plot_preset_keys")
    for statement in method.body:
        if not isinstance(statement, ast.If):
            continue
        test = statement.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "preset_name"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == preset_name
        ):
            returns = [item for item in statement.body if isinstance(item, ast.Return)]
            if not returns:
                raise AssertionError(f"Preset {preset_name!r} nie zwraca wartości.")
            return _constant_string_set(returns[0].value)
    raise AssertionError(f"Nie znaleziono presetu {preset_name!r}.")


def test_qt_basic_plot_preset_uses_first_interpretation_plots() -> None:
    """Sprawdź zakres i opis podstawowego presetu wykresów Qt."""
    source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    assert _preset_return_set("Podstawowe") == {
        "activity",
        "behavior",
        "simulated_brain_activity",
        "scenario_timeline",
    }
    assert "Najważniejsze wykresy do pierwszej " in source
    assert "interpretacji wyniku" in source


def test_qt_diagnostic_plot_preset_keeps_diagnostics_eeg_and_band_power() -> None:
    """Sprawdź, że preset diagnostyczny zachowuje kluczowe wykresy analityczne."""
    assert {"diagnostics", "eeg", "band_power"}.issubset(
        _preset_return_set("Diagnostyczne")
    )


def test_qt_full_plot_preset_selects_all_available_plots() -> None:
    """Sprawdź, że pełny preset Qt wybiera wszystkie dostępne wykresy."""
    method = _method_node("plot_preset_keys")

    for statement in method.body:
        if not isinstance(statement, ast.If):
            continue
        if ast.unparse(statement.test) != "preset_name == 'Pełne'":
            continue
        returns = [item for item in statement.body if isinstance(item, ast.Return)]
        assert returns
        assert ast.unparse(returns[0].value) == "set(self.plot_checks)"
        return

    raise AssertionError("Preset 'Pełne' nie został znaleziony.")


class _FakeCheckBox:
    """Minimalny checkbox do testów logiki presetów bez tworzenia okna Qt."""

    def __init__(self, checked: bool) -> None:
        """Zapamiętaj początkowy stan zaznaczenia."""
        self._checked = checked

    def isChecked(self) -> bool:
        """Zwróć stan używany przez logikę presetów."""
        return self._checked


def _module_tree() -> ast.Module:
    """Wczytaj AST modułu Qt bez importowania bibliotek okienkowych."""
    return ast.parse(QT_SECTIONS_PATH.read_text(encoding="utf-8"))


def _function_source(method_name: str) -> str:
    """Zwróć źródło metody `QtSections` odczytane statycznie z AST."""
    return ast.unparse(_method_node(method_name))


def _plot_labels() -> dict[str, str]:
    """Odczytaj słownik etykiet wykresów bez importowania PySide6."""
    assignment = next(
        node
        for node in _module_tree().body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "PLOT_LABELS"
    )
    labels = ast.literal_eval(assignment.value)
    if not isinstance(labels, dict):
        raise AssertionError("PLOT_LABELS nie jest słownikiem.")
    return labels


def _preset_logic_class() -> type:
    """Zbuduj minimalną klasę z rzeczywistymi metodami presetów, bez importu Qt."""
    class_source = "class PresetLogic:\n"
    for method_name in ("plot_preset_keys", "plot_preset_summary"):
        method_source = _function_source(method_name)
        class_source += "\n".join(f"    {line}" for line in method_source.splitlines())
        class_source += "\n"
    namespace: dict[str, object] = {}
    exec(class_source, namespace)
    preset_logic = namespace["PresetLogic"]
    if not isinstance(preset_logic, type):
        raise AssertionError("Nie udało się zbudować klasy logiki presetów.")
    return preset_logic


def test_qt_plot_preset_logic_runs_without_window() -> None:
    """Sprawdź logikę presetów bez uruchamiania QApplication i okna."""
    plot_labels = _plot_labels()
    sections = _preset_logic_class()()
    sections.plot_checks = {
        name: _FakeCheckBox(name in {"activity", "eeg"}) for name in plot_labels
    }

    assert sections.plot_preset_keys("Podstawowe") == {
        "activity",
        "behavior",
        "simulated_brain_activity",
        "scenario_timeline",
    }
    assert {"diagnostics", "eeg", "band_power"}.issubset(
        sections.plot_preset_keys("Diagnostyczne")
    )
    assert sections.plot_preset_keys("Pełne") == set(plot_labels)
    assert sections.plot_preset_keys("Niestandardowe") == {"activity", "eeg"}
    assert "Aktywny zestaw: Diagnostyczne" in sections.plot_preset_summary(
        "Diagnostyczne"
    )
