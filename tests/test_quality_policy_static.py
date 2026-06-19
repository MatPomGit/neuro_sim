from __future__ import annotations

import ast
from pathlib import Path

import tomllib

PRODUCTION_DOCSTRING_SCOPES = ("brain_core/**/*.py", "brain_model/**/*.py")
STRICT_MYPY_MODULES = {
    "brain_model.oscillators",
    "brain_model.calibration",
    "brain_model.validation",
}
STRICT_NO_ANY_PATHS = (
    Path("brain_model/oscillators.py"),
    Path("brain_model/calibration.py"),
    Path("brain_model/validation.py"),
)


def _load_pyproject() -> dict[str, object]:
    """Wczytaj konfigurację projektu jako słownik TOML."""
    repo_root = Path(__file__).resolve().parents[1]
    with (repo_root / "pyproject.toml").open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def test_production_docstring_ignores_are_precise() -> None:
    """Produkcyjny kod nie może globalnie ignorować całej rodziny reguł D."""
    pyproject = _load_pyproject()
    per_file_ignores = pyproject["tool"]["ruff"]["lint"]["per-file-ignores"]

    for scope in PRODUCTION_DOCSTRING_SCOPES:
        ignored_rules = set(per_file_ignores[scope])
        assert "D" not in ignored_rules
        assert ignored_rules <= {
            "D100",
            "D104",
            "D107",
            "D200",
            "D202",
            "D205",
            "D212",
            "D214",
            "D301",
            "D401",
            "D405",
            "D411",
            "D413",
            "D415",
            "D416",
            "D417",
        }


def test_key_scientific_modules_require_complete_type_annotations() -> None:
    """Kluczowe moduły naukowe muszą zachować zaostrzone reguły mypy."""
    pyproject = _load_pyproject()
    overrides = pyproject["tool"]["mypy"]["overrides"]
    strict_modules: set[str] = set()
    for override in overrides:
        modules = override["module"]
        if isinstance(modules, str):
            modules = [modules]
        if override.get("disallow_untyped_defs") and override.get("disallow_incomplete_defs"):
            strict_modules.update(modules)

    assert STRICT_MYPY_MODULES <= strict_modules


def test_key_scientific_modules_do_not_use_unjustified_any() -> None:
    """Wybrane moduły naukowe nie powinny używać `Any` jako zastępczego typu."""
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for relative_path in STRICT_NO_ANY_PATHS:
        tree = ast.parse((repo_root / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                for alias in node.names:
                    if alias.name == "Any":
                        offenders.append(f"{relative_path}:{node.lineno}: import Any")
            elif isinstance(node, ast.Name) and node.id == "Any":
                offenders.append(f"{relative_path}:{node.lineno}: Any")
            elif isinstance(node, ast.Attribute) and node.attr == "Any":
                offenders.append(f"{relative_path}:{node.lineno}: typing.Any")

    assert not offenders, "Nieuzasadnione użycie Any:\n" + "\n".join(offenders)
