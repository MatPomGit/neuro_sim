import time

import numpy as np

from brain_core.simulation.multiscale_engine import MultiScaleEngine, TimeScaleTask
from brain_core.simulation.state import SimulationState


class CounterModule:
    def __init__(self):
        self.steps = 0

    def update(self, state: SimulationState, dt: float) -> None:
        self.steps += 1
        state.metrics.setdefault("acc", 0.0)
        state.metrics["acc"] += 0.001 * dt


def test_multiscale_scheduler_respects_different_dt():
    fast = CounterModule()
    slow = CounterModule()
    engine = MultiScaleEngine(0.001, [TimeScaleTask("neural_mass", fast, 0.001), TimeScaleTask("snn_sync", slow, 0.005)])
    state = SimulationState()

    for _ in range(20):
        counts = engine.run_step(state)

    assert fast.steps == 20
    assert slow.steps == 4
    assert counts["neural_mass"] == 1
    assert state.step == 20
    assert np.isfinite(state.metrics["acc"])


def test_cosim_performance_and_numerical_stability_smoke():
    fast = CounterModule()
    slow = CounterModule()
    engine = MultiScaleEngine(0.001, [TimeScaleTask("hippocampus_nm", fast, 0.001), TimeScaleTask("dlpfc_snn", slow, 0.002)])
    state = SimulationState()

    t0 = time.perf_counter()
    for _ in range(10_000):
        engine.run_step(state)
    elapsed = time.perf_counter() - t0

    assert elapsed < 10.0
    assert state.step == 10_000
    assert np.isfinite(state.time)
    assert np.isfinite(state.metrics["acc"])
