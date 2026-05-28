from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray


@dataclass
class PlasticityRuleConfig:
    enabled: bool = False
    learning_rate: float = 0.0
    decay: float = 0.0


@dataclass
class HebbianRuleConfig:
    enabled: bool = False
    learning_rate: float = 0.0
    anti_hebbian: bool = False
    clip_update: float = 0.01


@dataclass
class ConnectivityAdaptationConfig:
    enabled: bool = False
    pairs: Sequence[Tuple[str, str]] = ()
    hebbian: HebbianRuleConfig = field(default_factory=HebbianRuleConfig)
    decay: float = 0.0
    l2: float = 0.0
    clip_min: float = -1.0
    clip_max: float = 1.0


def apply_state_learning(
    dx: NDArray[np.float64],
    x: NDArray[np.float64],
    diagnostics: Mapping[str, float],
    params: Any,
    idx: Mapping[str, int],
) -> NDArray[np.float64]:
    # TODO(typing): zastąpić Any docelowym typem konfiguracji modelu, gdy interfejs params zostanie ustabilizowany.
    sem_cfg = params.semantic_rule
    val_cfg = params.value_rule

    if sem_cfg.enabled:
        sem_i = idx["SEM"]
        dx[sem_i] += sem_cfg.learning_rate * x[idx["HIP"]] * diagnostics["gw_ignition"]
        dx[sem_i] -= sem_cfg.decay * x[sem_i]

    if val_cfg.enabled:
        dx[idx["VAL"]] += val_cfg.learning_rate * diagnostics["dopamine_delta"]

    return dx


def update_connectivity(
    W: NDArray[np.float64],
    x: NDArray[np.float64],
    diagnostics: MutableMapping[str, Any],
    params: Any,
    idx: Mapping[str, int],
) -> NDArray[np.float64]:
    # TODO(typing): zastąpić Any docelowym typem konfiguracji modelu, gdy interfejs params zostanie ustabilizowany.
    cfg = params.connectivity_adaptation
    diagnostics.setdefault("weight_updates", {})

    if not cfg.enabled or not cfg.pairs:
        return W

    for src_name, dst_name in cfg.pairs:
        src = idx[src_name]
        dst = idx[dst_name]

        dW = 0.0
        if cfg.hebbian.enabled:
            hebb_sign = -1.0 if cfg.hebbian.anti_hebbian else 1.0
            raw = hebb_sign * cfg.hebbian.learning_rate * x[dst] * x[src]
            dW += float(np.clip(raw, -cfg.hebbian.clip_update, cfg.hebbian.clip_update))

        if cfg.decay > 0.0:
            dW -= cfg.decay * W[dst, src]

        if cfg.l2 > 0.0:
            dW -= cfg.l2 * W[dst, src]

        W[dst, src] = float(np.clip(W[dst, src] + dW, cfg.clip_min, cfg.clip_max))
        diagnostics["weight_updates"][f"{src_name}->{dst_name}"] = {
            "weight": W[dst, src],
            "delta": dW,
        }

    return W


def build_weight_history_series(
    weight_history: List[Dict[str, Dict[str, float]]], series_len: int
) -> Dict[str, Dict[str, NDArray[np.float64]]]:
    if not weight_history:
        return {}

    keys = sorted({k for step in weight_history for k in step.keys()})
    weight_series = {k: np.zeros(series_len) for k in keys}
    delta_series = {k: np.zeros(series_len) for k in keys}

    for i, step in enumerate(weight_history):
        for key in keys:
            if key in step:
                weight_series[key][i] = step[key]["weight"]
                delta_series[key][i] = step[key]["delta"]
            elif i > 0:
                weight_series[key][i] = weight_series[key][i - 1]
                delta_series[key][i] = 0.0

    return {
        "weights": weight_series,
        "deltas": delta_series,
    }
