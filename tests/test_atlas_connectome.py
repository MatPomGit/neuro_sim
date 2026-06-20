from typing import Any

import numpy as np
import pytest

from brain_core.anatomy.atlases import (
    load_connectome,
    load_region_atlas,
    validate_atlas_connectome_consistency,
)


def test_load_default_atlas_and_connectome() -> None:
    """Testuje poprawne ładowanie domyślnego atlasu i konektomu oraz ich spójność wymiarową."""
    atlas = load_region_atlas()
    connectome = load_connectome(atlas)

    assert len(atlas.regions) == 16
    assert connectome.weights.shape == (16, 16)
    assert np.any(connectome.weights != 0.0)


def test_consistency_validation_rejects_wrong_region_order() -> Any:
    """Sprawdza odrzucenie konektomu z niezgodną kolejnością regionów."""
    atlas = load_region_atlas()
    connectome = load_connectome(atlas)

    broken = type(connectome)(
        region_names=tuple(reversed(connectome.region_names)),
        weights=connectome.weights,
        fiber_lengths=connectome.fiber_lengths,
    )

    with pytest.raises(ValueError):
        validate_atlas_connectome_consistency(atlas, broken)


def test_atlas_connectome_contract_shapes_units_and_ranges() -> None:
    """Sprawdza kontrakt kształtów, jednostek i zakresów atlasu oraz konektomu."""
    atlas = load_region_atlas()
    connectome = load_connectome(atlas)
    n_regions = len(atlas.regions)

    assert atlas.names == connectome.region_names
    assert connectome.weights.shape == (n_regions, n_regions)
    assert connectome.fiber_lengths.shape == (n_regions, n_regions)
    assert np.all(np.isfinite(connectome.weights))
    assert np.all(np.isfinite(connectome.fiber_lengths))
    assert np.all(np.abs(connectome.weights) <= 1.0)
    assert np.all(connectome.fiber_lengths >= 0.0)
    assert np.allclose(np.diag(connectome.weights), 0.0)
    assert np.allclose(np.diag(connectome.fiber_lengths), 0.0)
    assert all(region.tau > 0.0 for region in atlas.regions)

    validate_atlas_connectome_consistency(atlas, connectome)


def test_region_atlas_contract_rejects_empty_regions_with_contract_name() -> None:
    """Pusty atlas ma raportować naruszony kontrakt danych anatomii."""
    from brain_core.anatomy.regions import RegionAtlas
    from brain_core.data_contracts import validate_region_atlas_contract

    with pytest.raises(ValueError, match="Kontrakt A"):
        validate_region_atlas_contract(RegionAtlas(regions=()))


def test_connectome_contract_rejects_wrong_matrix_shape_with_contract_name() -> None:
    """Zły kształt macierzy konektomu ma wskazywać kontrakt A."""
    from brain_core.anatomy.connectome import Connectome
    from brain_core.data_contracts import validate_connectome_contract

    connectome = Connectome(
        region_names=("A", "B"),
        weights=np.zeros((2, 3)),
        fiber_lengths=np.zeros((2, 2)),
    )

    with pytest.raises(ValueError, match="Kontrakt A"):
        validate_connectome_contract(connectome)


def test_connectome_contract_rejects_negative_fiber_lengths_with_contract_name() -> (
    None
):
    """Ujemne długości włókien [mm] są błędem kontraktu konektomu."""
    from brain_core.anatomy.connectome import Connectome
    from brain_core.data_contracts import validate_connectome_contract

    connectome = Connectome(
        region_names=("A", "B"),
        weights=np.zeros((2, 2)),
        fiber_lengths=np.array([[0.0, -1.0], [2.0, 0.0]]),
    )

    with pytest.raises(ValueError, match="Kontrakt A"):
        validate_connectome_contract(connectome)
