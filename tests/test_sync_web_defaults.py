from pathlib import Path

import pytest

from scripts.sync_web_defaults import read_dataclass_defaults


def test_read_dataclass_defaults_reads_literal_values(tmp_path: Path) -> None:
    """Odczyt domyślnych wartości obsługuje bezpieczne literały AST."""
    source_path = tmp_path / "literal_params.py"
    source_path.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class LiteralParams:\n"
        "    count: int = 3\n"
        "    ratio: float = 0.25\n"
        "    label: str = 'alpha'\n"
        "    enabled: bool = True\n"
        "    optional_value: object = None\n"
        "    thresholds: list[float] = [0.1, 0.2, 0.3]\n"
        "    metadata: dict[str, object] = {'mode': 'test', 'retries': 2}\n",
        encoding="utf-8",
    )

    defaults = read_dataclass_defaults(source_path, "LiteralParams")

    assert defaults == {
        "count": 3,
        "ratio": 0.25,
        "label": "alpha",
        "enabled": True,
        "optional_value": None,
        "thresholds": [0.1, 0.2, 0.3],
        "metadata": {"mode": "test", "retries": 2},
    }


def test_read_dataclass_defaults_reports_missing_class(tmp_path: Path) -> None:
    """Brak wskazanej klasy jest raportowany razem z nazwą klasy i ścieżką."""
    source_path = tmp_path / "missing_class_params.py"
    source_path.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class OtherParams:\n"
        "    count: int = 3\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error_info:
        read_dataclass_defaults(source_path, "ExpectedParams")

    message = str(error_info.value)
    assert "ExpectedParams" in message
    assert str(source_path) in message


def test_read_dataclass_defaults_reports_unsupported_expression_field(
    tmp_path: Path,
) -> None:
    """Nieobsługiwane wyrażenie domyślne wskazuje nazwę problematycznego pola."""
    source_path = tmp_path / "unsupported_params.py"
    source_path.write_text(
        "from dataclasses import dataclass\n"
        "from pathlib import Path\n\n"
        "@dataclass\n"
        "class UnsupportedParams:\n"
        "    output_path: Path = Path('x')\n"
        "    count: int = 3\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error_info:
        read_dataclass_defaults(source_path, "UnsupportedParams")

    message = str(error_info.value)
    assert "output_path" in message
    assert "count" not in message


def test_read_dataclass_defaults_reads_field_default_factory_constructor(
    tmp_path: Path,
) -> None:
    """Obsługiwany format fabryki pola zachowuje opis konstruktora i argumentów."""
    source_path = tmp_path / "factory_params.py"
    source_path.write_text(
        "from dataclasses import dataclass, field\n\n"
        "@dataclass\n"
        "class NestedParams:\n"
        "    gain: float = 1.5\n\n"
        "@dataclass\n"
        "class FactoryParams:\n"
        "    nested: NestedParams = field(\n"
        "        default_factory=lambda: NestedParams(gain=2.0, name='demo')\n"
        "    )\n",
        encoding="utf-8",
    )

    defaults = read_dataclass_defaults(source_path, "FactoryParams")

    assert defaults == {
        "nested": {
            "default_factory": "NestedParams",
            "kwargs": {"gain": 2.0, "name": "demo"},
        }
    }
