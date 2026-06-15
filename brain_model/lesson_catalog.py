"""Loader katalogu lekcji dydaktycznych z plików YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
LESSON_CATALOG_DIR = REPO_ROOT / "configs" / "lessons"


def load_lesson_catalog(
    lesson_dir: Path = LESSON_CATALOG_DIR,
) -> dict[str, dict[str, Any]]:
    """Wczytaj katalog lekcji dydaktycznych z plików YAML.

    Parameters
    ----------
    lesson_dir:
        Katalog z plikami YAML opisującymi lekcje prezentowane w GUI.

    Returns
    -------
    dict[str, dict[str, Any]]
        Słownik lekcji indeksowany identyfikatorem z pola ``id``.

    Raises
    ------
    ValueError
        Gdy plik lekcji nie zawiera mapy YAML albo poprawnego identyfikatora.
    """

    lessons: dict[str, dict[str, Any]] = {}
    for lesson_path in sorted(lesson_dir.glob("*.yaml")):
        payload = yaml.safe_load(lesson_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Lekcja {lesson_path} nie zawiera mapy YAML.")
        lesson_id = payload.get("id")
        if not isinstance(lesson_id, str) or not lesson_id.strip():
            raise ValueError(f"Lekcja {lesson_path} nie zawiera poprawnego pola id.")
        lessons[lesson_id] = payload
    return lessons


def get_lesson_by_id(lesson_id: str) -> dict[str, Any] | None:
    """Zwróć metadane lekcji z katalogu YAML.

    Parameters
    ----------
    lesson_id:
        Identyfikator lekcji z pola ``id`` w pliku YAML.

    Returns
    -------
    dict[str, Any] | None
        Dane lekcji albo ``None``, gdy identyfikator nie istnieje w katalogu.
    """

    return load_lesson_catalog().get(lesson_id)
