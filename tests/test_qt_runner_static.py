"""Statyczne testy workera symulacji PySide6."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_APP_PATH = REPO_ROOT / "brain_model" / "qt_app.py"
QT_RUNNER_PATH = REPO_ROOT / "brain_model" / "qt_runner.py"


def _class_node(path: Path, class_name: str) -> ast.ClassDef:
    """Zwróć węzeł AST klasy o podanej nazwie z analizowanego pliku."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )


def _method_source(path: Path, method_name: str, class_name: str) -> str:
    """Zwróć znormalizowany kod źródłowy metody o podanej nazwie."""
    class_node = _class_node(path, class_name)
    method = next(
        node
        for node in ast.walk(class_node)
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )
    return ast.unparse(method)


def test_simulation_worker_is_qobject_with_required_signals() -> None:
    """Worker PySide6 dziedziczy po QObject i udostępnia wymagane sygnały."""
    class_node = _class_node(QT_RUNNER_PATH, "SimulationWorker")
    bases = {ast.unparse(base) for base in class_node.bases}
    assignments = {
        target.id: ast.unparse(statement.value)
        for statement in class_node.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name)
    }

    assert bases == {"QObject"}
    assert assignments["progress"] == "Signal(float)"
    assert assignments["done"] == "Signal(object)"
    assert assignments["warning"] == "Signal(str)"
    assert assignments["error"] == "Signal(str)"


def test_qt_window_runs_worker_in_dedicated_qthread() -> None:
    """Główne okno przenosi worker QObject do osobnego QThread."""
    source = _method_source(QT_APP_PATH, "start_simulation", "BrainModelQtWindow")

    assert "self.worker_thread = QThread(self)" in source
    assert "self.worker.moveToThread(self.worker_thread)" in source
    assert "self.worker_thread.started.connect(self.worker.run)" in source
    assert "self.worker.progress.connect(self.on_progress_changed)" in source
    assert "self.worker.done.connect(self.on_simulation_result)" in source
    assert "self.worker.error.connect(self.on_simulation_error)" in source


def test_qt_window_blocks_close_while_worker_is_active() -> None:
    """Aktywna symulacja blokuje zamknięcie okna jasnym komunikatem."""
    source = _method_source(QT_APP_PATH, "closeEvent", "BrainModelQtWindow")

    assert "if self._simulation_in_progress():" in source
    assert "Zamknięcie okna będzie możliwe po zakończeniu obliczeń." in source
    assert "event.ignore()" in source
    assert "super().closeEvent(event)" in source
