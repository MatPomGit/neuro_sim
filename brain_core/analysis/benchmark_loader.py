"""Loader benchmarków referencyjnych z walidacją spójności."""

from __future__ import annotations

import functools
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ALLOWED_BENCHMARK_LEVELS = frozenset(
    {"synthetic", "educational", "literature-inspired", "empirical"}
)
BENCHMARK_KEYS = ("eeg", "fmri", "behavior")
METADATA_FILE_NAME = "benchmark_metadata.json"
DEFAULT_BENCHMARK_BASE_DIR = Path("data/validation")


class BenchmarkValidationError(ValueError):
    """Wyjątek zgłaszany przy błędach walidacji benchmarków referencyjnych."""


def _resolve_benchmark_base_dir(base_dir: str | Path) -> Path:
    """Zwróć katalog benchmarków z obsługą zasobów spakowanych przez PyInstaller.

    Parameters
    ----------
    base_dir:
        Katalog bazowy z plikami benchmarków. Fallback do katalogu zasobów
        PyInstaller albo katalogu obok pliku EXE jest stosowany wyłącznie dla
        domyślnego katalogu projektu.

    Returns
    -------
    Path
        Ścieżka do katalogu benchmarków używana przez loader.
    """
    root = Path(base_dir)
    if root.exists() or root != DEFAULT_BENCHMARK_BASE_DIR:
        return root

    bundled_candidates: list[Path] = []
    pyinstaller_root = getattr(sys, "_MEIPASS", None)
    if pyinstaller_root:
        bundled_candidates.append(Path(pyinstaller_root) / DEFAULT_BENCHMARK_BASE_DIR)

    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        bundled_candidates.extend(
            [
                executable_dir / DEFAULT_BENCHMARK_BASE_DIR,
                executable_dir / "_internal" / DEFAULT_BENCHMARK_BASE_DIR,
            ]
        )

    for bundled_root in bundled_candidates:
        if bundled_root.exists():
            return bundled_root
    return root


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
    compliance_criteria:
        Jawny opis kryteriów zgodności używany w raportach tekstowych.
    compliance_checks:
        Strukturalne kryteria zgodności per benchmark. Każde pole musi pochodzić
        z pliku metadanych, aby kod nie dopisywał arbitralnych progów.
    """

    source: str
    scope: str
    limitations: str
    level: str
    compliance_criteria: str
    compliance_checks: dict[str, object]

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

    def to_dict(self) -> dict[str, object]:
        """Przekształć metadane benchmarku do słownika serializowalnego do JSON.

        Returns
        -------
        dict[str, str]
            Słownik z polami ``source``, ``scope``, ``limitations``, ``level``,
            ``compliance_criteria``, ``compliance_checks`` i
            ``comparison_origin_pl``.
        """
        return {
            "source": self.source,
            "scope": self.scope,
            "limitations": self.limitations,
            "level": self.level,
            "compliance_criteria": self.compliance_criteria,
            "compliance_checks": dict(self.compliance_checks),
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

    def metadata_payload(self) -> dict[str, dict[str, object]]:
        """Zwróć metadane w formie gotowej do zapisania w raporcie.

        Returns
        -------
        dict[str, dict[str, object]]
            Zagnieżdżony słownik metadanych benchmarków.
        """
        return {name: item.to_dict() for name, item in self.metadata.items()}


def _load_csv_matrix(
    path: Path, compliance_checks: dict[str, object] | None = None
) -> np.ndarray:
    """
    Ładuje macierz danych z pliku CSV i waliduje jej strukturę.

    Args:
        path (Path): Ścieżka do pliku CSV.
        compliance_checks (dict[str, object] | None): Jawne kryteria zgodności
            odczytane z metadanych benchmarku. Funkcja nie dopisuje brakujących
            kryteriów domyślnych.

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
    if compliance_checks is not None:
        required_columns = compliance_checks.get("required_columns")
        if not isinstance(required_columns, list):
            raise BenchmarkValidationError(
                f"Brak listy wymaganych kolumn w kryteriach dla pliku: {path}"
            )
        missing_columns = [
            str(column) for column in required_columns if str(column) not in cols
        ]
        if missing_columns:
            raise BenchmarkValidationError(
                f"Plik {path} nie spełnia kryteriów kolumn: "
                + ", ".join(missing_columns)
            )
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


