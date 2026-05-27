import pytest

from brain_core.experiments.protocols import GoNoGoTask, NBackTask, StroopTask
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import run_experiment
from typing import Any


def test_tasks_generate_deterministic_stimuli() -> Any:
    """Opis funkcji test_tasks_generate_deterministic_stimuli."""
    duration = 10.0
    s1 = StroopTask().generate_stimuli(seed=7, duration_s=duration)
    s2 = StroopTask().generate_stimuli(seed=7, duration_s=duration)
    assert s1 == s2

    g1 = GoNoGoTask().generate_stimuli(seed=7, duration_s=duration)
    g2 = GoNoGoTask().generate_stimuli(seed=7, duration_s=duration)
    assert g1 == g2

    n1 = NBackTask(n=2).generate_stimuli(seed=7, duration_s=duration)
    n2 = NBackTask(n=2).generate_stimuli(seed=7, duration_s=duration)
    assert n1 == n2


def test_trial_results_have_unified_schema_and_are_deterministic() -> Any:
    """Opis funkcji test_trial_results_have_unified_schema_and_are_deterministic."""
    cfg = ExperimentConfig(task={"name": "stroop", "scenario": "stroop", "duration": 5.0}, output={"save_results": False})
    r1 = run_experiment(cfg)
    r2 = run_experiment(cfg)

    assert r1["trial_results"] == r2["trial_results"]
    assert len(r1["trial_events"]) > 0

    first = r1["trial_results"][0]
    assert set(first.keys()) == {"trial_id", "reaction_time_s", "correct", "error_type", "condition"}
    assert isinstance(first["correct"], bool)


def test_all_task_configs_exist() -> Any:
    """Opis funkcji test_all_task_configs_exist."""
    pytest.importorskip("yaml")
    import yaml
    from pathlib import Path

    for path in ("configs/stroop.yaml", "configs/go_nogo.yaml", "configs/n_back.yaml"):
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        assert payload["task"]["name"]
