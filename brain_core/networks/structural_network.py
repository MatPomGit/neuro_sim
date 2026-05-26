from __future__ import annotations

import numpy as np


class StructuralNetwork:
    """Directed structural connectivity between regions."""

    def __init__(self, region_names: list[str], connectivity: np.ndarray):
        n = len(region_names)
        if connectivity.shape != (n, n):
            raise ValueError("connectivity musi mieć rozmiar [n_regions, n_regions]")
        self.region_names = region_names
        self.connectivity = connectivity.astype(float)

    def coupling(self, delayed_activity: np.ndarray) -> np.ndarray:
        if delayed_activity.shape != (len(self.region_names),):
            raise ValueError("delayed_activity musi mieć rozmiar [n_regions]")
        return self.connectivity @ delayed_activity
