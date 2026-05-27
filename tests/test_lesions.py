import numpy as np

from brain_core.experiments.lesions import PathologyController, PathologyMutation, pathology_scenarios
from brain_core.simulation.config_schema import validate_config
from brain_core.simulation.state import SimulationState
from typing import Any


def test_region_and_edge_mutations_change_state_signal_and_metrics() -> Any:
    """Opis funkcji test_region_and_edge_mutations_change_state_signal_and_metrics."""
    state = SimulationState(
        regions={"Hippocampus": np.array([1.0, 0.8]), "PFC": np.array([0.2, 0.3])},
        connections={"DLPFC->ACC": np.array([0.9])},
    )
    controller = PathologyController(
        [
            PathologyMutation(kind="lesion", scope="region", target="Hippocampus", magnitude=0.5, stage="pre"),
            PathologyMutation(kind="disconnection", scope="edge", source="DLPFC", target="ACC", magnitude=0.5, stage="runtime"),
            PathologyMutation(kind="noise_increase", scope="region", target="PFC", magnitude=0.2, stage="runtime"),
        ]
    )

    before_hip = state.regions["Hippocampus"].copy()
    before_edge = state.connections["DLPFC->ACC"].copy()
    controller.apply_pre_simulation(state)
    controller.apply_runtime(state)

    assert np.mean(state.regions["Hippocampus"]) < np.mean(before_hip)
    assert np.mean(state.connections["DLPFC->ACC"]) < np.mean(before_edge)
    assert "pathology:lesion:Hippocampus" in state.metrics
    assert "pathology:disconnection:DLPFC->ACC" in state.metrics


def test_ei_imbalance_and_delay_increase_change_dynamics_markers() -> Any:
    """Opis funkcji test_ei_imbalance_and_delay_increase_change_dynamics_markers."""
    state = SimulationState(
        regions={"PFC": np.array([0.1, 0.15])},
        connections={"A->B": np.array([0.8, 1.0])},
    )
    PathologyMutation(kind="ei_imbalance", scope="region", target="PFC", magnitude=0.3).apply(state)
    PathologyMutation(kind="delay_increase", scope="edge", source="A", target="B", magnitude=0.4).apply(state)

    assert state.metrics["ei_shift:PFC"] == 0.3
    assert state.metrics["delay_shift:A->B"] == 0.4
    assert float(np.mean(state.connections["A->B"])) < 0.9


def test_reference_scenarios_and_pathology_config_validation() -> Any:
    """Opis funkcji test_reference_scenarios_and_pathology_config_validation."""
    scenarios = pathology_scenarios()
    assert {"hippocampal_lesion", "dlpfc_weakening", "reduced_gaba"}.issubset(scenarios.keys())

    cfg = validate_config(
        {
            "task": {"duration": 5.0},
            "pathology": {
                "enabled": True,
                "scenario": "hippocampal_lesion",
                "mutations": [{"kind": "lesion", "scope": "region", "target": "Hippocampus", "magnitude": 0.7}],
            },
        }
    )
    assert cfg.pathology["enabled"] is True
    assert cfg.pathology["scenario"] == "hippocampal_lesion"
