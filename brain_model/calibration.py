from __future__ import annotations

import argparse
import csv
import itertools
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from .model import CognitiveBrainModel
from .params import BrainParams
from .validation import evaluate_run


SEARCH_SPACE = {
    "noise": [0.008, 0.012, 0.015, 0.02],
    "gw_threshold": [0.55, 0.60, 0.65],
    "gw_gain": [8.0, 10.0, 12.0],
    "learning_rate_semantic": [0.002, 0.004, 0.006],
    "learning_rate_value": [0.01, 0.02, 0.03],
}


def _sample_params(method: str, trials: int, seed: int) -> list[dict[str, float]]:
    """Opis funkcji _sample_params."""
    rng = np.random.default_rng(seed)
    keys = list(SEARCH_SPACE)
    if method == "grid":
        combos = list(itertools.product(*(SEARCH_SPACE[k] for k in keys)))
        rng.shuffle(combos)
        sampled = []
        for combo in combos[:trials]:
            sampled.append({k: v for k, v in zip(keys, combo)})
        return sampled

    sampled = []
    for _ in range(trials):
        sampled.append({k: float(rng.choice(SEARCH_SPACE[k])) for k in keys})
    return sampled


def run_sweep(scenario: str, trials: int, method: str, time_horizon: float, seed: int, output_dir: str) -> list[dict[str, Any]]:
    """Opis funkcji run_sweep."""
    params_candidates = _sample_params(method=method, trials=trials, seed=seed)
    base_rng = np.random.default_rng(seed)

    results: list[dict[str, Any]] = []
    for i, param_set in enumerate(params_candidates):
        run_seed = int(base_rng.integers(0, 2**31 - 1))
        params = replace(BrainParams(), **param_set)

        model = CognitiveBrainModel(params=params, stimulus=scenario, seed=run_seed)
        time, activity, diagnostics, oscillations = model.simulate(T=time_horizon)
        evaluation = evaluate_run(time, activity, diagnostics, oscillations, scenario=scenario)

        row = {
            "trial": i,
            "scenario": scenario,
            "method": method,
            "seed": run_seed,
            "params": param_set,
            "pass": evaluation["pass"],
            "rules": evaluation["rules"],
            "metrics": evaluation["metrics"],
        }
        results.append(row)

    save_results(results, output_dir=output_dir, scenario=scenario, method=method)
    return results


def save_results(results: list[dict[str, Any]], output_dir: str, scenario: str, method: str) -> None:
    """Opis funkcji save_results."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    jsonl_path = output / f"calibration_{scenario}_{method}.jsonl"
    csv_path = output / f"calibration_{scenario}_{method}.csv"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "trial", "scenario", "method", "seed", "pass",
        "noise", "gw_threshold", "gw_gain", "learning_rate_semantic", "learning_rate_value",
        "trajectory_stable", "bands_match", "threat_response", "reward_response",
        "saturation_fraction", "saturation_run_length_max", "band_match_score",
        "threat_sal_gain", "threat_int_gain", "reward_val_gain",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            metrics = row["metrics"]
            writer.writerow({
                "trial": row["trial"],
                "scenario": row["scenario"],
                "method": row["method"],
                "seed": row["seed"],
                "pass": row["pass"],
                **row["params"],
                **row["rules"],
                "saturation_fraction": metrics["stability"]["saturation_fraction"],
                "saturation_run_length_max": metrics["stability"]["saturation_run_length_max"],
                "band_match_score": metrics["band_alignment"]["band_match_score"],
                "threat_sal_gain": metrics["functional"]["threat_sal_gain"],
                "threat_int_gain": metrics["functional"]["threat_int_gain"],
                "reward_val_gain": metrics["functional"]["reward_val_gain"],
            })


def build_parser() -> argparse.ArgumentParser:
    """Opis funkcji build_parser."""
    parser = argparse.ArgumentParser(description="Parametryczny sweep kalibracyjny modelu.")
    parser.add_argument("--scenario", default="threat-response", help="Scenariusz bodźca")
    parser.add_argument("--trials", type=int, default=100, help="Liczba prób")
    parser.add_argument("--method", choices=["grid", "random"], default="random", help="Strategia sweepu")
    parser.add_argument("--time", type=float, default=45.0, help="Czas symulacji [s]")
    parser.add_argument("--seed", type=int, default=123, help="Seed bazowy")
    parser.add_argument("--output", default="outputs", help="Folder wyników CSV/JSONL")
    return parser


def main() -> None:
    """Opis funkcji main."""
    args = build_parser().parse_args()
    results = run_sweep(
        scenario=args.scenario,
        trials=args.trials,
        method=args.method,
        time_horizon=args.time,
        seed=args.seed,
        output_dir=args.output,
    )
    passed = sum(1 for r in results if r["pass"])
    print(f"Completed {len(results)} trials for scenario='{args.scenario}'. Pass: {passed}/{len(results)}")


if __name__ == "__main__":
    main()
