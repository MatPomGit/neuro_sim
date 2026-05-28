from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrainRegion:
    """
    Klasa reprezentująca pojedynczy region mózgu.

    Attributes:
        name (str): Nazwa regionu.
        tau (float): Stała czasowa regionu.
    """
    name: str
    tau: float


@dataclass(frozen=True)
class RegionAtlas:
    """
    Klasa reprezentująca atlas regionów mózgu.

    Attributes:
        regions (tuple[BrainRegion, ...]): Krotka regionów.
    """
    regions: tuple[BrainRegion, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """
        Zwraca nazwy wszystkich regionów w atlasie.
        Returns:
            tuple[str, ...]: Nazwy regionów.
        """
        return tuple(region.name for region in self.regions)

    @property
    def tau_vector(self) -> tuple[float, ...]:
        """
        Zwraca wektor stałych czasowych regionów.
        Returns:
            tuple[float, ...]: Stałe czasowe regionów.
        """
        return tuple(region.tau for region in self.regions)
