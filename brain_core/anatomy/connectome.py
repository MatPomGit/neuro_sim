from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Connectome:
    region_names: tuple[str, ...]
    weights: np.ndarray
    fiber_lengths: np.ndarray
