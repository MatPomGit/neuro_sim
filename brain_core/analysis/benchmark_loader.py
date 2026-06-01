"""Loader benchmarków referencyjnych z walidacją spójności."""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ALLOWED_BENCHMARK_LEVELS = frozenset(
    {"synthetic", "educational", "literature-inspired", "empirical"}
)
BENCHMARK_KEYS = ("eeg", "fmri", "behavior")
METADATA_FILE_NAME = "benchmark_metadata.json"


class BenchmarkValidationError(ValueError):
    """Wyjątek zgłaszany przy błędach walidacji benchmarków referencyjnych."""


@dataclass(frozen=True)
class BenchmarkMetadata:
    """Opis źródła i ograniczeń pojedynczego benchmarku walidacyjnego.

    Parameters
    ----------
    source:
        Jawny opis pochodzenia danych referencyjnych.
    scope:
        Zakres sygnału, zadania lub metryki objęty benchmarkiem.
    limitations:
        Ograniczenia metodologiczne i interpretacyjne benchmarku.
    level:
        Poziom benchmarku: ``synthetic``, ``educational``,
        ``literature-inspired`` albo ``empirical``.
    """

    source: str
    scope: str
    limitations: str
    level: str

    @property
    def comparison_origin_pl(self) -> str:
        """Zwróć polski opis, czy porównanie ma charakter syntetyczny czy empiryczny.

        Returns
        -------
        str
            ``empiryczny`` dla poziomu ``empirical`` oraz ``syntetyczny`` dla
            pozostałych poziomów niewyprowadzonych bezpośrednio z danych
            empirycznych.
        """
        if self.level == "empirical":
            return "empiryczny"
        return "syntetyczny"

    def to_dict(self) -> dict[str, str]:
        """Przekształć metadane benchmarku do słownika serializowalnego do JSON.

        Returns
        -------
        dict[str, str]
            Słownik z polami ``source``, ``scope``, ``limitations``, ``level``
            i ``comparison_origin_pl``.
        """
        return {
            "source": self.source,
            "scope": self.scope,
            "limitations": self.limitations,
            "level": self.level,
            "comparison_origin_pl": self.comparison_origin_pl,
        }


@dataclass(frozen=True)
class ReferenceBenchmarkBundle:
    """Pakiet benchmarków referencyjnych wraz z metadanymi.

    Parameters
    ----------
    data:
        Macierze numeryczne benchmarków indeksowane nazwą modalności.
    metadata:
        Zweryfikowane metadane opisujące źródło, zakres, ograniczenia i poziom
        każdego benchmarku.
    """

    data: dict[str, np.ndarray]
    metadata: dict[str, BenchmarkMetadata]

    def metadata_payload(self) -> dict[str, dict[str, str]]:
        """Zwróć metadane w formie gotowej do zapisania w raporcie.

        Returns
        -------
        dict[str, dict[str, str]]
            Zagnieżdżony słownik metadanych benchmarków.
        """
        return {name: item.to_dict() for name, item in self.metadata.items()}


def _load_csv_matrix(path: Path) -> np.ndarray:
    """
    Ładuje macierz danych z pliku CSV i waliduje jej strukturę.

    Args:
        path (Path): Ścieżka do pliku CSV.

    Returns:
        np.ndarray: Macierz danych z pliku.

    Raises:
        BenchmarkValidationError: Jeśli plik nie istnieje, jest pusty lub ma niepoprawną strukturę.
    """
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


def _validate_text_field(
    benchmark_name: str, metadata: dict[str, object], field_name: str
) -> str:
    """Zweryfikuj wymagane pole tekstowe metadanych benchmarku.

    Parameters
    ----------
    benchmark_name:
        Nazwa benchmarku, dla którego walidowane jest pole.
    metadata:
        Surowe metadane odczytane z pliku JSON.
    field_name:
        Nazwa wymaganego pola tekstowego.

    Returns
    -------
    str
        Oczyszczona wartość tekstowa.

    Raises
    ------
    BenchmarkValidationError
        Gdy pole jest nieobecne, nie jest tekstem albo zawiera pusty tekst.
    """
    value = metadata.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} ma niepoprawne pole metadanych: {field_name}"
        )
    return value.strip()


