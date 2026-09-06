"""Zarządzanie deterministycznymi źródłami losowości dla komponentów symulacji."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class RandomSources:
    """
    Zarządzanie strumieniami losowymi dla deterministyczności.

    Każdy moduł powinien pobierać swój generator po nazwie, żeby unikać
    przypadkowego współdzielenia stanu RNG między komponentami.

    Atrybuty:
        seed (int): Ziarno globalne.
        _root (np.random.SeedSequence): Bazowa sekwencja seedów.
        _streams (dict[str, np.random.Generator]): Słownik generatorów.
    """

    seed: int
    _root: np.random.SeedSequence = field(init=False)
    _streams: dict[str, np.random.Generator] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """
        Inicjalizuje sekwencję bazową na podstawie globalnego seeda.
        """
        self._root = np.random.SeedSequence(self.seed)

    def get(self, name: str) -> np.random.Generator:
        """
        Zwraca (lub tworzy) generator losowy przypisany do nazwy modułu.

        Args:
            name (str): Nazwa modułu.

        Returns:
            np.random.Generator: Generator losowy.

        Raises:
            ValueError: Jeśli nazwa komponentu jest pusta.
        """
        if not name:
            raise ValueError("Nazwa komponentu RNG nie może być pusta.")
        if name not in self._streams:
            child = self._root.spawn(1)[0]
            self._streams[name] = np.random.default_rng(child)
        return self._streams[name]

    def fork(self, name: str) -> np.random.Generator:
        """
        Tworzy nowy niezależny strumień i podmienia pod wskazaną nazwą.

        Args:
            name (str): Nazwa modułu.

        Returns:
            np.random.Generator: Nowy generator losowy.

        Raises:
            ValueError: Jeśli nazwa komponentu jest pusta.
        """
        if not name:
            raise ValueError("Nazwa komponentu RNG nie może być pusta.")
        child = self._root.spawn(1)[0]
        self._streams[name] = np.random.default_rng(child)
        return self._streams[name]

    def component_names(self) -> list[str]:
        """Zwróć nazwy komponentów, które pobrały strumień RNG.

        Returns:
            list[str]: Posortowane nazwy komponentów korzystających z RNG.
        """
        return sorted(self._streams)

    def _metadata_component_names(self) -> list[str]:
        """Zwróć stabilne publiczne identyfikatory komponentów RNG.

        Regionalny backbone zastępuje historyczne wykonanie modelu poznawczego
        i banku oscylatorów, ale format artefaktów ``randomness`` pozostaje
        wstecznie zgodny. Mapowanie dotyczy wyłącznie etykiet metadanych; stan
        generatora jest nadal przechowywany pod nazwą ``regional_wilson_cowan``.
        """
        names = set(self.component_names())
        if "regional_wilson_cowan" in names:
            names.remove("regional_wilson_cowan")
            names.update({"cognitive_brain_model", "wilson_cowan_oscillator_bank"})
        return sorted(names)

    def metadata(self) -> dict[str, object]:
        """Zbuduj metadane losowości zapisywane w artefaktach wyniku.

        Returns:
            dict[str, object]: Ziarno, komponenty RNG i flaga deterministyczności.
        """
        return {
            "rng_seed": self.seed,
            "rng_components": self._metadata_component_names(),
            "deterministic_generator": True,
            "generator": "numpy.random.Generator",
            "bit_generator": "PCG64",
        }
