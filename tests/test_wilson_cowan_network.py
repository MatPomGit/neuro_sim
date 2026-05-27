import numpy as np

from brain_core.networks.delays import DelayBuffer, delayed_coupling
from brain_core.networks.structural_network import StructuralNetwork
from brain_core.populations.wilson_cowan import RegionWilsonCowanModel, RegionWilsonCowanParams
from typing import Any


def test_delayed_coupling_formula() -> Any:
    """Opis funkcji test_delayed_coupling_formula."""
    conn = np.array([[0.0, 0.5], [0.3, 0.0]])
    delays = np.array([[0, 1], [2, 0]])
    buffer = DelayBuffer(n_regions=2, delays_steps=delays)

    buffer.push(np.array([0.1, 0.2]))
    buffer.push(np.array([0.2, 0.4]))
    buffer.push(np.array([0.3, 0.6]))

    delayed = buffer.delayed_activity_matrix()
    coupling = delayed_coupling(conn, delayed)
    assert np.allclose(coupling, np.array([0.2, 0.03]))


def test_region_wilson_cowan_step_shapes() -> Any:
    """Opis funkcji test_region_wilson_cowan_step_shapes."""
    regions = ["R1", "R2"]
    params = {r: RegionWilsonCowanParams() for r in regions}
    model = RegionWilsonCowanModel(region_names=regions, params=params)

    e, i = model.step(0.001, external_e=np.array([0.5, 0.1]), external_i=np.array([0.2, 0.3]))
    assert e.shape == (2,)
    assert i.shape == (2,)
    assert np.all((e >= 0) & (e <= 1))
    assert np.all((i >= 0) & (i <= 1))


def test_structural_network_coupling() -> Any:
    """Opis funkcji test_structural_network_coupling."""
    net = StructuralNetwork(["A", "B"], np.array([[0.0, 1.0], [0.5, 0.0]]))
    out = net.coupling(np.array([0.2, 0.7]))
    assert np.allclose(out, np.array([0.7, 0.1]))
