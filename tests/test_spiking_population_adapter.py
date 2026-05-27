import numpy as np

from brain_core.populations.spiking_population import Brian2SpikingPopulationAdapter, NeuralMassToSNNInput


def test_signal_contract_and_shape_validation():
    adapter = Brian2SpikingPopulationAdapter(region_names=["hippocampus", "dlpfc"], dt=0.001)
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


def test_pilot_circuits_only_hippocampus_dlpfc():
    # Zakres pilotażu: 1-2 obwody, tu hipokamp + DLPFC.
    adapter = Brian2SpikingPopulationAdapter(region_names=["hippocampus", "dlpfc"], dt=0.001)
    signal = NeuralMassToSNNInput(
        excitatory_drive_hz=np.array([25.0, 15.0]),
        inhibitory_drive_hz=np.array([7.0, 8.0]),
        sync_dt=0.005,
    )

    out = adapter.step(signal)
    assert out.firing_rate_hz[0] > out.firing_rate_hz[1]
