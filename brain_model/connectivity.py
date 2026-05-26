from brain_core.anatomy.atlases import load_connectome, load_region_atlas, validate_atlas_connectome_consistency


_ATLAS = load_region_atlas()
_CONNECTOME = load_connectome(_ATLAS)
validate_atlas_connectome_consistency(_ATLAS, _CONNECTOME)


def build_connectivity(names):
    """
    W[target, source] opisuje wpływ aktywności regionu source na region target.
    """
    if tuple(names) != _CONNECTOME.region_names:
        raise ValueError("Requested region order does not match loaded connectome")
    return _CONNECTOME.weights.copy()
