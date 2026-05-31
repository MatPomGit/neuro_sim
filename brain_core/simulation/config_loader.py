"""Ładowanie i walidacja konfiguracji eksperymentów symulacyjnych."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .config_schema import ExperimentConfig, validate_config


def _parse_payload(payload: str, suffix: str = "") -> dict[str, Any]:
    """
    Parsuje payload konfiguracji YAML/JSON do słownika Python.

    Args:
        payload (str): Tekst konfiguracji.
        suffix (str): Rozszerzenie pliku (".yaml" lub ".json").

    Returns:
        dict[str, Any]: Słownik z konfiguracją.

    """
    if suffix.lower() == ".json":
        return json.loads(payload)
    try:
        parsed = yaml.safe_load(payload)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return json.loads(payload)


def load_config(path: str | Path) -> ExperimentConfig:
    """
    Wczytuje konfigurację z pliku i zwraca obiekt po walidacji.

    Args:
        path (str | Path): Ścieżka do pliku konfiguracyjnego.

    Returns:
        ExperimentConfig: Zweryfikowany obiekt konfiguracji.
    """
    config_path = Path(path)
    raw_config = _parse_payload(
        config_path.read_text(encoding="utf-8"), suffix=config_path.suffix
    )
    return validate_config(raw_config)


def load_config_from_string(
    payload: str, format_hint: str = "yaml"
) -> ExperimentConfig:
    """
    Wczytuje konfigurację z tekstu i zwraca obiekt po walidacji.

    Args:
        payload (str): Tekst konfiguracji.
        format_hint (str): Podpowiedź formatu ("yaml" lub "json").

    Returns:
        ExperimentConfig: Zweryfikowany obiekt konfiguracji.
    """
    suffix = ".json" if format_hint.lower() == "json" else ".yaml"
    raw_config = _parse_payload(payload, suffix=suffix)
    return validate_config(raw_config)


def load_clinical_profile(path: str | Path) -> dict[str, Any]:
    """Wczytaj pojedynczy profil kliniczny YAML/JSON jako fragment konfiguracji.

    Parameters
    ----------
    path:
        Ścieżka do pliku profilu klinicznego z katalogu `configs/clinical_profiles`.

    Returns
    -------
    dict[str, Any]
        Zweryfikowany fragment konfiguracji zawierający sekcję `clinical_profile`.

    Raises
    ------
    ConfigValidationError
        Gdy profil nie spełnia schematu konfiguracji eksperymentu.
    """
    profile_path = Path(path)
    raw_profile = _parse_payload(
        profile_path.read_text(encoding="utf-8"), suffix=profile_path.suffix
    )
    validate_config(raw_profile)
    return raw_profile


def load_clinical_profiles(paths: list[str | Path]) -> list[dict[str, Any]]:
    """Wczytaj wiele profili klinicznych zachowując kolejność ścieżek.

    Parameters
    ----------
    paths:
        Lista ścieżek do plików profili klinicznych.

    Returns
    -------
    list[dict[str, Any]]
        Lista zweryfikowanych fragmentów konfiguracji profili klinicznych.
    """
    return [load_clinical_profile(path) for path in paths]
