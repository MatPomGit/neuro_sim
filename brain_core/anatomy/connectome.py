from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Connectome:
    """
    Klasa reprezentująca connectome (sieć połączeń między regionami mózgu).

    Attributes:
        region_names (tuple[str, ...]): Nazwy regionów.
        weights (np.ndarray): Macierz wag połączeń.
        fiber_lengths (np.ndarray): Macierz długości włókien.
    """
    region_names: tuple[str, ...]
    weights: np.ndarray
    fiber_lengths: np.ndarray
