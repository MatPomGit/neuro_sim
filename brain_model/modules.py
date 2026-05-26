import numpy as np

from brain_core.anatomy.atlases import load_region_atlas

_ATLAS = load_region_atlas()

MODULES = list(_ATLAS.names)
TAU = list(np.asarray(_ATLAS.tau_vector, dtype=float))
