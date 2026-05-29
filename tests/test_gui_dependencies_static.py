"""Statyczne testy zależności desktopowego GUI."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
ENVIRONMENT_PATH = REPO_ROOT / "environment.yml"


def _dependency_name(requirement: str) -> str:
    """Zwróć znormalizowaną nazwę pakietu z wpisu zależności."""
    return re.split(r"[<>=!~ ]", requirement.strip(), maxsplit=1)[0].lower()


def test_pyside6_is_declared_in_project_dependencies() -> None:
    """Sprawdź, że PySide6 pozostaje zależnością uruchomieniową projektu."""
    project = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]

    assert "pyside6" in {_dependency_name(dependency) for dependency in dependencies}


def test_pyside6_is_declared_in_environment_files() -> None:
    """Sprawdź spójność deklaracji PySide6 w plikach środowiska."""
    requirements = REQUIREMENTS_PATH.read_text(encoding="utf-8")
    environment = ENVIRONMENT_PATH.read_text(encoding="utf-8")

    assert re.search(r"^PySide6\s*>=\s*6\.6", requirements, flags=re.MULTILINE)
    assert re.search(r"^\s*-\s*pyside6\s*>=\s*6\.6", environment, flags=re.MULTILINE)
