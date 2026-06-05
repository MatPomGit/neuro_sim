"""Ładowanie i walidacja konfiguracji eksperymentów symulacyjnych."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .config_schema import ConfigValidationError, ExperimentConfig, validate_config


def _parse_payload(payload: str, suffix: str = "") -> dict[str, Any]:
    """Parsuje payload konfiguracji YAML/JSON do słownika Python.

    Parameters
    ----------
    payload:
        Tekst konfiguracji.
    suffix:
        Rozszerzenie pliku albo sztuczna podpowiedź formatu.

    Returns
    -------
    dict[str, Any]
        Surowy słownik konfiguracji kierowany do wspólnej walidacji schematu.

    Raises
    ------
    ConfigValidationError
        Gdy payload nie jest obiektem YAML/JSON.
    """
    normalized_suffix = suffix.lower()
    if normalized_suffix == ".json":
        parsed = json.loads(payload)
    else:
        parsed = yaml.safe_load(payload)

    if not isinstance(parsed, dict):
        raise ConfigValidationError(
            "Konfiguracja YAML/JSON musi być obiektem mapującym na poziomie głównym."
        )
    return parsed


def load_config(path: str | Path) -> ExperimentConfig:
    """Wczytuje konfigurację z pliku i zwraca obiekt po walidacji.

    Parameters
    ----------
    path:
        Ścieżka do pliku konfiguracyjnego YAML albo JSON.

    Returns
    -------
    ExperimentConfig
        Zweryfikowany obiekt konfiguracji.
    """
    config_path = Path(path)
    raw_config = _parse_payload(
        config_path.read_text(encoding="utf-8"), suffix=config_path.suffix
    )
    return validate_config(raw_config)


def load_config_from_string(
    payload: str, format_hint: str = "yaml"
) -> ExperimentConfig:
    """Wczytuje konfigurację z tekstu i zwraca obiekt po walidacji.

    Parameters
    ----------
    payload:
        Tekst konfiguracji.
    format_hint:
        Podpowiedź formatu: `yaml` albo `json`.

    Returns
    -------
    ExperimentConfig
        Zweryfikowany obiekt konfiguracji.
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
    validate_config(raw_profile, require_sections=False)
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
