from __future__ import annotations

"""Definicja mutowalnego stanu globalnego używanego przez symulację."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class SimulationState:
    """Centralny obiekt stanu symulacji.

    Przechowuje cały mutowalny stan potrzebny schedulerowi i modułom.
    """

    time: float = 0.0
    step: int = 0
    regions: dict[str, np.ndarray] = field(default_factory=dict)
    connections: dict[str, np.ndarray] = field(default_factory=dict)
    neuromodulators: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def snapshot_metrics(self) -> dict[str, Any]:
        """Zwraca głęboką kopię metryk do logowania i zapisu."""
        import copy

        return copy.deepcopy(self.metrics)

    def advance(self, dt: float) -> None:
        """Przesuwa licznik czasu i indeks kroku symulacji."""
        self.time += dt
        self.step += 1
