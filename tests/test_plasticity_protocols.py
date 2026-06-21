from typing import Any

import numpy as np
import pytest

from brain_core.experiments.protocols import ProtocolPhase, default_train_test_protocol
from brain_core.synapses.plasticity import (
    NeuralMassPlasticityConfig,
    PlasticityTracker,
    update_weights_two_timescales,
)
from brain_model.plasticity import (
    ConnectivityAdaptationConfig,
    HebbianRuleConfig,
    update_connectivity,
)


def test_protocol_contains_train_and_test_phases() -> Any:
    """Sprawdza obecność faz treningowej i testowej w protokole."""
    protocol = default_train_test_protocol()
    phases = {step.phase for step in protocol.steps}
    assert phases == {ProtocolPhase.TRAIN, ProtocolPhase.TEST}
    assert protocol.total_duration(ProtocolPhase.TRAIN) > protocol.total_duration(
        ProtocolPhase.TEST
    )


def test_plasticity_update_clamps_and_records_metrics() -> Any:
    """Sprawdza obcięcie wag plastyczności i zapis metryk aktualizacji."""
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

    W1, dW_fast, dW_slow = update_weights_two_timescales(
        W0, pre, post, neuromod=1.0, dt=0.2, config=cfg
    )

    assert W1.shape == W0.shape
    assert np.all(W1 >= cfg.min_weight)
    assert np.all(W1 <= cfg.max_weight)

    tracker = PlasticityTracker()
    tracker.record(W1, dW_fast, dW_slow)
    assert len(tracker.weight_history) == 1
    assert len(tracker.metrics_history) == 1
    assert "mean_weight" in tracker.metrics_history[0]


def test_connectivity_update_rejects_invalid_weight_update_diagnostics() -> Any:
    """Adaptacja konektywności jawnie odrzuca błędny typ diagnostyki wag."""
    W = np.array([[0.0, 0.2], [0.3, 0.0]], dtype=float)
    x = np.array([0.5, 0.4], dtype=float)
    diagnostics: dict[str, object] = {"weight_updates": []}

    class Params:
        """Minimalny kontrakt parametrów adaptacji konektywności w teście."""

        connectivity_adaptation = ConnectivityAdaptationConfig(
            enabled=True,
            pairs=(("SRC", "DST"),),
            hebbian=HebbianRuleConfig(enabled=True, learning_rate=0.1),
        )

    with pytest.raises(TypeError, match="weight_updates"):
        update_connectivity(
            W=W,
            x=x,
            diagnostics=diagnostics,
            params=Params(),
            idx={"SRC": 0, "DST": 1},
        )
