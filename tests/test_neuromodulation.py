import numpy as np

from brain_core.experiments.pharmacology import comparison_scenarios
from brain_core.populations.wilson_cowan import RegionWilsonCowanModel, RegionWilsonCowanParams
from brain_core.synapses.state import NeuromodulationState, update_region_state


def test_neuromodulation_state_update_bounds():
    s0 = NeuromodulationState()
    s1 = update_region_state(
        s0,
        reward_prediction_error=0.9,
        prediction_error=0.5,
        threat_signal=0.2,
        satiety_signal=0.8,
        attention_drive=0.7,
        novelty_drive=0.8,
        inhibition_drive=0.3,
        excitation_drive=0.7,
        arousal_signal=0.4,
    )
    for value in (
        s1.dopamine,
        s1.noradrenaline,
        s1.acetylcholine,
        s1.serotonin,
        s1.gaba,
        s1.glutamate,
        s1.cortisol,
        s1.adrenaline,
    ):
        assert 0.0 <= value <= 1.0


def test_pharmacology_scenarios_are_available():
    scenarios = comparison_scenarios()
    assert set(scenarios.keys()) == {"baseline", "high_ach", "high_na", "low_gaba"}


def test_wilson_cowan_accepts_neuromodulation_vector():
    regions = ["R1", "R2"]
    params = {r: RegionWilsonCowanParams() for r in regions}
    model = RegionWilsonCowanModel(region_names=regions, params=params)
    neuromodulators = {
        "dopamine": np.array([0.8, 0.4]),
        "noradrenaline": np.array([0.6, 0.5]),
        "acetylcholine": np.array([0.9, 0.2]),
        "serotonin": np.array([0.3, 0.6]),
        "gaba": np.array([0.4, 0.8]),
        "glutamate": np.array([0.7, 0.3]),
        "cortisol": np.array([0.2, 0.9]),
        "adrenaline": np.array([0.3, 0.7]),
    }
    e, i = model.step(0.001, np.array([0.2, 0.2]), np.array([0.1, 0.1]), neuromodulators=neuromodulators)
    assert e.shape == (2,)
    assert i.shape == (2,)
