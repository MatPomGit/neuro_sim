import time
from typing import Any

import numpy as np
import pytest

from brain_core.networks.delays import DelayBuffer
from brain_core.simulation.multiscale_engine import (
    ClosedLoopFeedbackPath,
    MultiScaleEngine,
    MultiScaleIOContract,
    TimeScaleTask,
)
from brain_core.simulation.state import SimulationState


class CounterModule:
    """Moduł testowy zliczający kroki i akumulujący prostą metrykę."""

    def __init__(self) -> None:
        """Inicjalizuje licznik wykonanych kroków modułu testowego."""
        self.steps: int = 0

    def update(self, state: SimulationState, dt: float) -> None:
        """Zwiększa licznik i dopisuje deterministyczny wkład do metryki."""
        self.steps += 1
        state.metrics.setdefault("acc", 0.0)
        state.metrics["acc"] += 0.001 * dt


def test_multiscale_scheduler_respects_different_dt() -> Any:
    """Sprawdza harmonogram uruchamiania zadań o różnych krokach czasowych."""
    fast = CounterModule()
    slow = CounterModule()
    contract = MultiScaleIOContract(
        base_dt=0.001,
        snn_sync_dt=0.005,
        rate_unit="Hz",
        activity_unit="fraction",
        mapped_populations=("hippocampus",),
    )
    engine = MultiScaleEngine(
        0.001,
        [
            TimeScaleTask("neural_mass", fast, 0.001),
            TimeScaleTask("snn_sync", slow, 0.005),
        ],
        io_contract=contract,
    )
    state = SimulationState()

    for _ in range(20):
        counts = engine.run_step(state)

    assert fast.steps == 20
    assert slow.steps == 4
    assert counts["neural_mass"] == 1
    assert state.step == 20
    assert np.isfinite(state.metrics["acc"])


def test_cosim_performance_and_numerical_stability_smoke() -> Any:
    """Sprawdza wydajność i stabilność numeryczną długiej symulacji smoke."""
    fast = CounterModule()
    slow = CounterModule()
    engine = MultiScaleEngine(
        0.001,
        [
            TimeScaleTask("hippocampus_nm", fast, 0.001),
            TimeScaleTask("dlpfc_snn", slow, 0.002),
        ],
    )
    state = SimulationState()

    t0 = time.perf_counter()
    for _ in range(10_000):
        engine.run_step(state)
    elapsed = time.perf_counter() - t0

    assert elapsed < 10.0
    assert state.step == 10_000
    assert np.isfinite(state.time)
    assert np.isfinite(state.metrics["acc"])


def test_delay_buffer_length_and_no_nan_drift() -> Any:
    """Sprawdza długość bufora opóźnień i brak dryfu do wartości NaN."""
    delays = np.array([[0, 3], [2, 0]])
    buffer = DelayBuffer(n_regions=2, delays_steps=delays)

    for _ in range(5000):
        buffer.push(np.array([0.1, 0.2]))
        delayed = buffer.delayed_activity_matrix()
        assert delayed.shape == (2, 2)
        assert np.all(np.isfinite(delayed))

    assert buffer._history.shape[0] == int(np.max(delays)) + 1


class FeedbackWriterModule:
    """Moduł testowy zapisujący deterministyczne wyjście SNN do stanu."""

    def __init__(self, drive: float) -> None:
        """Zapamiętuje amplitudę sygnału zwrotnego dla kolejnych kroków."""
        self.drive = drive

    def update(self, state: SimulationState, dt: float) -> None:
        """Zapisuje sygnał zwrotny SNN w metrykach stanu symulacji."""
        state.metrics["snn_closed_loop_drive"] = {"HIP": self.drive}


def test_closed_loop_feedback_path_applies_snn_drive_one_step_later() -> Any:
    """Ścieżka closed-loop dopisuje ograniczony sygnał do wejścia HIP z opóźnieniem."""
    state = SimulationState()
    writer = FeedbackWriterModule(drive=0.3)
    feedback = ClosedLoopFeedbackPath(target_region_name="HIP", max_abs_amplitude=0.15)
    engine = MultiScaleEngine(
        0.001,
        [TimeScaleTask("snn_sync", writer, 0.001)],
        closed_loop_feedback=feedback,
    )

    engine.run_step(state)
    first_drive = state.metrics["neural_mass_external_drive"]["HIP"]
    engine.run_step(state)
    second_drive = state.metrics["neural_mass_external_drive"]["HIP"]

    assert first_drive == 0.0
    assert second_drive == 0.15
    assert np.isfinite(second_drive)


def test_multiscale_engine_counts_are_deterministic_for_repeated_runs() -> Any:
    """Scheduler zachowuje deterministyczne liczniki i stabilne metryki."""
    observed_counts: list[dict[str, int]] = []
    observed_metrics: list[float] = []

    for _ in range(2):
        fast = CounterModule()
        slow = CounterModule()
        contract = MultiScaleIOContract(
            base_dt=0.001,
            snn_sync_dt=0.004,
            rate_unit="Hz",
            activity_unit="fraction",
            mapped_populations=("HIP",),
        )
        engine = MultiScaleEngine(
            0.001,
            [
                TimeScaleTask("neural_mass", fast, 0.001),
                TimeScaleTask("snn_sync", slow, 0.004),
            ],
            io_contract=contract,
        )
        state = SimulationState()
        last_counts: dict[str, int] = {}

        for _step_index in range(16):
            last_counts = engine.run_step(state)

        observed_counts.append({"fast": fast.steps, "slow": slow.steps, **last_counts})
        observed_metrics.append(state.metrics["acc"])

    assert observed_counts[0] == observed_counts[1]
    assert observed_counts[0]["fast"] == 16
    assert observed_counts[0]["slow"] == 4
    assert observed_counts[0]["neural_mass"] == 1
    assert np.all(np.isfinite(observed_metrics))
    assert observed_metrics[0] == observed_metrics[1]


def test_delay_buffer_rejects_negative_delays_with_contract_name() -> None:
    """Ujemne opóźnienia przewodzenia są błędem kontraktu B."""
    with pytest.raises(ValueError, match="Kontrakt B"):
        DelayBuffer(n_regions=2, delays_steps=np.array([[0, -1], [1, 0]]))
