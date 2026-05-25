import argparse

from brain_model.model import CognitiveBrainModel
from brain_model.plotting import (
    plot_activity,
    plot_band_power,
    plot_diagnostics,
    plot_eeg_modules,
)
from brain_model.scenarios import list_scenarios


def build_parser():
    parser = argparse.ArgumentParser(description="Uruchom symulację modelu poznawczego.")
    parser.add_argument("--scenario", default="reward-learning", choices=list_scenarios(), help="Identyfikator scenariusza bodźców")
    parser.add_argument("--time", type=float, default=45.0, help="Czas symulacji [s]")
    parser.add_argument("--seed", type=int, default=7, help="Seed generatora losowego")
    return parser


def main():
    args = build_parser().parse_args()
    model = CognitiveBrainModel(seed=args.seed, stimulus=args.scenario)
    time, activity, diagnostics, oscillations = model.simulate(T=args.time)

    plot_activity(time, activity, model.names, model.idx)
    plot_diagnostics(time, diagnostics)
    plot_eeg_modules(time, oscillations, model.names, model.idx)
    plot_band_power(time, oscillations)


if __name__ == "__main__":
    main()
