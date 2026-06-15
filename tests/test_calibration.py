from __future__ import annotations

from pathlib import Path
from typing import Any

from brain_model.calibration import run_sweep


def test_run_sweep_accepts_current_simulation_result_contract(tmp_path: Path) -> None:
    """Sweep kalibracyjny używa pełnego kontraktu wyniku symulacji z zachowaniem."""
    results = run_sweep(
        scenario="reward-learning",
        trials=1,
        method="random",
        time_horizon=0.02,
        seed=13,
        output_dir=str(tmp_path),
    )

    assert len(results) == 1
    assert results[0]["scenario"] == "reward-learning"
    assert (tmp_path / "calibration_reward-learning_random.jsonl").exists()
    assert (tmp_path / "calibration_reward-learning_random.csv").exists()
