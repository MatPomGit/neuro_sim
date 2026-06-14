"""Pomocnicze walidatory zgodności nazw i metadanych BIDS."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BIDS_VERSION = "1.11.1"
BIDS_ENTITY_ORDER = (
    "sub",
    "ses",
    "task",
    "acq",
    "ce",
    "rec",
    "dir",
    "run",
    "mod",
    "echo",
    "part",
    "chunk",
)
BIDS_RAW_SUFFIXES = {
    "T1w",
    "T2w",
    "bold",
    "dwi",
    "eeg",
    "events",
    "channels",
    "electrodes",
    "coordsystem",
}
BIDS_ALLOWED_EXTENSIONS = {
    ".nii",
    ".nii.gz",
    ".json",
    ".tsv",
    ".edf",
    ".bdf",
    ".vhdr",
    ".vmrk",
    ".eeg",
    ".set",
    ".fdt",
}
_ENTITY_PATTERN = re.compile(r"^(?P<key>[a-z0-9]+)-(?P<value>[A-Za-z0-9]+)$")


@dataclass(frozen=True)
class BidsValidationResult:
    """Wynik lekkiej walidacji elementu BIDS.

    Parameters
    ----------
    is_valid:
        Informacja, czy sprawdzany element spełnia lokalne reguły BIDS.
    errors:
        Lista błędów blokujących uznanie elementu za zgodny z BIDS.
    warnings:
        Lista ostrzeżeń, które wymagają przeglądu metodologicznego.
    """

    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def _split_bids_extension(file_name: str) -> tuple[str, str]:
    """Oddziela nazwę bazową od rozszerzenia, obsługując ``.nii.gz``.

    Parameters
    ----------
    file_name:
        Nazwa pliku BIDS bez ścieżki katalogu.

    Returns
    -------
    tuple[str, str]
        Para zawierająca nazwę bez rozszerzenia i rozszerzenie.
    """
    if file_name.endswith(".nii.gz"):
        return file_name[: -len(".nii.gz")], ".nii.gz"
    path = Path(file_name)
    return path.stem, path.suffix


def validate_bids_file_name(file_name: str) -> BidsValidationResult:
    """Waliduje podstawową strukturę nazwy pliku BIDS.

    Parameters
    ----------
    file_name:
        Nazwa pliku, np. ``sub-001_task-rest_eeg.edf`` albo
        ``sub-001_task-rest_events.tsv``.

    Returns
    -------
    BidsValidationResult
        Wynik walidacji obejmujący kolejność encji, sufiks i rozszerzenie.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if Path(file_name).name != file_name:
        errors.append("Nazwa pliku BIDS nie może zawierać katalogów.")

    base_name, extension = _split_bids_extension(file_name)
    if extension not in BIDS_ALLOWED_EXTENSIONS:
        errors.append(
            f"Rozszerzenie '{extension}' nie jest obsługiwane przez lokalne reguły BIDS."
        )

    parts = base_name.split("_")
    if len(parts) < 2:
        errors.append("Nazwa BIDS musi zawierać co najmniej jedną encję i sufiks.")
        return BidsValidationResult(False, tuple(errors), tuple(warnings))

    suffix = parts[-1]
    if suffix not in BIDS_RAW_SUFFIXES:
        errors.append(
            f"Sufiks '{suffix}' nie jest zarejestrowany w lokalnych regułach raw BIDS."
        )

    seen_positions: list[int] = []
    seen_entities: set[str] = set()
    for entity in parts[:-1]:
        match = _ENTITY_PATTERN.match(entity)
        if match is None:
            errors.append(f"Encja '{entity}' nie ma postaci key-value zgodnej z BIDS.")
            continue
        key = match.group("key")
        if key not in BIDS_ENTITY_ORDER:
            errors.append(
                f"Encja '{key}' nie jest obsługiwana przez lokalne reguły BIDS."
            )
            continue
        if key in seen_entities:
            errors.append(f"Encja '{key}' występuje więcej niż raz.")
        seen_entities.add(key)
        seen_positions.append(BIDS_ENTITY_ORDER.index(key))

    if seen_positions != sorted(seen_positions):
        errors.append("Encje BIDS występują w niepoprawnej kolejności.")
    if not base_name.startswith("sub-"):
        warnings.append("Typowe pliki surowe BIDS zaczynają się od encji 'sub'.")

    return BidsValidationResult(not errors, tuple(errors), tuple(warnings))


def validate_dataset_description(path: Path) -> BidsValidationResult:
    """Waliduje minimalne metadane ``dataset_description.json`` dla BIDS.

    Parameters
    ----------
    path:
        Ścieżka do pliku ``dataset_description.json``.

    Returns
    -------
    BidsValidationResult
        Wynik walidacji pól wymaganych dla zbioru BIDS.
    """
    errors: list[str] = []
    warnings: list[str] = []
    try:
        metadata: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return BidsValidationResult(False, ("Brak pliku dataset_description.json.",))
    except json.JSONDecodeError as error:
        return BidsValidationResult(False, (f"Niepoprawny JSON: {error.msg}.",))

    for field_name in ("Name", "BIDSVersion", "DatasetType"):
        if not metadata.get(field_name):
            errors.append(
                f"Pole '{field_name}' jest wymagane w dataset_description.json."
            )
    if metadata.get("BIDSVersion") != BIDS_VERSION:
        current_version = metadata.get("BIDSVersion")
        warnings.append(
            "Pole 'BIDSVersion' ma wartość "
            f"'{current_version}', a projekt używa '{BIDS_VERSION}'."
        )
    if metadata.get("DatasetType") not in {"raw", "derivative"}:
        errors.append("Pole 'DatasetType' musi mieć wartość 'raw' albo 'derivative'.")

    return BidsValidationResult(not errors, tuple(errors), tuple(warnings))
