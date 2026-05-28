from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from brain_core.anatomy.atlases import load_connectome, load_region_atlas, validate_atlas_connectome_consistency


_ATLAS = load_region_atlas()
_CONNECTOME = load_connectome(_ATLAS)
validate_atlas_connectome_consistency(_ATLAS, _CONNECTOME)


def build_connectivity(names: Sequence[str]) -> NDArray[np.float64]:
    """
    W[target, source] opisuje wpływ aktywności regionu source na region target.
    """
    if tuple(names) != _CONNECTOME.region_names:
        raise ValueError("Requested region order does not match loaded connectome")
    return _CONNECTOME.weights.copy()
