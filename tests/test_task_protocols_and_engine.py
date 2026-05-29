import pytest

from brain_core.experiments.protocols import GoNoGoTask, NBackTask, RovingOddballTask, StroopTask, get_task
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

    r1 = RovingOddballTask(n_runs=3, run_length_min=2, run_length_max=4, jitter=0.05).generate_stimuli(seed=7, duration_s=duration)
    r2 = RovingOddballTask(n_runs=3, run_length_min=2, run_length_max=4, jitter=0.05).generate_stimuli(seed=7, duration_s=duration)
    assert r1 == r2


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

    for path in (
        "configs/stroop.yaml",
        "configs/go_nogo.yaml",
        "configs/n_back.yaml",
        "configs/roving_oddball_healthy.yaml",
        "configs/roving_oddball_disorder_gaba.yaml",
        "configs/roving_oddball_lesion_hippocampus.yaml",
    ):
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        assert payload["task"]["name"]


def test_roving_oddball_sequence_aliases_and_metrics() -> Any:
    """Sprawdza strukturę sekwencji i metryk trial-level dla roving oddball."""
    assert get_task("roving-oddball").name == "roving_oddball"
    task = RovingOddballTask(
        n_runs=3,
        run_length_min=2,
        run_length_max=2,
        deviant_probability=1.0,
        inter_stimulus_interval=0.5,
        jitter=0.0,
    )

    stimuli = task.generate_stimuli(seed=5, duration_s=10.0)

    assert [stim.condition for stim in stimuli] == [
        "standard",
        "standard",
        "deviant",
        "standard",
        "standard",
        "deviant",
        "standard",
        "standard",
    ]
    assert stimuli[3].payload["is_new_standard"] is True
    assert stimuli[3].payload["tone_hz"] == stimuli[2].payload["tone_hz"]
    for stimulus in stimuli:
        assert {"surprise_index", "habituation_level", "readaptation_latency"}.issubset(stimulus.payload)


def test_roving_oddball_trial_results_include_metrics() -> Any:
    """Sprawdza deterministyczność wyników i obecność metryk w silniku."""
    cfg = ExperimentConfig(
        task={
            "name": "roving_oddball",
            "scenario": "roving_oddball",
            "duration": 8.0,
            "n_runs": 3,
            "run_length_min": 2,
            "run_length_max": 2,
            "deviant_probability": 1.0,
            "inter_stimulus_interval": 0.5,
            "jitter": 0.0,
        },
        output={"save_results": False},
    )

    r1 = run_experiment(cfg)
    r2 = run_experiment(cfg)

    assert r1["trial_events"] == r2["trial_events"]
    assert r1["trial_results"] == r2["trial_results"]
    assert len(r1["trial_results"]) == 8
    assert {"surprise_index", "habituation_level", "readaptation_latency"}.issubset(r1["trial_results"][0])
    assert any(result["condition"] == "deviant" for result in r1["trial_results"])
