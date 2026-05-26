from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrainRegion:
    name: str
    tau: float


@dataclass(frozen=True)
class RegionAtlas:
    regions: tuple[BrainRegion, ...]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(region.name for region in self.regions)

    @property
    def tau_vector(self):
        return [region.tau for region in self.regions]
