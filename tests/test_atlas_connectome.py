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
    """Opis funkcji test_consistency_validation_rejects_wrong_region_order."""
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
