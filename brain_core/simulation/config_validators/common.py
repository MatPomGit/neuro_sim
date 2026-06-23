"""Wspólne narzędzia walidacji sekcji konfiguracji symulacji."""

from __future__ import annotations

import math
from typing import Any


class ConfigValidationError(ValueError):
    """Błąd walidacji konfiguracji eksperymentu."""


def require_mapping(value: Any, field_path: str) -> dict[str, Any]:
    """Wymaga obiektu mapującego dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, dict):
        raise ConfigValidationError(f"{field_path} musi być obiektem")
    return dict(value)


def require_bool(value: Any, field_path: str) -> bool:
    """Wymaga wartości logicznej dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, bool):
        raise ConfigValidationError(f"{field_path} musi być wartością logiczną")
    return value


def require_non_empty_string(value: Any, field_path: str) -> str:
    """Wymaga niepustego tekstu dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"{field_path} musi być niepustym tekstem")
    return value.strip()


def require_number(value: Any, field_path: str) -> float:
    """Wymaga skończonej liczby dla wskazanej ścieżki konfiguracji."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigValidationError(f"{field_path} musi być liczbą")
    number = float(value)
    if not math.isfinite(number):
        raise ConfigValidationError(f"{field_path} musi być liczbą skończoną")
    return number


def require_positive_number(value: Any, field_path: str) -> float:
    """Wymaga dodatniej skończonej liczby dla wskazanej ścieżki konfiguracji."""
    number = require_number(value, field_path)
    if number <= 0:
        raise ConfigValidationError(f"{field_path} musi być > 0")
    return number


def require_non_negative_int(value: Any, field_path: str) -> int:
    """Wymaga nieujemnej liczby całkowitej dla wskazanej ścieżki konfiguracji."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"{field_path} musi być liczbą całkowitą")
    if value < 0:
        raise ConfigValidationError(f"{field_path} musi być >= 0")
    return int(value)


def require_list(value: Any, field_path: str) -> list[Any]:
    """Wymaga listy dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, list):
        raise ConfigValidationError(f"{field_path} musi być listą")
    return list(value)


def coerce_string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    """Normalizuje listę nazw regionów SNN do krotki niepustych tekstów."""
    values = require_list(value, field_name)
    if not all(isinstance(item, str) and item.strip() for item in values):
        raise ConfigValidationError(f"{field_name} musi być listą niepustych tekstów")
    return tuple(str(item).strip() for item in values)
