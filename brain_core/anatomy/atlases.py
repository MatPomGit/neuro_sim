from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .connectome import Connectome
from .regions import BrainRegion, RegionAtlas


DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def load_region_atlas(path: str | Path | None = None) -> RegionAtlas:
    atlas_path = Path(path) if path else DATA_ROOT / "atlases" / "default_regions.csv"
    with atlas_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        regions = tuple(
            BrainRegion(name=row["region"].strip(), tau=float(row["tau"]))
            for row in reader
        )
    if not regions:
        raise ValueError("Atlas region file is empty")
    return RegionAtlas(regions=regions)


def _load_square_matrix(path: Path, expected_names: tuple[str, ...]) -> np.ndarray:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    header = tuple(cell.strip() for cell in rows[0][1:])
    if header != expected_names:
        raise ValueError(f"Matrix header mismatch for {path.name}")

    matrix = np.zeros((len(expected_names), len(expected_names)), dtype=float)
    for i, row in enumerate(rows[1:]):
        row_name = row[0].strip()
        if row_name != expected_names[i]:
            raise ValueError(f"Row order mismatch for {path.name}: expected {expected_names[i]}, got {row_name}")
        matrix[i, :] = np.array([float(v) for v in row[1:]], dtype=float)
    return matrix


def load_connectome(atlas: RegionAtlas, connectome_dir: str | Path | None = None) -> Connectome:
    root = Path(connectome_dir) if connectome_dir else DATA_ROOT / "connectomes"
    region_names = atlas.names
    weights = _load_square_matrix(root / "weights.csv", region_names)
    lengths = _load_square_matrix(root / "fiber_lengths.csv", region_names)
    return Connectome(region_names=region_names, weights=weights, fiber_lengths=lengths)


def validate_atlas_connectome_consistency(atlas: RegionAtlas, connectome: Connectome) -> None:
    region_names = atlas.names
    if connectome.region_names != region_names:
        raise ValueError("Region names in connectome do not match atlas")
    if connectome.weights.shape != (len(region_names), len(region_names)):
        raise ValueError("Connectivity matrix has invalid shape")
    if connectome.fiber_lengths.shape != connectome.weights.shape:
        raise ValueError("Fiber length matrix shape must match connectivity matrix")
    for region in atlas.regions:
        if region.tau <= 0:
            raise ValueError(f"Region {region.name} has non-positive tau")
