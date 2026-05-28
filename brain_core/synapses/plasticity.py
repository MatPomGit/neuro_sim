from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True, slots=True)
class NeuralMassPlasticityConfig:
    """Parametry reguły plastyczności synaptycznej w skali neural-mass."""

    eta: float = 0.01
    decay_lambda: float = 0.001
    homeostatic_rate: float = 0.005
    target_mean_weight: float = 0.2
    min_weight: float = -1.0
    max_weight: float = 1.0
    forgetting_rate: float = 0.001
    consolidation_rate: float = 0.0002


@dataclass(slots=True)
class PlasticityTracker:
    """Rejestruje historię wag i metryk aktualizacji plastyczności."""

    weight_history: list[np.ndarray] = field(default_factory=list)
    metrics_history: list[dict[str, float]] = field(default_factory=list)

    def record(self, weights: np.ndarray, dW_fast: np.ndarray, dW_slow: np.ndarray) -> None:
        """Zapisuje kopię wag oraz normy szybkiej i wolnej aktualizacji."""
        self.weight_history.append(weights.copy())
        self.metrics_history.append(
            {
                "mean_weight": float(np.mean(weights)),
                "std_weight": float(np.std(weights)),
                "fast_update_norm": float(np.linalg.norm(dW_fast)),
                "slow_update_norm": float(np.linalg.norm(dW_slow)),
            }
        )


def update_weights_two_timescales(
    weights: np.ndarray,
    pre_activity: np.ndarray,
    post_activity: np.ndarray,
    neuromod: float,
    dt: float,
    config: NeuralMassPlasticityConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Aktualizuje wagi synaptyczne regułą neural-mass w dwóch skalach czasu.

    dW_ij/dt = eta * pre_j * post_i * neuromod - lambda * W_ij
    """
    if weights.ndim != 2:
        raise ValueError("weights must be a 2D array")
    if len(post_activity) != weights.shape[0] or len(pre_activity) != weights.shape[1]:
        raise ValueError(
            f"Shape mismatch: weights is {weights.shape}, but post_activity has length {len(post_activity)} "
            f"and pre_activity has length {len(pre_activity)}"
        )
    hebbian_drive = np.outer(post_activity, pre_activity)
    dW_fast = config.eta * neuromod * hebbian_drive - config.decay_lambda * weights
    dW_fast -= config.forgetting_rate * weights

    mean_w = float(np.mean(weights))
    homeostatic = config.homeostatic_rate * (config.target_mean_weight - mean_w)
    dW_slow = config.consolidation_rate * dW_fast + homeostatic

    updated = weights + dt * (dW_fast + dW_slow)
    updated = np.clip(updated, config.min_weight, config.max_weight)
    return updated, dW_fast, dW_slow