def _validate_compliance_checks(
    benchmark_name: str, metadata: dict[str, object]
) -> dict[str, object]:
    """Zweryfikuj strukturalne kryteria zgodności benchmarku.

    Parameters
    ----------
    benchmark_name:
        Nazwa benchmarku, dla którego walidowane są kryteria.
    metadata:
        Surowe metadane odczytane z pliku JSON.

    Returns
    -------
    dict[str, object]
        Kryteria zgodności opisane w pliku metadanych.

    Raises
    ------
    BenchmarkValidationError
        Gdy kryteria są nieobecne albo nie zawierają wymaganych pól.
    """
    checks = metadata.get("compliance_checks")
    if not isinstance(checks, dict):
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} musi mieć obiekt compliance_checks."
        )

    required_fields = (
        "required_columns",
        "minimum_rows",
        "accepted_comparison_metrics",
        "interpretation_scope",
        "acceptance_rule",
    )
    missing = [field for field in required_fields if field not in checks]
    if missing:
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} nie ma pól compliance_checks: "
            + ", ".join(missing)
        )

    required_columns = checks["required_columns"]
    if (
        not isinstance(required_columns, list)
        or not all(isinstance(item, str) and item.strip() for item in required_columns)
        or any(item.strip() in {"time", "trial"} for item in required_columns)
    ):
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} ma niepoprawne required_columns "
            "(nie mogą zawierać 'time' ani 'trial')."
        )

    accepted_metrics = checks["accepted_comparison_metrics"]
    if not isinstance(accepted_metrics, list) or not all(
        isinstance(item, str) and item.strip() for item in accepted_metrics
    ):
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} ma niepoprawne accepted_comparison_metrics."
        )

    minimum_rows = checks["minimum_rows"]
    if isinstance(minimum_rows, bool) or not isinstance(minimum_rows, int):
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} ma niepoprawne minimum_rows."
        )
    if minimum_rows < 2:
        raise BenchmarkValidationError(
            f"Benchmark {benchmark_name} musi wymagać co najmniej dwóch wierszy."
        )

    normalized = dict(checks)
    normalized["required_columns"] = [str(item).strip() for item in required_columns]
    normalized["accepted_comparison_metrics"] = [
        str(item).strip() for item in accepted_metrics
    ]
    normalized["minimum_rows"] = minimum_rows
    for text_field in ("interpretation_scope", "acceptance_rule"):
        value = normalized[text_field]
        if not isinstance(value, str) or not value.strip():
            raise BenchmarkValidationError(
                f"Benchmark {benchmark_name} ma niepoprawne {text_field}."
            )
        normalized[text_field] = value.strip()
    return normalized


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
    compliance_criteria = _validate_text_field(
        benchmark_name, metadata, "compliance_criteria"
    )
    compliance_checks = _validate_compliance_checks(benchmark_name, metadata)
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
        compliance_criteria=compliance_criteria,
        compliance_checks=compliance_checks,
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
    path = _resolve_benchmark_base_dir(base_dir) / METADATA_FILE_NAME
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
    root = _resolve_benchmark_base_dir(base_dir)
    metadata = load_reference_benchmark_metadata(base_dir)
    matrices = {
        "eeg": _load_csv_matrix(
            root / "eeg_target.csv", metadata["eeg"].compliance_checks
        ),
        "fmri": _load_csv_matrix(
            root / "fmri_target.csv", metadata["fmri"].compliance_checks
        ),
        "behavior": _load_csv_matrix(
            root / "behavior_target.csv", metadata["behavior"].compliance_checks
        ),
    }

    for benchmark_name, matrix in matrices.items():
        minimum_rows = metadata[benchmark_name].compliance_checks["minimum_rows"]
        if matrix.shape[0] < int(minimum_rows):
            raise BenchmarkValidationError(
                f"Benchmark {benchmark_name} musi mieć co najmniej "
                f"{minimum_rows} wiersze."
            )

    return matrices
