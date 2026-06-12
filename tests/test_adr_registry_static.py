"""Statyczne testy spójności rejestru ADR z plikami decyzji."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_INDEX_PATH = REPO_ROOT / "docs" / "architecture_decision_records.md"
ADR_STATUS_PATTERN = re.compile(
    r"^\*\*Status:\*\*\s*(proposed|accepted|superseded|deprecated)\b",
    flags=re.MULTILINE,
)
INDEX_ROW_PATTERN = re.compile(
    r"^\|\s*(ADR-\d{4})\s*\|\s*"
    r"(proposed|accepted|superseded|deprecated)\s*\|[^|]*\|\s*"
    r"\[`docs/adr/([^`]+)`\]\(adr/[^)]+\)",
    flags=re.MULTILINE,
)


def _indexed_adr_statuses() -> dict[str, tuple[str, Path]]:
    """Wczytaj statusy ADR wskazanych w indeksie jako osobne pliki."""
    index_source = ADR_INDEX_PATH.read_text(encoding="utf-8")
    indexed_statuses: dict[str, tuple[str, Path]] = {}

    for match in INDEX_ROW_PATTERN.finditer(index_source):
        adr_id, status, file_name = match.groups()
        indexed_statuses[adr_id] = (status, REPO_ROOT / "docs" / "adr" / file_name)

    return indexed_statuses


def _file_adr_status(path: Path) -> str:
    """Zwróć status zapisany w nagłówku pliku ADR."""
    source = path.read_text(encoding="utf-8")
    match = ADR_STATUS_PATTERN.search(source)

    assert match is not None, f"Brak statusu ADR w pliku: {path}"
    return match.group(1)


def test_adr_registry_statuses_match_adr_files() -> None:
    """Status w indeksie ADR musi odpowiadać statusowi w docelowym pliku ADR."""
    indexed_statuses = _indexed_adr_statuses()

    assert indexed_statuses
    for adr_id, (index_status, path) in indexed_statuses.items():
        assert path.exists(), f"{adr_id} wskazuje nieistniejący plik: {path}"
        assert index_status == _file_adr_status(path), (
            f"{adr_id} ma status {index_status!r} w indeksie, "
            f"ale inny status w pliku {path}."
        )
