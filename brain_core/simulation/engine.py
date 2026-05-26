from __future__ import annotations

import time as pytime
from pathlib import Path

from brain_model.io import build_output_dir, save_run
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from .config_schema import ExperimentConfig


def run_experiment(config: ExperimentConfig, progress_callback=None):
    model_params = BrainParams(dt=config.timestep, **config.model)
    osc_params = WilsonCowanParams(**config.integrator.get("oscillator", {}))
    model = CognitiveBrainModel(
        params=model_params,
        oscillator_params=osc_params,
        seed=config.seed,
        stimulus=config.task.get("scenario", "reward-learning"),
    )

    start = pytime.perf_counter()
    time, activity, diagnostics, oscillations, behavior = model.simulate(
        T=float(config.task.get("duration", 45.0)),
        progress_callback=progress_callback,
    )
    elapsed = pytime.perf_counter() - start

    save_info = None
    if config.output.get("save_results", False):
        out_dir = build_output_dir(config.task.get("scenario", "run"), config.output.get("label", "run"))
        save_info = save_run(
            out_dir,
            time,
            activity,
            diagnostics,
            oscillations,
            model_params=model.p,
            oscillator_params=model.oscillator_bank.params,
            scenario=oscillations.get("metadata"),
            seed=config.seed,
            duration_s=elapsed,
        )
    return {
        "model": model,
        "time": time,
        "activity": activity,
        "diagnostics": diagnostics,
        "oscillations": oscillations,
        "behavior": behavior,
        "save_info": save_info,
        "elapsed": elapsed,
    }