def _build_metadata(
    benchmark_name: str, metadata: dict[str, object]
) -> BenchmarkMetadata:
    """Zbuduj zwalidowane metadane pojedynczego benchmarku.

    Parameters
    ----------
    benchmark_name:
        Nazwa benchmarku opisywanego przez metadane.
    metadata:
        Surowy słownik metadanych z pliku JSON.

    Returns
    -------
    BenchmarkMetadata
        Zwalidowane metadane benchmarku.

    Raises
    ------
    BenchmarkValidationError
        Gdy poziom lub wymagane pola metadanych są niepoprawne.
    """
    source = _validate_text_field(benchmark_name, metadata, "source")
    scope = _validate_text_field(benchmark_name, metadata, "scope")
    limitations = _validate_text_field(benchmark_name, metadata, "limitations")
    level = _validate_text_field(benchmark_name, metadata, "level")
    if level not in ALLOWED_BENCHMARK_LEVELS:
        allowed = ", ".join(sorted(ALLOWED_BENCHMARK_LEVELS))
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} ma nieobsługiwany poziom {level!r}; "
            f"dozwolone poziomy: {allowed}."
        )
    return BenchmarkMetadata(
        source=source,
        scope=scope,
        limitations=limitations,
        level=level,
    )


@functools.lru_cache(maxsize=4)
def load_reference_benchmark_metadata(
    base_dir: str | Path = "data/validation",
) -> dict[str, BenchmarkMetadata]:
    """Załaduj i zwaliduj metadane benchmarków referencyjnych.

    Parameters
    ----------
    base_dir:
        Katalog bazowy zawierający plik ``benchmark_metadata.json``.

    Returns
    -------
    dict[str, BenchmarkMetadata]
        Metadane indeksowane nazwami ``eeg``, ``fmri`` i ``behavior``.

    Raises
    ------
    BenchmarkValidationError
        Gdy plik metadanych nie istnieje, jest niekompletny albo zawiera
        nieobsługiwany poziom benchmarku.
    """
    path = Path(base_dir) / METADATA_FILE_NAME
    if not path.exists():
        raise BenchmarkValidationError(
            f"Plik metadanych benchmarków nie istnieje: {path}"
        )

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise BenchmarkValidationError(
            f"Plik metadanych benchmarków nie jest poprawnym JSON: {path}"
        ) from error
    if not isinstance(raw, dict):
        raise BenchmarkValidationError("Metadane benchmarków muszą być obiektem JSON.")

    missing = [name for name in BENCHMARK_KEYS if name not in raw]
    if missing:
        raise BenchmarkValidationError(
            "Brak metadanych benchmarków: " + ", ".join(missing)
        )

    metadata: dict[str, BenchmarkMetadata] = {}
    for benchmark_name in BENCHMARK_KEYS:
        raw_item = raw[benchmark_name]
        if not isinstance(raw_item, dict):
            raise BenchmarkValidationError(
                f"Metadane benchmarku {benchmark_name} muszą być obiektem JSON."
            )
        metadata[benchmark_name] = _build_metadata(benchmark_name, raw_item)
    return metadata


@functools.lru_cache(maxsize=4)
def load_reference_benchmark_bundle(
    base_dir: str | Path = "data/validation",
) -> ReferenceBenchmarkBundle:
    """Załaduj benchmarki referencyjne razem z metadanymi.

    Parameters
    ----------
    base_dir:
        Katalog bazowy z plikami CSV i plikiem metadanych benchmarków.

    Returns
    -------
    ReferenceBenchmarkBundle
        Pakiet macierzy benchmarków i zwalidowanych metadanych.

    Raises
    ------
    BenchmarkValidationError
        Gdy dane lub metadane benchmarków są niepoprawne.
    """
    data = load_reference_benchmarks(base_dir)
    metadata = load_reference_benchmark_metadata(base_dir)
    return ReferenceBenchmarkBundle(data=data, metadata=metadata)


@functools.lru_cache(maxsize=4)
def load_reference_benchmarks(
    base_dir: str | Path = "data/validation",
) -> dict[str, np.ndarray]:
    """
    Ładuje benchmarki referencyjne EEG, fMRI i zachowania z plików CSV.

    Args:
        base_dir (str | Path): Katalog bazowy z plikami benchmarków.

    Returns:
        dict[str, np.ndarray]: Słownik z macierzami benchmarków.

    Raises:
        BenchmarkValidationError: Jeśli benchmarki są niepoprawne lub niekompletne.
    """
    root = Path(base_dir)
    eeg = _load_csv_matrix(root / "eeg_target.csv")
    fmri = _load_csv_matrix(root / "fmri_target.csv")
    behavior = _load_csv_matrix(root / "behavior_target.csv")

    if eeg.shape[0] < 2 or fmri.shape[0] < 2 or behavior.shape[0] < 2:
        raise BenchmarkValidationError("Benchmarki muszą mieć co najmniej 2 wiersze.")

    return {"eeg": eeg, "fmri": fmri, "behavior": behavior}
