"""Testy lekkiego kontraktu artefaktów reprodukowalności."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from brain_model.io import (
    REPRODUCIBILITY_ARTIFACTS,
    collect_environment_info,
    collect_git_info,
    save_run,
)


def test_reproducibility_manifest_lists_required_artifacts() -> None:
    """Kontrakt zapisu wyników wymienia wszystkie wymagane artefakty."""
    required_artifacts = {
        "config.json",
        "metrics.json",
        "environment.json",
        "git_info.json",
        "run.log",
        "metadata.json",
        "run_data.npz",
        "event_timeline.json",
    }

    assert required_artifacts.issubset(set(REPRODUCIBILITY_ARTIFACTS))


def test_environment_info_contains_required_dependency_keys() -> None:
    """Artefakt środowiska zawiera wersję Pythona, platformę i zależności."""
    environment = collect_environment_info()

    assert {"python_version", "platform", "dependencies"}.issubset(environment)
    assert {"numpy", "matplotlib", "PyYAML", "PySide6"}.issubset(
        environment["dependencies"]
    )


def test_git_info_contains_required_reproducibility_keys(tmp_path: Path) -> None:
    """Artefakt Git ma stabilne klucze także poza repozytorium."""
    git_info = collect_git_info(tmp_path)

    assert {"commit", "branch", "is_dirty"}.issubset(git_info)


def test_save_run_writes_reproducibility_artifacts(tmp_path: Path) -> None:
    """Zapis małych danych kontrolnych tworzy pełny zestaw plików manifestu."""
    save_info = save_run(
        tmp_path,
        time=np.array([0.0, 0.1]),
        activity=np.array([[0.1, 0.2], [0.2, 0.3]]),
        diagnostics={"mean_drive": np.array([0.1, 0.2])},
        oscillations={
            "eeg": np.array([[0.1], [0.2]]),
            "excitatory": np.array([[0.1, 0.2], [0.2, 0.3]]),
            "inhibitory": np.array([[0.05, 0.1], [0.1, 0.15]]),
            "band_power": {"alpha": np.array([1.0])},
            "frequency": np.array([8.0, 12.0]),
        },
        seed=7,
        duration_s=0.2,
        config={"rng_seed": 7, "task": {"name": "test"}},
        metrics={"metrics": {"behavior_mean": 0.5}},
        event_timeline=[{"time_s": 0.1, "event_type": "test_event"}],
    )

    for artifact_name in REPRODUCIBILITY_ARTIFACTS:
        assert (tmp_path / artifact_name).exists(), artifact_name
    assert {"config", "metrics", "environment", "git_info", "run_log"}.issubset(
        save_info
    )

    environment = _read_json(tmp_path / "environment.json")
    git_info = _read_json(tmp_path / "git_info.json")
    metrics = _read_json(tmp_path / "metrics.json")
    event_timeline = _read_json(tmp_path / "event_timeline.json")

    assert {"python_version", "platform", "dependencies"}.issubset(environment)
    assert {"commit", "branch", "is_dirty"}.issubset(git_info)
    assert metrics["metrics"]["behavior_mean"] == 0.5
    assert event_timeline == [{"time_s": 0.1, "event_type": "test_event"}]


def _read_json(path: Path) -> Any:
    """Odczytuje pomocniczy plik JSON utworzony przez test zapisu."""
    return json.loads(path.read_text(encoding="utf-8"))
