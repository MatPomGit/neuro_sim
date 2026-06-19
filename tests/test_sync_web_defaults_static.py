from pathlib import Path

import pytest

from scripts.sync_web_defaults import read_dataclass_defaults


def test_read_dataclass_defaults_reads_literal_value(tmp_path: Path) -> None:
    """Funkcja odczytuje literalne wartości domyślne bez uruchamiania modułu."""
    source_path = tmp_path / "params.py"
    source_path.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class ExampleParams:\n"
        "    threshold: float = 0.75\n"
        "    enabled: bool = True\n",
        encoding="utf-8",
    )

    defaults = read_dataclass_defaults(source_path, "ExampleParams")

    assert defaults == {"threshold": 0.75, "enabled": True}


def test_read_dataclass_defaults_reports_unsupported_expression(
    tmp_path: Path,
) -> None:
    """Funkcja zgłasza pola z wartościami niemożliwymi do statycznego odczytu."""
    source_path = tmp_path / "params.py"
    source_path.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class ExampleParams:\n"
        "    threshold: float = float(0.75)\n"
        "    enabled: bool = True\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error_info:
        read_dataclass_defaults(source_path, "ExampleParams")

    message = str(error_info.value)
    assert str(source_path) in message
    assert "ExampleParams" in message
    assert "threshold" in message
    assert "enabled" not in message


def test_read_dataclass_defaults_reports_missing_class(tmp_path: Path) -> None:
    """Funkcja zgłasza brak wskazanej klasy zamiast zwracać pusty słownik."""
    source_path = tmp_path / "params.py"
    source_path.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class OtherParams:\n"
        "    threshold: float = 0.75\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error_info:
        read_dataclass_defaults(source_path, "ExampleParams")

    message = str(error_info.value)
    assert str(source_path) in message
    assert "ExampleParams" in message
