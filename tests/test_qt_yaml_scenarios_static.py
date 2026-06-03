"""Statyczne testy wyboru konfiguracji YAML w GUI PySide6."""

from __future__ import annotations

import ast
from pathlib import Path

from brain_model.qt_config import SCENARIO_YAML_PRESETS, load_scenario_yaml_config

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
