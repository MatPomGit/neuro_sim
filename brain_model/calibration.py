"""Kalibracja parametrów modelu poznawczego na podstawie metryk stabilności."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import logging
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np

from .model import CognitiveBrainModel
from .params import BrainParams
from .validation import evaluate_run

logger = logging.getLogger(__name__)

SEARCH_SPACE = {
    "noise": [0.008, 0.012, 0.015, 0.02],
    "gw_threshold": [0.55, 0.60, 0.65],
    "gw_gain": [8.0, 10.0, 12.0],
    "learning_rate_semantic": [0.002, 0.004, 0.006],
    "learning_rate_value": [0.01, 0.02, 0.03],
}


def _sample_params(method: str, trials: int, seed: int) -> list[dict[str, float]]:
    """Wylosuj lub wybierz z siatki kandydackie parametry kalibracji.

    Zwraca listę słowników ``{nazwa_parametru: wartość}``; liczba elementów nie
    przekracza ``trials``. ``seed`` kontroluje kolejność siatki i losowanie.
    """
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


def run_sweep(
    scenario: str,
    trials: int,
    method: str,
    time_horizon: float,
    seed: int,
    output_dir: str,
) -> list[dict[str, object]]:
    """Uruchom serię symulacji kalibracyjnych i oceń każdą konfigurację.

    Parameters
    ----------
    scenario:
        Identyfikator scenariusza bodźców używany w każdej symulacji.
    trials:
        Maksymalna liczba kandydackich konfiguracji do sprawdzenia.
    method:
        Strategia próbkowania: ``"grid"`` miesza siatkę wartości, a
        ``"random"`` losuje wartości z tej samej przestrzeni.
    time_horizon:
        Czas każdej symulacji w sekundach.
    seed:
        Ziarno bazowe kontrolujące próbkowanie parametrów i ziarna uruchomień.
    output_dir:
        Katalog na pliki JSONL i CSV z wynikami.

    Returns:
    -------
    list[dict[str, object]]
        Lista rekordów prób. Każdy rekord zawiera numer próby, scenariusz,
        metodę, ziarno uruchomienia, parametry, status ``pass``, reguły i
        metryki walidacyjne.

    Raises:
    ------
    ValueError
        Może zostać propagowany z konfiguracji modelu, walidacji scenariusza lub
        oceny uruchomienia.
    OSError
        Gdy nie można utworzyć katalogu wyników albo zapisać plików.

    Notes:
    -----
    Funkcja jest deterministyczna dla tego samego ``seed`` i tej samej wersji
    kodu; nie modyfikuje danych wejściowych poza zapisem artefaktów kalibracji.
    """
    params_candidates = _sample_params(method=method, trials=trials, seed=seed)
    base_rng = np.random.default_rng(seed)

    results: list[dict[str, object]] = []
    for i, param_set in enumerate(params_candidates):
        run_seed = int(base_rng.integers(0, 2**31 - 1))
        params = replace(
            BrainParams(),
            noise=param_set["noise"],
            gw_threshold=param_set["gw_threshold"],
            gw_gain=param_set["gw_gain"],
            learning_rate_semantic=param_set["learning_rate_semantic"],
            learning_rate_value=param_set["learning_rate_value"],
        )

        model = CognitiveBrainModel(params=params, stimulus=scenario, seed=run_seed)
        time, activity, diagnostics, oscillations, behavior = model.simulate(
            T=time_horizon
        )
        evaluation = evaluate_run(
            time,
            activity,
            diagnostics,
            oscillations,
            scenario=scenario,
            behavior=behavior,
        )

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


def save_results(
    results: list[dict[str, object]], output_dir: str, scenario: str, method: str
) -> None:
    """Zapisz wyniki kalibracji do plików JSONL i CSV.

    Parameters
    ----------
    results:
        Rekordy zwrócone przez ``run_sweep``. Każdy rekord musi zawierać
        parametry, reguły i zagnieżdżone metryki stabilności, pasm oraz funkcji.
    output_dir:
        Katalog docelowy tworzony w razie potrzeby.
    scenario:
        Identyfikator scenariusza używany w nazwie plików wynikowych.
    method:
        Nazwa metody próbkowania używana w nazwie plików wynikowych.

    Returns:
    -------
    None
        Funkcja zapisuje ``calibration_<scenario>_<method>.jsonl`` z pełnymi
        rekordami oraz ``.csv`` z płaskimi kolumnami metryk.

    Raises:
    ------
    KeyError
        Gdy rekord wynikowy nie zawiera oczekiwanych pól.
    OSError
        Gdy zapis JSONL lub CSV nie powiedzie się.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    jsonl_path = output / f"calibration_{scenario}_{method}.jsonl"
    csv_path = output / f"calibration_{scenario}_{method}.csv"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "trial",
        "scenario",
        "method",
        "seed",
        "pass",
        "noise",
        "gw_threshold",
        "gw_gain",
        "learning_rate_semantic",
        "learning_rate_value",
        "trajectory_stable",
        "bands_match",
        "threat_response",
        "reward_response",
        "saturation_fraction",
        "saturation_run_length_max",
        "band_match_score",
        "threat_sal_gain",
        "threat_int_gain",
        "reward_val_gain",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            metrics = cast(dict[str, dict[str, object]], row["metrics"])
            params = cast(dict[str, object], row["params"])
            rules = cast(dict[str, object], row["rules"])
            writer.writerow(
                {
                    "trial": row["trial"],
                    "scenario": row["scenario"],
                    "method": row["method"],
                    "seed": row["seed"],
                    "pass": row["pass"],
                    **params,
                    **rules,
                    "saturation_fraction": metrics["stability"]["saturation_fraction"],
                    "saturation_run_length_max": metrics["stability"][
                        "saturation_run_length_max"
                    ],
                    "band_match_score": metrics["band_alignment"]["band_match_score"],
                    "threat_sal_gain": metrics["functional"]["threat_sal_gain"],
                    "threat_int_gain": metrics["functional"]["threat_int_gain"],
                    "reward_val_gain": metrics["functional"]["reward_val_gain"],
                }
            )


def build_parser() -> argparse.ArgumentParser:
    """Zbuduj parser CLI dla sweepu kalibracyjnego.

    Zwraca ``argparse.ArgumentParser`` z polskimi opisami opcji scenariusza,
    liczby prób, metody, czasu symulacji w sekundach, ziarna i katalogu wyników.
    """
    parser = argparse.ArgumentParser(
        description="Parametryczny sweep kalibracyjny modelu."
    )
    parser.add_argument(
        "--scenario", default="threat-response", help="Scenariusz bodźca"
    )
    parser.add_argument("--trials", type=int, default=100, help="Liczba prób")
    parser.add_argument(
        "--method",
        choices=["grid", "random"],
        default="random",
        help="Strategia sweepu",
    )
    parser.add_argument("--time", type=float, default=45.0, help="Czas symulacji [s]")
    parser.add_argument("--seed", type=int, default=123, help="Seed bazowy")
    parser.add_argument("--output", default="outputs", help="Folder wyników CSV/JSONL")
    return parser


def main() -> None:
    """Uruchom kalibrację z argumentów CLI i zaloguj podsumowanie.

    Funkcja nie zwraca wartości; propaguje błędy parsowania, symulacji i zapisu,
    aby nie ukrywać nieudanych eksperymentów.
    """
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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logger.info(
        "Ukończono %s prób dla scenariusza='%s'. Poprawne: %s/%s",
        len(results),
        args.scenario,
        passed,
        len(results),
    )


if __name__ == "__main__":
    main()
