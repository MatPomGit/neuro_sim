from __future__ import annotations

from pathlib import Path

PLACEHOLDER_PHRASES = ("Opis funkcji", "Opis klasy")
PRODUCTION_DIRS = ("brain_model", "brain_core", "brain_viewer", "analysis", "scripts")


def test_production_docstrings_do_not_contain_placeholder_phrases() -> None:
    """Docstringi kodu produkcyjnego nie mogą zawierać fraz zastępczych."""
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for directory_name in PRODUCTION_DIRS:
        directory = repo_root / directory_name
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for phrase in PLACEHOLDER_PHRASES:
                if phrase in text:
                    offenders.append(f"{path.relative_to(repo_root)}: {phrase}")

    assert not offenders, "Znaleziono zastępcze frazy w docstringach:\n" + "\n".join(
        offenders
    )
