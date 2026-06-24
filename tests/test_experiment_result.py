from dataclasses import fields
from pathlib import Path
from typing import Any

from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.results import ExperimentResult

LEGACY_RESULT_KEYS = {
    "model",
    "time",
    "activity",
    "diagnostics",
    "oscillations",
    "behavior",
    "trial_events",
    "trial_results",
    "trial_report_context",
    "stimulus_sequence_signature",
    "event_timeline",
    "analysis_report",
    "task_activation",
    "clinical_profile",
    "snn_comparison",
    "save_info",
    "elapsed",
    "randomness",
}


def test_experiment_result_has_required_reproducibility_fields() -> Any:
    """Sprawdza jawne pola wyniku wymagane do reprodukcji eksperymentu."""
    result_fields = {field.name for field in fields(ExperimentResult)}

    assert {
        "config",
        "signals",
        "metrics",
        "trial_events",
        "analysis_report",
        "output_dir",
        "git_info",
        "environment_info",
    }.issubset(result_fields)


def test_experiment_result_exports_stable_legacy_keys() -> Any:
    """Sprawdza stabilność kluczy eksportowanych do starszego formatu API."""
    experiment_result = ExperimentResult(
        config=ExperimentConfig(output={"save_results": False}),
        signals={
            "model": "model",
            "time": [0.0],
            "activity": [[0.1]],
            "diagnostics": {"loss": [0.0]},
            "oscillations": {"eeg": [0.1]},
            "behavior": {"decision_score": [0.2]},
        },
        metrics={"metrics": {"accuracy": 1.0}},
        trial_events=[{"trial_id": 1}],
        analysis_report={"metrics": {"accuracy": 1.0}},
        output_dir=Path("outputs/example"),
        git_info={"commit": "abc", "branch": "main", "is_dirty": False},
        environment_info={"python_version": "3.x", "platform": "test"},
        trial_results=[{"trial_id": 1, "correct": True}],
        trial_report_context={"scenario": "test"},
        stimulus_sequence_signature={"count": 1},
        event_timeline=[{"time_s": 0.0}],
        task_activation={"regions": []},
        clinical_profile={"id": "healthy_v1"},
        snn_comparison=None,
        save_info=None,
        elapsed=0.1,
        randomness={"seed": 7, "rng_seed": 7},
    )

    legacy_result = experiment_result.to_legacy_dict()

    assert set(legacy_result) == LEGACY_RESULT_KEYS
    assert legacy_result["trial_events"] == experiment_result.trial_events
    assert legacy_result["analysis_report"] == experiment_result.analysis_report
    assert legacy_result["save_info"] is None
    assert legacy_result["randomness"] == experiment_result.randomness
