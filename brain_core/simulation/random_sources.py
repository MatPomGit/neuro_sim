from __future__ import annotations

"""Zarządzanie deterministycznymi źródłami losowości dla komponentów symulacji."""

from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class RandomSources:
    """Zarządzanie strumieniami losowymi dla deterministyczności.

    Każdy moduł powinien pobierać swój generator po nazwie, żeby unikać
    przypadkowego współdzielenia stanu RNG między komponentami.
    """

    seed: int
    _root: np.random.SeedSequence = field(init=False)
    _streams: dict[str, np.random.Generator] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Inicjalizuje sekwencję bazową na podstawie globalnego seeda."""
        self._root = np.random.SeedSequence(self.seed)

    def get(self, name: str) -> np.random.Generator:
        """Zwraca (lub tworzy) generator losowy przypisany do nazwy modułu."""
        if name not in self._streams:
            child = self._root.spawn(1)[0]
            self._streams[name] = np.random.default_rng(child)
        return self._streams[name]

    def fork(self, name: str) -> np.random.Generator:
        """Tworzy nowy niezależny strumień i podmienia pod wskazaną nazwą."""
        child = self._root.spawn(1)[0]
        self._streams[name] = np.random.default_rng(child)
        return self._streams[name]
