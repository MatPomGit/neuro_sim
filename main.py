import argparse
import time as pytime

from brain_model.io import build_output_dir, save_run
from brain_model.model import CognitiveBrainModel
from brain_model.plotting import (
    plot_activity,
    plot_band_power,
    plot_diagnostics,
    plot_eeg_modules,
)
from brain_model.scenarios import list_scenarios
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    """Tworzy i konfiguruje parser argumentów wiersza poleceń dla symulacji."""
    parser = argparse.ArgumentParser(description="Uruchom symulację modelu poznawczego.")
    parser.add_argument("--scenario", default="reward-learning", choices=list_scenarios(), help="Identyfikator scenariusza bodźców")
    parser.add_argument("--time", type=float, default=45.0, help="Czas symulacji [s]")
    parser.add_argument("--seed", type=int, default=7, help="Seed generatora losowego")
    parser.add_argument("--save", action="store_true", help="Zapisz wyniki symulacji do outputs/")
    parser.add_argument("--label", default="run", help="Czytelna etykieta eksperymentu do nazwy katalogu")
    return parser


def main() -> None:
    """Główna funkcja uruchamiająca symulację na podstawie parametrów z CLI."""
    args = build_parser().parse_args()
    model = CognitiveBrainModel(seed=args.seed, stimulus=args.scenario)
    start = pytime.perf_counter()
    time, activity, diagnostics, oscillations = model.simulate(T=args.time)
    elapsed = pytime.perf_counter() - start

    if args.save:
        try:
            out_dir = build_output_dir(args.scenario, args.label)
            saved = save_run(
                out_dir,
                time,
                activity,
                diagnostics,
                oscillations,
                model_params=model.p,
                oscillator_params=model.oscillator_bank.params,
                scenario=oscillations.get("metadata"),
                seed=args.seed,
                duration_s=elapsed,
            )
            print(f"Saved run to: {saved['output_dir']}")
        except Exception as exc:
            print(f"Warning: Failed to save run results: {exc}")

    plot_activity(time, activity, model.names, model.idx)
    plot_diagnostics(time, diagnostics)
    plot_eeg_modules(time, oscillations, model.names, model.idx)
    plot_band_power(time, oscillations)


if __name__ == "__main__":
    main()
