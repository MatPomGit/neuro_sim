"""Regional Wilson-Cowan backbone driven by atlas and structural connectome."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

from brain_core.anatomy.atlases import DATA_ROOT, load_connectome, load_region_atlas
from brain_core.cognition.mapping import mapping_for_task
from brain_core.experiments.protocols import TrialStimulus
from brain_core.networks.delays import DelayBuffer, delayed_coupling
from brain_core.populations.wilson_cowan import (
    RegionWilsonCowanModel,
    RegionWilsonCowanParams,
)

from .config_schema import ExperimentConfig
from .random_sources import RandomSources
from .timebase import compute_step_count


@dataclass(slots=True)
class RegionalSimulationResult:
    """Signals produced by the regional Wilson-Cowan backbone."""

    region_names: list[str]
    time: np.ndarray
    excitatory: np.ndarray
    inhibitory: np.ndarray
    activity: np.ndarray
    behavior: dict[str, np.ndarray]
    oscillations: dict[str, Any]
    diagnostics: dict[str, Any]
    delay_steps: np.ndarray
    connectivity: np.ndarray

    @property
    def names(self) -> list[str]:
        """Expose region names under the historical model attribute."""
        return list(self.region_names)


def _atlas_path(atlas_name: str) -> Path:
    """Resolve an atlas identifier to the repository CSV path."""
    candidate = Path(atlas_name)
    if candidate.suffix:
        return candidate
    return DATA_ROOT / "atlases" / f"{atlas_name}.csv"


def _connectome_dir(config: ExperimentConfig) -> Path | None:
    """Return a common connectome directory when configured files share one."""
    weights = config.connectome.get("weights")
    lengths = config.connectome.get("fiber_lengths")
    if not weights or not lengths:
        return None
    weights_path = Path(str(weights))
    lengths_path = Path(str(lengths))
    if weights_path.parent != lengths_path.parent:
        raise ValueError(
            "connectome.weights i connectome.fiber_lengths muszą znajdować się "
            "w tym samym katalogu dla regionalnego runtime"
        )
    return weights_path.parent


def _delay_steps(
    fiber_lengths_mm: np.ndarray,
    timestep_s: float,
    conduction_speed_m_s: float,
) -> np.ndarray:
    """Convert tract lengths in millimetres to integer propagation delays."""
    if conduction_speed_m_s <= 0.0:
        raise ValueError("connectome.conduction_speed_m_s musi być > 0")
    delay_s = (np.asarray(fiber_lengths_mm, dtype=float) / 1000.0) / float(
        conduction_speed_m_s
    )
    return np.rint(delay_s / float(timestep_s)).astype(int)


def _regional_params(
    config: ExperimentConfig,
    region_names: Sequence[str],
    atlas_tau: Sequence[float],
) -> dict[str, RegionWilsonCowanParams]:
    """Build per-region Wilson-Cowan parameters from atlas and config overrides."""
    raw = config.integrator.get("regional_wilson_cowan", {})
    allowed = {
        "tau_E",
        "tau_I",
        "w_EE",
        "w_EI",
        "w_IE",
        "w_II",
        "gain_E",
        "gain_I",
        "threshold_E",
        "threshold_I",
    }
    shared = {key: float(value) for key, value in raw.items() if key in allowed}
    params: dict[str, RegionWilsonCowanParams] = {}
    for name, tau in zip(region_names, atlas_tau, strict=True):
        values = dict(shared)
        values.setdefault("tau_E", float(tau))
        values.setdefault("tau_I", max(float(config.timestep), float(tau) * 0.5))
        params[name] = RegionWilsonCowanParams(**values)
    return params


def _stimulus_vector(
    region_names: Sequence[str], stimulus: TrialStimulus | None
) -> np.ndarray:
    """Map an active trial's regional input onto atlas ordering."""
    if stimulus is None:
        return np.zeros(len(region_names), dtype=float)
    return np.asarray(
        [float(stimulus.regional_input.get(name, 0.0)) for name in region_names],
        dtype=float,
    )


def _active_stimulus(
    stimuli: Sequence[TrialStimulus], time_s: float
) -> TrialStimulus | None:
    """Return the stimulus active at ``time_s`` if one exists."""
    for stimulus in stimuli:
        onset = float(stimulus.onset_s)
        if onset <= time_s < onset + float(stimulus.duration_s):
            return stimulus
    return None


def _decision_signal(
    task_name: str,
    region_names: Sequence[str],
    excitatory: np.ndarray,
) -> np.ndarray:
    """Derive a bounded task-specific decision variable from regional state."""
    index = {name: idx for idx, name in enumerate(region_names)}
    mapping = mapping_for_task(task_name)
    readout_regions: list[str] = []
    for module_name in mapping.module_names:
        if module_name in index and module_name not in readout_regions:
            readout_regions.append(module_name)

    if not readout_regions:
        readout_regions = [name for name in ("EXEC", "ATT", "SAL", "MOT") if name in index]
    if not readout_regions:
        readout_regions = [region_names[0]]

    score = np.mean(
        np.column_stack([excitatory[:, index[name]] for name in readout_regions]),
        axis=1,
    )
    baseline = float(np.median(score[: max(1, min(20, score.size))]))
    return np.clip((score - baseline) * 5.0, 0.0, 1.0)


