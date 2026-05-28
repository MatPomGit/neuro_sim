"""Loader benchmarków referencyjnych z walidacją spójności."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class BenchmarkValidationError(ValueError):
    pass
    """Wyjątek zgłaszany przy błędach walidacji benchmarków referencyjnych."""


def _load_csv_matrix(path: Path) -> np.ndarray:
    if not path.exists():
        raise BenchmarkValidationError(f"Plik benchmarku nie istnieje: {path}")
    data = np.genfromtxt(path, delimiter=",", names=True)
    if data.size == 0:
        raise BenchmarkValidationError(f"Pusty plik benchmarku: {path}")
    if data.dtype.names is None:
        raise BenchmarkValidationError(f"Brak nagłówków kolumn w pliku: {path}")
    cols = [name for name in data.dtype.names if name not in {"time", "trial"}]
    if not cols:
        raise BenchmarkValidationError(f"Brak kolumn metryk w pliku: {path}")
    matrix = np.column_stack([np.asarray(data[name], dtype=float) for name in cols])
    if matrix.ndim != 2:
        raise BenchmarkValidationError(f"Niepoprawny kształt danych: {path}")
    return matrix
    """
    Ładuje macierz danych z pliku CSV i waliduje jej strukturę.

    Args:
        path (Path): Ścieżka do pliku CSV.

    Returns:
        np.ndarray: Macierz danych z pliku.

    Raises:
        BenchmarkValidationError: Jeśli plik nie istnieje, jest pusty lub ma niepoprawną strukturę.
    """


import functools


@functools.lru_cache(maxsize=4)
def load_reference_benchmarks(base_dir: str | Path = "data/validation") -> dict[str, np.ndarray]:
    root = Path(base_dir)
    eeg = _load_csv_matrix(root / "eeg_target.csv")
    fmri = _load_csv_matrix(root / "fmri_target.csv")
    behavior = _load_csv_matrix(root / "behavior_target.csv")

    if eeg.shape[0] < 2 or fmri.shape[0] < 2 or behavior.shape[0] < 2:
        raise BenchmarkValidationError("Benchmarki muszą mieć co najmniej 2 wiersze.")

    return {"eeg": eeg, "fmri": fmri, "behavior": behavior}
    """
    Ładuje benchmarki referencyjne EEG, fMRI i zachowania z plików CSV.

    Args:
        base_dir (str | Path): Katalog bazowy z plikami benchmarków.

    Returns:
        dict[str, np.ndarray]: Słownik z macierzami benchmarków.

    Raises:
        BenchmarkValidationError: Jeśli benchmarki są niepoprawne lub niekompletne.
    """
