from typing import Any

import numpy as np

from brain_core.networks.delays import DelayBuffer, delayed_coupling
from brain_core.networks.structural_network import StructuralNetwork
from brain_core.populations.wilson_cowan import (
    RegionWilsonCowanModel,
    RegionWilsonCowanParams,
)


def test_delayed_coupling_formula() -> Any:
    """Sprawdza wzór sprzężenia z macierzą aktywności opóźnionej."""
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
    """Sprawdza kształty i zakresy stanów po kroku modelu Wilsona-Cowana."""
    regions = ["R1", "R2"]
    params = {r: RegionWilsonCowanParams() for r in regions}
    model = RegionWilsonCowanModel(region_names=regions, params=params)

    e, i = model.step(
        0.001, external_e=np.array([0.5, 0.1]), external_i=np.array([0.2, 0.3])
    )
    assert e.shape == (2,)
    assert i.shape == (2,)
    assert np.all((e >= 0) & (e <= 1))
    assert np.all((i >= 0) & (i <= 1))


def test_region_wilson_cowan_parameter_vectors_are_cached() -> Any:
    """Sprawdza, że wektory parametrów nie są alokowane ponownie przy każdym odczycie."""
    regions = ["R1", "R2"]
    params = {
        "R1": RegionWilsonCowanParams(tau_E=0.02, tau_I=0.01, w_EE=11.0),
        "R2": RegionWilsonCowanParams(tau_E=0.03, tau_I=0.02, w_EE=12.0),
    }
    model = RegionWilsonCowanModel(region_names=regions, params=params)

    parameter_properties = (
        "_tau_E",
        "_tau_I",
        "_w_EE",
        "_w_EI",
        "_w_IE",
        "_w_II",
        "_gain_E",
        "_gain_I",
        "_threshold_E",
        "_threshold_I",
    )
    for property_name in parameter_properties:
        vector = getattr(model, property_name)
        assert vector is getattr(model, property_name)
        assert not vector.flags.writeable

    assert np.allclose(model._tau_E, np.array([0.02, 0.03]))
    assert np.allclose(model._w_EE, np.array([11.0, 12.0]))


def test_structural_network_coupling() -> Any:
    """Sprawdza mnożenie konektomu przez wektor aktywności regionów."""
    net = StructuralNetwork(["A", "B"], np.array([[0.0, 1.0], [0.5, 0.0]]))
    out = net.coupling(np.array([0.2, 0.7]))
    assert np.allclose(out, np.array([0.7, 0.1]))


def test_network_population_synapse_contract_shapes_ranges_and_rng() -> None:
    """Sprawdza kontrakt sieci, populacji i neuromodulacji dla kształtów oraz RNG."""
    regions = ["R1", "R2", "R3"]
    params = {region: RegionWilsonCowanParams() for region in regions}
    neuromodulators = {
        "dopamine": np.array([0.2, 0.3, 0.4]),
        "noradrenaline": np.array([0.1, 0.2, 0.3]),
        "acetylcholine": np.array([0.4, 0.5, 0.6]),
        "serotonin": np.array([0.3, 0.3, 0.3]),
        "gaba": np.array([0.5, 0.4, 0.3]),
        "glutamate": np.array([0.2, 0.3, 0.4]),
        "cortisol": np.array([0.1, 0.1, 0.2]),
        "adrenaline": np.array([0.2, 0.1, 0.2]),
    }
    external_e = np.array([0.2, 0.1, 0.3])
    external_i = np.array([0.1, 0.2, 0.1])

    first_model = RegionWilsonCowanModel(region_names=regions, params=params)
    second_model = RegionWilsonCowanModel(region_names=regions, params=params)
    first_e, first_i = first_model.step(
        0.001,
        external_e=external_e,
        external_i=external_i,
        neuromodulators=neuromodulators,
        rng=np.random.default_rng(123),
    )
    second_e, second_i = second_model.step(
        0.001,
        external_e=external_e,
        external_i=external_i,
        neuromodulators=neuromodulators,
        rng=np.random.default_rng(123),
    )

    neuromodulation_matrix = RegionWilsonCowanModel.neuromodulation_vector(
        neuromodulators
    )
    assert neuromodulation_matrix.shape == (len(regions), 8)
    assert np.all((neuromodulation_matrix >= 0.0) & (neuromodulation_matrix <= 1.0))
    assert first_e.shape == (len(regions),)
    assert first_i.shape == (len(regions),)
    assert np.all((first_e >= 0.0) & (first_e <= 1.0))
    assert np.all((first_i >= 0.0) & (first_i <= 1.0))
    assert np.allclose(first_e, second_e)
    assert np.allclose(first_i, second_i)


def test_delay_buffer_contract_shapes_and_value_ranges() -> None:
    """Sprawdza kontrakt macierzy opóźnień i sprzężenia opóźnionego."""
    connectivity = np.array(
        [
            [0.0, 0.4, -0.2],
            [0.1, 0.0, 0.3],
            [0.2, -0.1, 0.0],
        ]
    )
    delays_steps = np.array([[0, 1, 2], [2, 0, 1], [1, 2, 0]])
    buffer = DelayBuffer(n_regions=3, delays_steps=delays_steps)

    for activity in (
        np.array([0.1, 0.2, 0.3]),
        np.array([0.2, 0.3, 0.4]),
        np.array([0.3, 0.4, 0.5]),
    ):
        buffer.push(activity)

    delayed_matrix = buffer.delayed_activity_matrix()
    coupling = delayed_coupling(connectivity, delayed_matrix)

    assert buffer.delays_steps.shape == connectivity.shape
    assert np.issubdtype(buffer.delays_steps.dtype, np.integer)
    assert np.all(buffer.delays_steps >= 0)
    assert delayed_matrix.shape == connectivity.shape
    assert np.all((delayed_matrix >= 0.0) & (delayed_matrix <= 0.5))
    assert coupling.shape == (3,)
    assert np.all(np.isfinite(coupling))
