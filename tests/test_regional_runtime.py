from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from brain_core.experiments.protocols import TrialStimulus
from brain_core.simulation.config_loader import load_config
from brain_core.simulation.random_sources import RandomSources
from brain_core.simulation.regional_runtime import (
    _delay_steps,
    run_regional_wilson_cowan,
)


def _short_config():
    config = load_config("configs/default.yaml")
    config.task["duration"] = 0.25
    config.output["save_results"] = False
    return config


def _visual_stimulus(amplitude: float = 1.0) -> list[TrialStimulus]:
    return [
        TrialStimulus(
            trial_id=1,
            onset_s=0.02,
            duration_s=0.12,
            payload={},
            condition="target",
            regional_input={"VIS": amplitude},
        )
    ]


def test_regional_runtime_is_reproducible_and_uses_atlas_shape() -> None:
    config = _short_config()
    first = run_regional_wilson_cowan(
        config,
        _visual_stimulus(),
        RandomSources(seed=13),
    )
    second = run_regional_wilson_cowan(
        config,
        _visual_stimulus(),
        RandomSources(seed=13),
    )

    assert first.region_names == second.region_names
    assert first.activity.shape[1] == 16
    assert first.activity.shape == first.excitatory.shape == first.inhibitory.shape
    np.testing.assert_allclose(first.activity, second.activity)
    np.testing.assert_allclose(
        first.behavior["decision_score"],
        second.behavior["decision_score"],
    )


def test_stronger_regional_stimulus_changes_neural_trajectory() -> None:
    config = _short_config()
    weak = run_regional_wilson_cowan(
        config,
        _visual_stimulus(0.25),
        RandomSources(seed=2),
    )
    strong = run_regional_wilson_cowan(
        config,
        _visual_stimulus(1.5),
        RandomSources(seed=2),
    )
    vis = weak.region_names.index("VIS")

    assert np.max(strong.excitatory[:, vis]) > np.max(weak.excitatory[:, vis])
    assert not np.allclose(strong.activity, weak.activity)


def test_fiber_length_controls_delay_steps() -> None:
    short = _delay_steps(np.array([[0.0, 10.0], [10.0, 0.0]]), 0.001, 5.0)
    long = _delay_steps(np.array([[0.0, 50.0], [50.0, 0.0]]), 0.001, 5.0)

    assert short[0, 1] == 2
    assert long[0, 1] == 10
    assert long[0, 1] > short[0, 1]


def _rewrite_weight(
    source: Path,
    destination: Path,
    target_row: str,
    target_column: str,
    value: float,
) -> None:
    with source.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    column = rows[0].index(target_column)
    for row in rows[1:]:
        if row[0] == target_row:
            row[column] = str(value)
            break
    with destination.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def test_changing_connectome_changes_propagation(tmp_path: Path) -> None:
    source_root = Path("data/connectomes")
    weights_path = tmp_path / "weights.csv"
    lengths_path = tmp_path / "fiber_lengths.csv"
    _rewrite_weight(
        source_root / "weights.csv",
        weights_path,
        target_row="SAL",
        target_column="VIS",
        value=0.0,
    )
    lengths_path.write_text(
        (source_root / "fiber_lengths.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    baseline_config = _short_config()
    altered_config = _short_config()
    altered_config.connectome["weights"] = str(weights_path)
    altered_config.connectome["fiber_lengths"] = str(lengths_path)

    baseline = run_regional_wilson_cowan(
        baseline_config,
        _visual_stimulus(),
        RandomSources(seed=5),
    )
    altered = run_regional_wilson_cowan(
        altered_config,
        _visual_stimulus(),
        RandomSources(seed=5),
    )
    sal = baseline.region_names.index("SAL")

    assert not np.allclose(baseline.excitatory[:, sal], altered.excitatory[:, sal])
