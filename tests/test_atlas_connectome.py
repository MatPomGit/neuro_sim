import numpy as np
import pytest

from brain_core.anatomy.atlases import (
    load_connectome,
    load_region_atlas,
    validate_atlas_connectome_consistency,
)


def test_load_default_atlas_and_connectome():
    atlas = load_region_atlas()
    connectome = load_connectome(atlas)

    assert len(atlas.regions) == 16
    assert connectome.weights.shape == (16, 16)
    assert np.any(connectome.weights != 0.0)


def test_consistency_validation_rejects_wrong_region_order():
    atlas = load_region_atlas()
    connectome = load_connectome(atlas)

    broken = type(connectome)(
        region_names=tuple(reversed(connectome.region_names)),
        weights=connectome.weights,
        fiber_lengths=connectome.fiber_lengths,
    )

    with pytest.raises(ValueError):
        validate_atlas_connectome_consistency(atlas, broken)
