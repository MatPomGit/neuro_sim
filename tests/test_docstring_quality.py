from __future__ import annotations

import ast
from pathlib import Path

PLACEHOLDER_PHRASES = tuple(f"Opis {name}" for name in ("funkcji", "klasy"))
PRODUCTION_DIRS = ("brain_model", "brain_core", "brain_viewer", "analysis", "scripts")
TEST_DIR = "tests"


def test_production_docstrings_do_not_contain_placeholder_phrases() -> None:
    """Docstringi kodu produkcyjnego nie mogą zawierać fraz zastępczych."""
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for directory_name in PRODUCTION_DIRS:
        directory = repo_root / directory_name
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    continue
                docstring = ast.get_docstring(node) or ""
                for phrase in PLACEHOLDER_PHRASES:
                    if phrase in docstring:
                        offenders.append(
                            f"{path.relative_to(repo_root)}:{node.lineno}: "
                            f"{node.name}: {phrase}"
                        )

    assert not offenders, "Znaleziono zastępcze frazy w docstringach:\n" + "\n".join(
        offenders
    )


def test_test_docstrings_do_not_contain_placeholder_phrases() -> None:
    """Docstringi testów nie mogą zawierać fraz zastępczych."""
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for path in sorted((repo_root / TEST_DIR).rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                continue
            docstring = ast.get_docstring(node) or ""
            for phrase in PLACEHOLDER_PHRASES:
                if phrase in docstring:
                    offenders.append(
                        f"{path.relative_to(repo_root)}:{node.lineno}: "
                        f"{node.name}: {phrase}"
                    )

    assert not offenders, "Znaleziono zastępcze frazy w docstringach:\n" + "\n".join(
        offenders
    )
