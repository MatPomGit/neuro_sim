from typing import Any

from brain_core.simulation import ExperimentResult, run_experiment, run_experiment_legacy
from brain_core.simulation.config_schema import ExperimentConfig


def _typed_result(config: ExperimentConfig) -> ExperimentResult:
    """Zwróć minimalny typowany wynik backendu dla testu publicznego API."""
    return ExperimentResult(
        config=config,
        signals={
            "model": "regional-model",
            "time": [0.0, 0.01],
            "activity": [[0.1], [0.2]],
            "diagnostics": {"stable": [True, True]},
            "oscillations": {"eeg": [0.1, 0.2]},
            "behavior": {"decision_score": [0.0, 0.1]},
        },
        metrics={
            "metrics": {"score": 1.0},
            "comparison": {},
            "randomness": {"seed": 7, "rng_seed": 7},
        },
        trial_events=[],
        analysis_report={"metrics": {"score": 1.0}, "comparison": {}},
        output_dir=None,
        git_info={"commit": "abc"},
        environment_info={"python": "test"},
        trial_results=[],
        trial_report_context={"scenario": "test"},
        stimulus_sequence_signature={"count": 0},
        event_timeline=[],
        task_activation={"regions": ["VIS"]},
        clinical_profile={"id": "healthy_v1"},
        snn_comparison=None,
        save_info=None,
        elapsed=0.01,
        randomness={"seed": 7, "rng_seed": 7},
    )


def test_public_run_experiment_returns_engine_result_without_reconstruction(
    monkeypatch: Any,
) -> None:
    """Publiczne API przekazuje bez zmian typowany wynik silnika."""
    import brain_core.simulation.api as api

    config = ExperimentConfig(output={"save_results": False})
    expected = _typed_result(config)
    monkeypatch.setattr(api, "_run_experiment", lambda *args, **kwargs: expected)

    result = run_experiment(config)

    assert result is expected
    assert isinstance(result, ExperimentResult)
    assert result["model"] == "regional-model"
    assert result.analysis_report["metrics"]["score"] == 1.0
    assert result.config is config


def test_legacy_entrypoint_converts_typed_result_to_literal_dict(
    monkeypatch: Any,
) -> None:
    """Jawny adapter legacy wykonuje jedyną konwersję wyniku do ``dict``."""
    import brain_core.simulation.api as api

    config = ExperimentConfig(output={"save_results": False})
    expected = _typed_result(config)
    monkeypatch.setattr(api, "_run_experiment", lambda *args, **kwargs: expected)

    result = run_experiment_legacy(config)

    assert type(result) is dict
    assert result == expected.to_legacy_dict()
    assert result["model"] == "regional-model"
