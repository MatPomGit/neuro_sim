from brain_model.model import CognitiveBrainModel
from brain_model.plotting import (
    plot_activity,
    plot_band_power,
    plot_diagnostics,
    plot_eeg_modules,
)


def main():
    model = CognitiveBrainModel()
    time, activity, diagnostics, oscillations = model.simulate(T=45.0)

    plot_activity(time, activity, model.names, model.idx)
    plot_diagnostics(time, diagnostics)
    plot_eeg_modules(time, oscillations, model.names, model.idx)
    plot_band_power(time, oscillations)


if __name__ == "__main__":
    main()
