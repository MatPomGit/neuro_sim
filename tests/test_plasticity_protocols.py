import numpy as np

from brain_core.experiments.protocols import ProtocolPhase, default_train_test_protocol
from brain_core.synapses.plasticity import (
    NeuralMassPlasticityConfig,
    PlasticityTracker,
    update_weights_two_timescales,
)
from typing import Any


def test_protocol_contains_train_and_test_phases() -> Any:
    """Opis funkcji test_protocol_contains_train_and_test_phases."""
    protocol = default_train_test_protocol()
    phases = {step.phase for step in protocol.steps}
    assert phases == {ProtocolPhase.TRAIN, ProtocolPhase.TEST}
    assert protocol.total_duration(ProtocolPhase.TRAIN) > protocol.total_duration(ProtocolPhase.TEST)


def test_plasticity_update_clamps_and_records_metrics() -> Any:
    """Opis funkcji test_plasticity_update_clamps_and_records_metrics."""
    cfg = NeuralMassPlasticityConfig(
        eta=0.4,
        decay_lambda=0.01,
        homeostatic_rate=0.02,
        target_mean_weight=0.1,
        min_weight=0.0,
        max_weight=0.5,
        forgetting_rate=0.01,
        consolidation_rate=0.1,
    )
    W0 = np.array([[0.49, 0.45], [0.40, 0.48]])
    pre = np.array([0.9, 0.7])
    post = np.array([0.8, 0.6])

    W1, dW_fast, dW_slow = update_weights_two_timescales(W0, pre, post, neuromod=1.0, dt=0.2, config=cfg)

    assert W1.shape == W0.shape
    assert np.all(W1 >= cfg.min_weight)
    assert np.all(W1 <= cfg.max_weight)

    tracker = PlasticityTracker()
    tracker.record(W1, dW_fast, dW_slow)
    assert len(tracker.weight_history) == 1
    assert len(tracker.metrics_history) == 1
    assert "mean_weight" in tracker.metrics_history[0]
