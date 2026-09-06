from typing import Any

from brain_core.simulation import ExperimentResult, run_experiment, run_experiment_legacy
from brain_core.simulation.config_schema import ExperimentConfig


def _legacy_payload() -> dict[str, Any]:
    """Zwróć minimalny słownik backendu dla testu publicznego API."""
    return {
        "model": "regional-model",
        "time": [0.0, 0.01],
        "activity": [[0.1], [0.2]],
        "diagnostics": {"stable": [True, True]},
        "oscillations": {"eeg": [0.1, 0.2]},
        "behavior": {"decision_score": [0.0, 0.1]},
        "trial_events": [],
        "trial_results": [],
        "trial_report_context": {"scenario": "test"},
        "stimulus_sequence_signature": {"count": 0},
        "event_timeline": [],
        "analysis_report": {"metrics": {"score": 1.0}, "comparison": {}},
        "task_activation": {"regions": ["VIS"]},
        "clinical_profile": {"id": "healthy_v1"},
        "snn_comparison": None,
        "save_info": None,
        "elapsed": 0.01,
        "randomness": {"seed": 7, "rng_seed": 7},
    }


def test_public_run_experiment_returns_typed_result(monkeypatch: Any) -> None:
    """Publiczny punkt wejścia zwraca ``ExperimentResult`` i zachowuje Mapping."""
    import brain_core.simulation.api as api

    monkeypatch.setattr(api, "_run_experiment_legacy", lambda *args, **kwargs: _legacy_payload())
    monkeypatch.setattr(api, "collect_git_info", lambda *args, **kwargs: {"commit": "abc"})
    monkeypatch.setattr(api, "collect_environment_info", lambda: {"python": "test"})

    config = ExperimentConfig(output={"save_results": False})
    result = run_experiment(config)

    assert isinstance(result, ExperimentResult)
    assert result["model"] == "regional-model"
    assert result.analysis_report["metrics"]["score"] == 1.0
    assert result.config is config


def test_legacy_entrypoint_returns_literal_dict(monkeypatch: Any) -> None:
    """Jawny adapter legacy zachowuje literalny typ ``dict``."""
    import brain_core.simulation.api as api

    payload = _legacy_payload()
    monkeypatch.setattr(api, "_run_experiment_legacy", lambda *args, **kwargs: payload)

    result = run_experiment_legacy(ExperimentConfig(output={"save_results": False}))

    assert type(result) is dict
    assert result is payload
