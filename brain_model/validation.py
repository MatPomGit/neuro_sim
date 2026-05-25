from __future__ import annotations

from typing import Any

import numpy as np

from .modules import MODULES

DEFAULT_RULES = {
    "saturation_fraction_max": 0.08,
    "saturation_run_length_max": 0.18,
    "band_match_min": 0.45,
    "threat_sal_int_gain_min": 0.03,
    "reward_val_gain_min": 0.02,
}


def _window_mean(signal: np.ndarray, from_idx: int, to_idx: int) -> float:
    if to_idx <= from_idx:
        return float(np.mean(signal))
    return float(np.mean(signal[from_idx:to_idx]))


def _find_module_index(module_names: list[str], module: str) -> int | None:
    try:
        return module_names.index(module)
    except ValueError:
        return None


def evaluate_run(time, activity, diagnostics, oscillations, scenario, rules: dict[str, float] | None = None) -> dict[str, Any]:
    """Evaluate one simulation run and return metrics with pass/fail rules."""
    if len(time) == 0:
        raise ValueError("time cannot be empty")

    config = {**DEFAULT_RULES, **(rules or {})}

    steps, modules = activity.shape
    sat_low = activity <= 0.01
    sat_high = activity >= 0.99
    sat_mask = sat_low | sat_high

    saturation_fraction = float(np.mean(sat_mask))
    saturation_per_module = {f"module_{i}": float(np.mean(sat_mask[:, i])) for i in range(modules)}

    run_lengths = []
    for m in range(modules):
        arr = sat_mask[:, m].astype(np.int8)
        if np.any(arr):
            starts = np.where(np.diff(np.concatenate(([0], arr))) == 1)[0]
            ends = np.where(np.diff(np.concatenate((arr, [0]))) == -1)[0] + 1
            run_lengths.extend((ends - starts).tolist())
    saturation_run_length_max = float(max(run_lengths) / steps) if run_lengths else 0.0

    band_power = oscillations.get("band_power", {})
    band_totals = {band: float(np.mean(np.asarray(values))) for band, values in band_power.items()}
    total = sum(max(v, 0.0) for v in band_totals.values())
    band_share = {band: (value / total if total > 1e-12 else 0.0) for band, value in band_totals.items()}

    scenario_id = scenario if isinstance(scenario, str) else scenario.get("scenario_id", "unknown")

    expected = {
        "threat-response": {"theta": 0.35, "alpha": 0.20, "beta": 0.25, "gamma": 0.20},
        "reward-learning": {"theta": 0.25, "alpha": 0.30, "beta": 0.30, "gamma": 0.15},
    }.get(scenario_id)

    if expected:
        match = 1.0 - 0.5 * sum(abs(band_share.get(b, 0.0) - expected[b]) for b in expected)
        band_match_score = float(np.clip(match, 0.0, 1.0))
    else:
        uniform = 1.0 / max(len(band_share), 1)
        band_match_score = float(np.clip(1.0 - 0.5 * sum(abs(v - uniform) for v in band_share.values()), 0.0, 1.0))

    from .modules import MODULES

    module_names = list(MODULES)

    def metric_change(metric_name: str, signal: np.ndarray) -> float:
        cue = np.asarray(diagnostics.get(metric_name, np.zeros_like(time)))
        trigger_idx = int(np.argmax(cue > np.percentile(cue, 70))) if np.any(cue > np.percentile(cue, 70)) else 0
        early = _window_mean(signal, 0, max(1, trigger_idx))
        late = _window_mean(signal, min(steps - 1, trigger_idx + steps // 8), steps)
        return float(late - early)

    sal_idx = _find_module_index(module_names, "SAL")
    int_idx = _find_module_index(module_names, "INT")
    val_idx = _find_module_index(module_names, "VAL")

    threat_signal = np.asarray(diagnostics.get("noradrenaline", np.zeros(steps)))
    reward_signal = np.asarray(diagnostics.get("dopamine_delta", np.zeros(steps)))

    if sal_idx is not None:
        sal_gain = metric_change("noradrenaline", activity[:, sal_idx])
    else:
        sal_gain = 0.0

    if int_idx is not None:
        int_gain = metric_change("noradrenaline", activity[:, int_idx])
    else:
        int_gain = 0.0

    if val_idx is not None:
        val_gain = metric_change("dopamine_delta", activity[:, val_idx])
    else:
        val_gain = 0.0

    threat_strength = float(np.mean(threat_signal))
    reward_strength = float(np.mean(np.abs(reward_signal)))

    functional = {
        "threat_sal_gain": sal_gain,
        "threat_int_gain": int_gain,
        "reward_val_gain": val_gain,
        "threat_signal_mean": threat_strength,
        "reward_signal_mean_abs": reward_strength,
    }

    rules_status = {
        "trajectory_stable": saturation_fraction <= config["saturation_fraction_max"] and saturation_run_length_max <= config["saturation_run_length_max"],
        "bands_match": band_match_score >= config["band_match_min"],
        "threat_response": (sal_gain >= config["threat_sal_int_gain_min"]) and (int_gain >= config["threat_sal_int_gain_min"]),
        "reward_response": val_gain >= config["reward_val_gain_min"],
    }

    return {
        "scenario": scenario_id,
        "metrics": {
            "stability": {
                "saturation_fraction": saturation_fraction,
                "saturation_run_length_max": saturation_run_length_max,
                "saturation_per_module": saturation_per_module,
            },
            "band_alignment": {
                "band_share": band_share,
                "band_match_score": band_match_score,
                "expected_share": expected,
            },
            "functional": functional,
        },
        "rules": rules_status,
        "pass": bool(all(rules_status.values())),
    }