def run_regional_wilson_cowan(
    config: ExperimentConfig,
    stimuli: Sequence[TrialStimulus],
    random_sources: RandomSources,
    progress_callback: Callable[[float], None] | None = None,
) -> RegionalSimulationResult:
    """Run the atlas/connectome regional Wilson-Cowan network.

    Structural weights contribute to the excitatory drive after propagation
    delays derived from tract length and configured conduction speed. The same
    trial sequence used by the experiment scheduler supplies regional external
    input, so neural activity, behavioral readout and reports share one stimulus
    timeline. A small configurable intrinsic drive noise makes ``rng_seed`` a
    genuine stochastic control parameter while preserving exact repeatability
    for a fixed seed.
    """
    atlas_name = str(config.connectome.get("atlas", "default_regions"))
    atlas = load_region_atlas(_atlas_path(atlas_name))
    connectome = load_connectome(atlas, _connectome_dir(config))
    region_names = list(atlas.names)

    conduction_speed = float(config.connectome.get("conduction_speed_m_s", 5.0))
    coupling_gain = float(config.connectome.get("coupling_gain", 0.35))
    regional_options = config.integrator.get("regional_wilson_cowan", {})
    intrinsic_noise_std = float(regional_options.get("noise_std", 0.002))
    if intrinsic_noise_std < 0.0:
        raise ValueError("integrator.regional_wilson_cowan.noise_std musi być >= 0")

    delays = _delay_steps(connectome.fiber_lengths, config.timestep, conduction_speed)
    delay_buffer = DelayBuffer(len(region_names), delays)
    model = RegionWilsonCowanModel(
        region_names,
        _regional_params(config, region_names, atlas.tau_vector),
    )
    rng = random_sources.get("regional_wilson_cowan")

    duration_s = float(config.task.get("duration", 45.0))
    n_steps = compute_step_count(duration_s, config.timestep)
    time = np.arange(n_steps, dtype=float) * float(config.timestep)
    excitatory = np.zeros((n_steps, len(region_names)), dtype=float)
    inhibitory = np.zeros_like(excitatory)

    progress_stride = max(1, n_steps // 100)
    for step, time_s in enumerate(time):
        delayed_matrix = delay_buffer.delayed_activity_matrix()
        network_drive = delayed_coupling(connectome.weights, delayed_matrix)
        task_drive = _stimulus_vector(
            region_names,
            _active_stimulus(stimuli, float(time_s)),
        )
        stochastic_drive = rng.normal(
            0.0,
            intrinsic_noise_std,
            size=len(region_names),
        )
        external_e = task_drive + coupling_gain * network_drive + stochastic_drive
        external_i = np.zeros(len(region_names), dtype=float)
        e_state, i_state = model.step(
            float(config.timestep),
            external_e,
            external_i,
            rng=rng,
        )
        excitatory[step] = e_state
        inhibitory[step] = i_state
        delay_buffer.push(e_state)
        if progress_callback is not None and (
            step % progress_stride == 0 or step == n_steps - 1
        ):
            progress_callback((step + 1) / n_steps)

    activity = excitatory - inhibitory
    task_name = str(config.task.get("name", "stroop"))
    decision_score = _decision_signal(task_name, region_names, excitatory)
    decision_threshold = float(config.model.get("decision_threshold", 0.01))
    decision_event = (decision_score >= decision_threshold).astype(float)

    return RegionalSimulationResult(
        region_names=region_names,
        time=time,
        excitatory=excitatory,
        inhibitory=inhibitory,
        activity=activity,
        behavior={
            "decision_score": decision_score,
            "decision_event": decision_event,
        },
        oscillations={
            "eeg": activity.copy(),
            "excitatory": excitatory,
            "inhibitory": inhibitory,
            "regional_e": excitatory,
            "regional_i": inhibitory,
            "metadata": {
                "backbone": "regional_wilson_cowan",
                "conduction_speed_m_s": conduction_speed,
                "coupling_gain": coupling_gain,
                "intrinsic_noise_std": intrinsic_noise_std,
                "decision_threshold": decision_threshold,
                "decision_readout_modules": list(mapping_for_task(task_name).module_names),
            },
        },
        diagnostics={
            "regional_e": excitatory,
            "regional_i": inhibitory,
            "delay_steps": delays,
            "connectivity": connectome.weights,
        },
        delay_steps=delays,
        connectivity=connectome.weights,
    )
