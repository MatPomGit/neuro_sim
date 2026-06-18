"""Statyczne testy katalogu lekcji dydaktycznych."""

from __future__ import annotations

from pathlib import Path

from brain_model.lesson_catalog import LESSON_CONFIG_DIR, load_lesson_catalog

REQUIRED_LESSON_IDS = {
    "roving_oddball_prediction",
    "go_nogo_inhibition",
    "n_back_working_memory",
    "stroop_conflict_control",
    "stress_recovery_emotion_regulation",
    "snn_hippocampus_cosimulation",
}


def test_lesson_catalog_contains_required_ready_lessons() -> None:
    """Katalog obejmuje podstawowe taski oraz lekcje stress-recovery i SNN."""
    lessons = load_lesson_catalog()

    assert {lesson.id for lesson in lessons} >= REQUIRED_LESSON_IDS


def test_lesson_loader_sees_all_lesson_yaml_files() -> None:
    """Loader katalogu zwraca jedną lekcję dla każdego pliku YAML."""
    lesson_paths = sorted(LESSON_CONFIG_DIR.glob("*.yaml"))
    lessons = load_lesson_catalog()

    assert lessons
    assert len(lessons) == len(lesson_paths)
    assert {lesson.id for lesson in lessons} == {path.stem for path in lesson_paths}


def test_lesson_configs_point_to_existing_yaml_files() -> None:
    """Każda lekcja wskazuje istniejący scenariusz i opcjonalne porównanie."""
    for lesson in load_lesson_catalog():
        assert Path(lesson.scenario_config).exists(), lesson.id
        if lesson.comparison_config is not None:
            assert Path(lesson.comparison_config).exists(), lesson.id


def test_lesson_labels_are_polish_and_not_empty() -> None:
    """Etykiety lekcji są niepustymi polskimi tekstami dla warstwy GUI."""
    for lesson in load_lesson_catalog():
        assert lesson.label_pl.strip(), lesson.id
        assert lesson.label_pl.startswith("Lekcja — "), lesson.id
        assert lesson.label_pl != lesson.id, lesson.id


def test_lesson_configs_have_reproducible_teaching_fields() -> None:
    """Każda lekcja zawiera metadane potrzebne do odtworzenia zajęć."""
    for lesson in load_lesson_catalog():
        assert lesson.estimated_duration_min > 0
        assert lesson.level_pl.strip(), lesson.id
        assert lesson.learning_goal_pl.strip(), lesson.id
        assert lesson.pre_run_questions_pl, lesson.id
        assert lesson.expected_observations_pl, lesson.id
        assert lesson.post_run_questions_pl, lesson.id
        assert lesson.next_run_changes, lesson.id


def test_lesson_ids_and_labels_are_unique_and_match_file_names() -> None:
    """Identyfikatory są unikalne, a nazwy plików odpowiadają polu ``id``."""
    lessons = load_lesson_catalog()
    lesson_ids = [lesson.id for lesson in lessons]
    lesson_labels = [lesson.label_pl for lesson in lessons]

    assert len(lesson_ids) == len(set(lesson_ids))
    assert len(lesson_labels) == len(set(lesson_labels))
    assert set(lesson_ids) == {path.stem for path in LESSON_CONFIG_DIR.glob("*.yaml")}


def test_next_run_changes_have_complete_comparison_fields() -> None:
    """Każda sugestia kolejnego przebiegu opisuje jedną jawną zmianę."""
    required_change_fields = {
        "element",
        "current_value",
        "next_value",
        "reason",
    }

    for lesson in load_lesson_catalog():
        for change in lesson.next_run_changes:
            assert set(change) == required_change_fields, lesson.id
            assert all(value.strip() for value in change.values()), lesson.id
