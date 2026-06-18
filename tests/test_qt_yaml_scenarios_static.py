"""Statyczne testy wyboru konfiguracji YAML w GUI PySide6."""

from __future__ import annotations

import ast
from pathlib import Path

from brain_model.qt_config import (
    SCENARIO_YAML_DESCRIPTIONS,
    SCENARIO_YAML_PRESETS,
    load_scenario_yaml_config,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_CONFIG_PATH = REPO_ROOT / "brain_model" / "qt_config.py"
QT_RUNNER_PATH = REPO_ROOT / "brain_model" / "qt_runner.py"
QT_SECTIONS_PATH = REPO_ROOT / "brain_model" / "qt_sections.py"
QT_RESULTS_PATH = REPO_ROOT / "brain_model" / "qt_results.py"


def _source(path: Path) -> str:
    """Zwróć tekst źródłowy pliku do prostych asercji statycznych."""
    return path.read_text(encoding="utf-8")


def _function_source(path: Path, function_name: str) -> str:
    """Zwróć znormalizowany kod źródłowy funkcji z analizowanego pliku."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    return ast.unparse(node)


def test_qt_config_exposes_required_yaml_scenario_presets() -> None:
    """GUI udostępnia wymagane scenariusze YAML: trzy roving oddball i demo SNN."""
    preset_paths = {str(path) for _label, path in SCENARIO_YAML_PRESETS}

    assert "configs/roving_oddball_healthy.yaml" in preset_paths
    assert "configs/roving_oddball_disorder_gaba.yaml" in preset_paths
    assert "configs/roving_oddball_lesion_hippocampus.yaml" in preset_paths
    assert "configs/snn_hippocampus_demo.yaml" in preset_paths
    assert "configs/scenario_yaml_stroop_dlpfc.yaml" in preset_paths
    assert "configs/scenario_yaml_go_nogo_gaba.yaml" in preset_paths
    assert "configs/scenario_yaml_n_back_dopamine.yaml" in preset_paths
    assert "configs/scenario_yaml_stress_recovery_serotonin.yaml" in preset_paths


def test_yaml_presets_validate_and_include_clinical_profile_fields() -> None:
    """Każdy preset YAML przechodzi walidację silnika i ma pola profilu klinicznego."""
    for _label, path in SCENARIO_YAML_PRESETS:
        config = load_scenario_yaml_config(path)

        assert config.clinical_profile["mechanism"]
        assert isinstance(config.clinical_profile["affected_regions"], list)
        assert isinstance(config.clinical_profile["cognitive_functions"], list)


def test_qt_sections_load_yaml_config_instead_of_recreating_task_logic() -> None:
    """Sekcja GUI ładuje konfigurację YAML i nie importuje protokołów tasków."""
    source = _source(QT_SECTIONS_PATH)
    apply_source = _function_source(QT_SECTIONS_PATH, "apply_scenario_yaml_config")

    assert "scenario_yaml_preset_labels" in source
    assert "load_scenario_yaml_config(selected_path)" in apply_source
    assert "show_clinical_profile" in apply_source
    assert "brain_core.experiments" not in source
    assert "get_task" not in source
    assert "TaskStimulusPlayer" not in source


def test_qt_sections_expose_ready_lessons_as_yaml_presets() -> None:
    """Szybki start pozwala wybrać lekcję bez dopisywania logiki tasków do GUI."""
    source = _source(QT_SECTIONS_PATH)
    lesson_source = _function_source(QT_SECTIONS_PATH, "apply_ready_lesson")

    assert "load_lesson_catalog" in source
    assert "lesson_by_label" in source
    assert "READY_LESSON_PRESETS" not in source
    assert "self.ready_lesson_combo" in source
    assert "label_for_scenario_yaml_path(lesson.scenario_config)" in lesson_source
    assert (
        "write_combo_box(self.scenario_config_combo, lesson_config_label)"
        in lesson_source
    )


def test_qt_sections_describe_each_yaml_configuration() -> None:
    """GUI wyjaśnia użytkownikowi cel i różnice każdego presetu YAML."""
    source = _source(QT_SECTIONS_PATH)
    description_source = _function_source(
        QT_SECTIONS_PATH, "refresh_scenario_config_description"
    )
    preset_labels = {label for label, _path in SCENARIO_YAML_PRESETS}

    assert set(SCENARIO_YAML_DESCRIPTIONS) == preset_labels
    assert all(SCENARIO_YAML_DESCRIPTIONS[label] for label in preset_labels)
    assert all(
        "Wybierz" in SCENARIO_YAML_DESCRIPTIONS[label] for label in preset_labels
    )
    assert all(
        "Różni się" in SCENARIO_YAML_DESCRIPTIONS[label] for label in preset_labels
    )
    assert "self.scenario_config_description_label" in source
    assert "scenario_yaml_description_for_label(selected_label)" in description_source
    assert "scenario_yaml_path_for_label(selected_label)" in description_source
    assert "Plik YAML" in description_source


def test_advanced_batch_scenarios_are_not_a_duplicate_quick_start_choice() -> None:
    """Opcje zaawansowane opisują scenariusze serii jako pole trybu batch."""
    source = _source(QT_SECTIONS_PATH)
    advanced_source = _function_source(
        QT_SECTIONS_PATH, "build_advanced_options_section"
    )

    assert "scenariusze serii (batch)" in advanced_source
    assert "Tylko dla trybu serii" in advanced_source
    assert "Nie zmienia pojedynczego scenariusza z sekcji Szybki start" in source
    assert "To nie jest drugi wybór scenariusza" in advanced_source


def test_teacher_panels_do_not_import_task_protocols() -> None:
    """Panele nauczyciela nie importują protokołów tasków z brain_core."""
    source = _source(QT_RESULTS_PATH)

    assert "brain_core.experiments.protocols" not in source
    assert "from brain_core.experiments" not in source
    assert "get_task" not in source
    assert "TaskStimulusPlayer" not in source


def test_qt_results_have_teacher_lesson_panel_without_task_protocols() -> None:
    """Panel lekcji nauczyciela korzysta z YAML i artefaktów, nie z protokołów."""
    source = _source(QT_RESULTS_PATH)

    assert "class TeacherLessonPanel" in source
    assert "Hipoteza przed uruchomieniem" in source
    assert "Ograniczenia interpretacyjne" in source
    assert "learning_goal_pl" in source
    assert "pre_run_questions_pl" in source
    assert "expected_observations_pl" in source
    assert "post_run_questions_pl" in source
    assert "next_run_changes" in source
    assert "lesson_steps_pl" in source
    assert "expected_report_pl" in source
    assert "assessment_criteria_pl" in source
    assert "Checklista lekcji" in source
    assert "Kryteria oceny odpowiedzi" in source
    assert "Raport porównawczy" in source
    assert "scenario_config" in source
    assert "comparison_config" in source
    assert "brain_core.experiments.protocols" not in source
    assert "from brain_core.experiments" not in source
    assert "get_task" not in source
    assert "TaskStimulusPlayer" not in source


def test_qt_runner_delegates_execution_to_brain_core_engine_only() -> None:
    """Worker GUI buduje konfigurację i deleguje wykonanie do `run_experiment`."""
    source = _source(QT_RUNNER_PATH)
    run_source = _function_source(QT_RUNNER_PATH, "run_single_experiment")

    assert "from brain_core.simulation.engine import run_experiment" in source
    assert (
        "return run_experiment(cfg, progress_callback=progress_callback)" in run_source
    )
    assert "from .model import CognitiveBrainModel" not in source
    assert "get_task" not in source
    assert "TaskStimulusPlayer" not in source


def test_qt_results_have_event_timeline_filter_and_clinical_profile_panel() -> None:
    """GUI ma panel osi czasu filtrowany typem oraz panel profilu klinicznego."""
    source = _source(QT_RESULTS_PATH)

    assert "class EventTimelinePanel" in source
    assert "event_type_filter" in source
    assert 'str(event.get("event_type", "n/a")) == selected_type' in source
    assert "class ClinicalProfilePanel" in source
    assert "mechanism" in source
    assert "affected_regions" in source
    assert "cognitive_functions" in source


def test_qt_results_have_teacher_observation_and_roving_questions_panels() -> None:
    """Panel nauczyciela bazuje na osi czasu, profilu i raporcie roving oddball."""
    source = _source(QT_RESULTS_PATH)

    assert "class ObservationPanel" in source
    assert "Co obserwujesz?" in source
    assert "event_timeline" in source
    assert "clinical_profile" in source
    assert (
        "analysis_report.get('roving_oddball', {})" in source
        or 'analysis_report.get("roving_oddball", {})' in source
    )
    assert "class RovingOddballQuestionsPanel" in source
    assert "Panel pytań kontrolnych: roving oddball" in source
    assert "standard" in source
    assert "dewiant" in source
    assert "habituację" in source
    assert "readaptację" in source


def test_qt_results_have_generic_lesson_questions_panel() -> None:
    """Panel pytań lekcji używa metadanych YAML bez logiki protokołów tasków."""
    source = _source(QT_RESULTS_PATH)

    assert "class LessonQuestionsPanel" in source
    assert "Pytania przed uruchomieniem" in source
    assert "Pytania po uruchomieniu" in source
    assert "brain_core.experiments.protocols" not in source
    assert "from brain_core.experiments" not in source
    assert "get_task" not in source
    assert "TaskStimulusPlayer" not in source


def test_qt_yaml_presets_have_user_facing_descriptions() -> None:
    """GUI opisuje po polsku cel każdego wyboru gotowej konfiguracji YAML."""
    config_source = _source(QT_CONFIG_PATH)
    sections_source = _source(QT_SECTIONS_PATH)

    assert "SCENARIO_YAML_DESCRIPTIONS" in config_source
    assert "scenario_yaml_description_for_label" in config_source
    assert "self.scenario_config_description" in sections_source
    assert "po co ten wybór" in sections_source
    assert "Profil referencyjny bez patologii" in config_source
    assert "obniżoną inhibicją GABA" in config_source
    assert "uszkodzenia hipokampa" in config_source
    assert "osłabienia DLPFC" in config_source
    assert "hamowania reakcji" in config_source
    assert "deficyt dopaminowy" in config_source
    assert "równowagi serotoninowej" in config_source


def test_teacher_panel_does_not_import_task_protocols() -> None:
    """Panel nauczyciela nie importuje protokołów tasków ani logiki brain_core."""
    tree = ast.parse(QT_RESULTS_PATH.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert "brain_core.experiments.protocols" not in imports
    assert all(not item.startswith("brain_core.experiments") for item in imports)
    source = _source(QT_RESULTS_PATH)
    assert "sequence_signature" in source
    assert "run_experiment()" in source
