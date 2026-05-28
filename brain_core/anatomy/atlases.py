from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .connectome import Connectome
from .regions import BrainRegion, RegionAtlas


DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def load_region_atlas(path: str | Path | None = None) -> RegionAtlas:
    """
    Ładuje atlas regionów mózgu z pliku CSV.

    Args:
        path (str | Path | None): Ścieżka do pliku CSV z atlasem.

    Returns:
        RegionAtlas: Obiekt atlasu regionów.

    Raises:
        ValueError: Jeśli plik jest pusty.
    """
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
    """
    Ładuje kwadratową macierz z pliku CSV i sprawdza zgodność nagłówków i wierszy.

    Args:
        path (Path): Ścieżka do pliku CSV.
        expected_names (tuple[str, ...]): Oczekiwane nazwy regionów.

    Returns:
        np.ndarray: Kwadratowa macierz wartości.

    Raises:
        ValueError: Jeśli plik jest pusty lub niezgodny z oczekiwaniami.
    """
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Matrix file {path.name} is empty")

    header = tuple(cell.strip() for cell in rows[0][1:])
    if header != expected_names:
        raise ValueError(f"Matrix header mismatch for {path.name}")

    if len(rows) - 1 != len(expected_names):
        raise ValueError(f"Matrix row count mismatch for {path.name}: expected {len(expected_names)}, got {len(rows) - 1}")

    matrix = np.zeros((len(expected_names), len(expected_names)), dtype=float)
    for i, row in enumerate(rows[1:]):
        row_name = row[0].strip()
        if row_name != expected_names[i]:
            raise ValueError(f"Row order mismatch for {path.name}: expected {expected_names[i]}, got {row_name}")
        matrix[i, :] = np.array([float(v) for v in row[1:]], dtype=float)
    return matrix


def load_connectome(atlas: RegionAtlas, connectome_dir: str | Path | None = None) -> Connectome:
    """
    Ładuje connectome na podstawie atlasu regionów i katalogu z plikami CSV.

    Args:
        atlas (RegionAtlas): Atlas regionów.
        connectome_dir (str | Path | None): Katalog z plikami connectome.

    Returns:
        Connectome: Obiekt connectome z wagami i długościami włókien.
    """
    root = Path(connectome_dir) if connectome_dir else DATA_ROOT / "connectomes"
    region_names = atlas.names
    weights = _load_square_matrix(root / "weights.csv", region_names)
    lengths = _load_square_matrix(root / "fiber_lengths.csv", region_names)
    return Connectome(region_names=region_names, weights=weights, fiber_lengths=lengths)


def validate_atlas_connectome_consistency(atlas: RegionAtlas, connectome: Connectome) -> None:
    """
    Waliduje spójność atlasu regionów i connectome.

    Args:
        atlas (RegionAtlas): Atlas regionów.
        connectome (Connectome): Obiekt connectome.

    Raises:
        ValueError: Jeśli występuje niezgodność nazw, kształtów lub wartości.
    """
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
