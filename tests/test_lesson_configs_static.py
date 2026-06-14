"""Statyczne testy katalogu lekcji dydaktycznych."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

LESSON_DIR = Path("configs/lessons")
REQUIRED_LESSON_IDS = {
    "roving_oddball_prediction",
    "go_nogo_inhibition",
    "n_back_working_memory",
    "stroop_conflict_control",
}
REQUIRED_KEYS = {
    "id",
    "label_pl",
    "level_pl",
    "estimated_duration_min",
    "scenario_config",
    "learning_goal_pl",
    "pre_run_questions_pl",
    "expected_observations_pl",
    "post_run_questions_pl",
    "next_run_changes",
}


def _load_lessons() -> list[dict[str, Any]]:
    """Wczytaj wszystkie lekcje YAML z katalogu konfiguracji."""
    lessons: list[dict[str, Any]] = []
    for path in sorted(LESSON_DIR.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path
        payload["_path"] = path
        lessons.append(payload)
    return lessons


def test_lesson_catalog_contains_required_ready_lessons() -> None:
    """Katalog lekcji obejmuje cztery podstawowe taski dydaktyczne."""
    lessons = _load_lessons()

    assert {lesson["id"] for lesson in lessons} >= REQUIRED_LESSON_IDS


def test_lesson_configs_have_reproducible_teaching_fields() -> None:
    """Każda lekcja wskazuje YAML, pytania, obserwacje i dalsze zmiany."""
    for lesson in _load_lessons():
        assert REQUIRED_KEYS.issubset(lesson), lesson["_path"]
        assert Path(lesson["scenario_config"]).exists(), lesson["_path"]
        comparison_config = lesson.get("comparison_config")
        if comparison_config is not None:
            assert Path(comparison_config).exists(), lesson["_path"]
        assert isinstance(lesson["estimated_duration_min"], int)
        assert lesson["estimated_duration_min"] > 0
        for list_key in (
            "pre_run_questions_pl",
            "expected_observations_pl",
            "post_run_questions_pl",
            "next_run_changes",
        ):
            assert isinstance(lesson[list_key], list), (lesson["_path"], list_key)
            assert lesson[list_key], (lesson["_path"], list_key)
