from typing import Any

import numpy as np

from brain_core.populations.spiking_population import (
    Brian2SpikingPopulationAdapter,
    NeuralMassToSNNInput,
    SNNToNeuralMassOutput,
)
from brain_core.simulation.signal_adapter import (
    CouplingSignalAdapter,
    SNNPopulationMapping,
)


def test_signal_contract_and_shape_validation() -> Any:
    """Opis funkcji test_signal_contract_and_shape_validation."""
    adapter = Brian2SpikingPopulationAdapter(
        region_names=["hippocampus", "dlpfc"], dt=0.001
    )
    signal = NeuralMassToSNNInput(
        excitatory_drive_hz=np.array([18.0, 14.0]),
        inhibitory_drive_hz=np.array([6.0, 5.0]),
        sync_dt=0.01,
    )

    out = adapter.step(signal)

    assert out.firing_rate_hz.shape == (2,)
    assert out.mean_membrane_potential_mv.shape == (2,)
    assert out.sync_dt == 0.01
    assert np.all(out.firing_rate_hz >= 0.0)


def test_pilot_circuits_only_hippocampus_dlpfc() -> Any:
    """Opis funkcji test_pilot_circuits_only_hippocampus_dlpfc."""
    adapter = Brian2SpikingPopulationAdapter(
        region_names=["hippocampus", "dlpfc"], dt=0.001
    )
    signal = NeuralMassToSNNInput(
        excitatory_drive_hz=np.array([25.0, 15.0]),
        inhibitory_drive_hz=np.array([7.0, 8.0]),
        sync_dt=0.005,
    )

    out = adapter.step(signal)
    assert out.firing_rate_hz[0] > out.firing_rate_hz[1]


def test_coupling_adapter_roundtrip_mapping_and_units() -> Any:
    """Opis funkcji test_coupling_adapter_roundtrip_mapping_and_units."""
    mapping = SNNPopulationMapping(
        snn_region_names=("hippocampus",),
        neural_mass_region_names=("hippocampus", "acc", "pcc"),
    )
    adapter = CouplingSignalAdapter(mapping=mapping, sync_dt=0.01)

    nm_to_snn = adapter.rate_to_spike_drive(
        excitatory_rate_hz=np.array([18.0, 6.0, 7.0]),
        inhibitory_rate_hz=np.array([5.0, 2.0, 2.0]),
    )
    assert np.allclose(nm_to_snn.excitatory_drive_hz, np.array([18.0]))
    assert np.allclose(nm_to_snn.inhibitory_drive_hz, np.array([5.0]))
    assert nm_to_snn.sync_dt == 0.01

    regional = adapter.spike_summary_to_regional_activity(
        SNNToNeuralMassOutput(
            firing_rate_hz=np.array([45.0]),
            mean_membrane_potential_mv=np.array([-62.0]),
            sync_dt=0.01,
        ),
        n_regions=3,
    )
    assert np.allclose(regional, np.array([0.45, 0.0, 0.0]))


def test_snn_report_section_compares_baseline_and_local_circuit() -> Any:
    """Raport demo ma zawierać porównanie przebiegu bez SNN i z obwodem lokalnym."""
    from brain_core.simulation.config_loader import load_config
    from brain_core.simulation.engine import run_experiment

    cfg = load_config("configs/snn_hippocampus_demo.yaml")
    cfg.output["save_results"] = False

    result = run_experiment(cfg)
    snn_comparison = result["analysis_report"]["snn_comparison"]

    assert snn_comparison["regions"] == ["HIP"]
    assert snn_comparison["sync_dt_s"] == 0.010
    assert snn_comparison["input_rate_unit"] == "Hz"
    assert snn_comparison["output_activity_unit"] == "fraction"
    assert "HIP" in snn_comparison["region_differences"]
    assert snn_comparison["region_differences"]["HIP"]["max_abs_difference"] >= 0.0
