from __future__ import annotations

import time as pytime
from pathlib import Path

from brain_model.io import build_output_dir, save_run
from brain_model.model import CognitiveBrainModel
from brain_model.oscillators import WilsonCowanParams
from brain_model.params import BrainParams

from brain_core.experiments.protocols import ErrorType, TrialResult, get_task

from .config_schema import ExperimentConfig
from .scheduler import SimulationScheduler, TaskStimulusPlayer
from .state import SimulationState


def _deterministic_observed_response(task_name: str, condition: str, trial_id: int, seed: int, expected: str | None = None):
    key = (trial_id + seed) % 7
    if task_name == "stroop":
        if key == 0:
            return None
        if key == 1:
            colors = [c for c in ("red", "green", "blue", "yellow") if c != expected]
            return colors[(trial_id + seed) % len(colors)]
        return expected
    if task_name == "go_nogo":
        if condition == "go":
            return "press" if key != 0 else None
        return "press" if key == 0 else None
    if task_name == "n_back":
        if condition == "target":
            return "match" if key != 0 else None
        return "match" if key == 0 else None
    return None


def _simulate_task_trials(config: ExperimentConfig) -> tuple[list[dict], list[dict]]:
    task_name = str(config.task.get("name", "stroop"))
    task = get_task(task_name, **config.task)
    duration = float(config.task.get("duration", 45.0))
    stimuli = task.generate_stimuli(seed=config.seed, duration_s=duration)

    scheduler = SimulationScheduler(stimuli=[TaskStimulusPlayer(stimuli=stimuli)])
    state = SimulationState()
    for _ in range(int(duration / config.timestep)):
        scheduler.run_step(state, config.timestep)

    trial_results: list[dict] = []
    for stimulus in stimuli:
        observed = _deterministic_observed_response(task.name, stimulus.condition, stimulus.trial_id, config.seed, expected=task.expected_response(stimulus))
        reaction_time = None if observed is None else round(0.25 + ((stimulus.trial_id + config.seed) % 5) * 0.05, 3)
        result: TrialResult = task.score_trial(stimulus, observed, reaction_time)
        trial_results.append(
            {
                "trial_id": result.trial_id,
                "reaction_time_s": result.reaction_time_s,
                "correct": result.correct,
                "error_type": result.error_type.value if isinstance(result.error_type, ErrorType) else str(result.error_type),
                "condition": result.condition,
            }
        )

    return state.metrics.get("trial_events", []), trial_results


def run_experiment(config: ExperimentConfig, progress_callback=None):
    model_params = BrainParams(dt=config.timestep, **config.model)
    osc_params = WilsonCowanParams(**config.integrator.get("oscillator", {}))
    stimulus_scenario = str(config.task.get("scenario", "reward-learning"))
    try:
        model = CognitiveBrainModel(
            params=model_params,
            oscillator_params=osc_params,
            seed=config.seed,
            stimulus=stimulus_scenario,
        )
    except ValueError:
        model = CognitiveBrainModel(
            params=model_params,
            oscillator_params=osc_params,
            seed=config.seed,
            stimulus="reward-learning",
        )

    start = pytime.perf_counter()
    time, activity, diagnostics, oscillations, behavior = model.simulate(
        T=float(config.task.get("duration", 45.0)),
        progress_callback=progress_callback,
    )
    elapsed = pytime.perf_counter() - start

    trial_events, trial_results = _simulate_task_trials(config)

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
        "trial_events": trial_events,
        "trial_results": trial_results,
        "save_info": save_info,
        "elapsed": elapsed,
    }
