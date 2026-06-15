"""Katalog lekcji dydaktycznych wczytywanych z konfiguracji YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

LESSON_CONFIG_DIR = Path("configs/lessons")
_REQUIRED_LESSON_FIELDS = {
    "id",
    "label_pl",
    "level_pl",
    "estimated_duration_min",
    "scenario_config",
    "comparison_config",
    "learning_goal_pl",
    "pre_run_questions_pl",
    "expected_observations_pl",
    "post_run_questions_pl",
    "next_run_changes",
}


@dataclass(frozen=True)
class LessonCatalogItem:
    """Opis pojedynczej lekcji dydaktycznej dostępnej w GUI.

    Parameters
    ----------
    id:
        Techniczny identyfikator lekcji używany do stabilnego rozpoznawania
        wpisu katalogu.
    label_pl:
        Polska etykieta lekcji prezentowana użytkownikowi.
    level_pl:
        Polski opis poziomu trudności lekcji.
    estimated_duration_min:
        Szacowany czas wykonania lekcji w minutach.
    scenario_config:
        Ścieżka do konfiguracji YAML uruchamianej przez silnik symulacji.
    comparison_config:
        Opcjonalna ścieżka do konfiguracji porównania profili.
    learning_goal_pl:
        Polski opis celu dydaktycznego lekcji.
    pre_run_questions_pl:
        Pytania kontrolne zadawane przed uruchomieniem symulacji.
    expected_observations_pl:
        Oczekiwane obserwacje interpretowane po uruchomieniu symulacji.
    post_run_questions_pl:
        Pytania podsumowujące po analizie wyniku.
    next_run_changes:
        Propozycje zmian parametrów dla kolejnego uruchomienia.
    """

    id: str
    label_pl: str
    level_pl: str
    estimated_duration_min: int
    scenario_config: str
    comparison_config: str | None
    learning_goal_pl: str
    pre_run_questions_pl: list[str]
    expected_observations_pl: list[str]
    post_run_questions_pl: list[str]
    next_run_changes: list[dict[str, str]]


def _load_lesson_payload(path: Path) -> dict[str, Any]:
    """Wczytaj pojedynczy plik lekcji YAML jako mapowanie.

    Parameters
    ----------
    path:
        Ścieżka do pliku ``configs/lessons/*.yaml``.

    Returns
    -------
    dict[str, Any]
        Surowe mapowanie pól lekcji.

    Raises
    ------
    ValueError
        Gdy dokument YAML nie jest mapowaniem.
    yaml.YAMLError
        Gdy plik zawiera niepoprawną składnię YAML.
    OSError
        Gdy pliku nie można odczytać.
    """

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Lekcja {path} musi być mapowaniem YAML.")
    return payload


def _require_lesson_fields(path: Path, payload: dict[str, Any]) -> None:
    """Sprawdź obecność obowiązkowych pól lekcji.

    Parameters
    ----------
    path:
        Ścieżka pliku używana w komunikacie diagnostycznym.
    payload:
        Surowe mapowanie YAML lekcji.

    Raises
    ------
    ValueError
        Gdy brakuje co najmniej jednego wymaganego pola.
    """

    lesson_name = str(payload.get("id") or path.stem)
    for field_name in sorted(_REQUIRED_LESSON_FIELDS):
        if field_name not in payload:
            raise ValueError(f"Lekcja {lesson_name} nie zawiera pola {field_name}.")


def _as_string_list(path: Path, payload: dict[str, Any], field_name: str) -> list[str]:
    """Zwaliduj i zwróć pole lekcji jako listę tekstów.

    Parameters
    ----------
    path:
        Ścieżka pliku używana w komunikacie diagnostycznym.
    payload:
        Surowe mapowanie YAML lekcji.
    field_name:
        Nazwa walidowanego pola.

    Returns
    -------
    list[str]
        Lista niepustych tekstów z pola lekcji.

    Raises
    ------
    ValueError
        Gdy pole nie jest niepustą listą tekstów.
    """

    values = payload[field_name]
    lesson_name = str(payload.get("id") or path.stem)
    if not isinstance(values, list) or not values:
        raise ValueError(f"Lekcja {lesson_name} musi mieć niepustą listę {field_name}.")
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"Lekcja {lesson_name} ma niepoprawne teksty w {field_name}.")
    return list(values)


def _as_next_run_changes(path: Path, payload: dict[str, Any]) -> list[dict[str, str]]:
    """Zwaliduj i zwróć propozycje zmian kolejnego uruchomienia.

    Parameters
    ----------
    path:
        Ścieżka pliku używana w komunikacie diagnostycznym.
    payload:
        Surowe mapowanie YAML lekcji.

    Returns
    -------
    list[dict[str, str]]
        Lista mapowań tekstowych opisujących zmianę kolejnego uruchomienia.

    Raises
    ------
    ValueError
        Gdy pole nie jest niepustą listą mapowań tekstowych.
    """

    values = payload["next_run_changes"]
    lesson_name = str(payload.get("id") or path.stem)
    if not isinstance(values, list) or not values:
        raise ValueError(
            f"Lekcja {lesson_name} musi mieć niepustą listę next_run_changes."
        )
    changes: list[dict[str, str]] = []
    for value in values:
        if not isinstance(value, dict) or not all(
            isinstance(key, str) and isinstance(item, str)
            for key, item in value.items()
        ):
            raise ValueError(
                f"Lekcja {lesson_name} ma niepoprawny wpis next_run_changes."
            )
        changes.append(dict(value))
    return changes


def _lesson_from_payload(path: Path, payload: dict[str, Any]) -> LessonCatalogItem:
    """Zbuduj zwalidowany element katalogu lekcji z mapowania YAML.

    Parameters
    ----------
    path:
        Ścieżka pliku lekcji.
    payload:
        Surowe mapowanie YAML lekcji.

    Returns
    -------
    LessonCatalogItem
        Niemutowalny opis lekcji używany przez GUI i testy statyczne.

    Raises
    ------
    ValueError
        Gdy wymagane pole jest nieobecne albo ma nieobsługiwany typ.
    """

    _require_lesson_fields(path, payload)
    lesson_name = str(payload.get("id") or path.stem)
    string_fields = (
        "id",
        "label_pl",
        "level_pl",
        "scenario_config",
        "learning_goal_pl",
    )
    for field_name in string_fields:
        if not isinstance(payload[field_name], str) or not payload[field_name].strip():
            raise ValueError(f"Lekcja {lesson_name} ma niepoprawne pole {field_name}.")
    comparison_config = payload["comparison_config"]
    if comparison_config is not None and not isinstance(comparison_config, str):
        raise ValueError(f"Lekcja {lesson_name} ma niepoprawne pole comparison_config.")
    estimated_duration_min = payload["estimated_duration_min"]
    if not isinstance(estimated_duration_min, int) or estimated_duration_min <= 0:
        raise ValueError(
            f"Lekcja {lesson_name} ma niepoprawne pole estimated_duration_min."
        )

    return LessonCatalogItem(
        id=payload["id"],
        label_pl=payload["label_pl"],
        level_pl=payload["level_pl"],
        estimated_duration_min=estimated_duration_min,
        scenario_config=payload["scenario_config"],
        comparison_config=comparison_config,
        learning_goal_pl=payload["learning_goal_pl"],
        pre_run_questions_pl=_as_string_list(path, payload, "pre_run_questions_pl"),
        expected_observations_pl=_as_string_list(
            path, payload, "expected_observations_pl"
        ),
        post_run_questions_pl=_as_string_list(path, payload, "post_run_questions_pl"),
        next_run_changes=_as_next_run_changes(path, payload),
    )


def load_lesson_catalog() -> list[LessonCatalogItem]:
    """Wczytaj katalog lekcji dydaktycznych z ``configs/lessons``.

    Returns
    -------
    list[LessonCatalogItem]
        Lekcje posortowane deterministycznie według nazwy pliku YAML.

    Raises
    ------
    ValueError
        Gdy katalog lekcji nie istnieje albo dowolny plik ma niepełną strukturę.
    yaml.YAMLError
        Gdy plik zawiera niepoprawną składnię YAML.
    OSError
        Gdy pliku nie można odczytać.
    """

    if not LESSON_CONFIG_DIR.exists():
        raise ValueError(f"Katalog lekcji {LESSON_CONFIG_DIR} nie istnieje.")
    return [
        _lesson_from_payload(path, _load_lesson_payload(path))
        for path in sorted(LESSON_CONFIG_DIR.glob("*.yaml"))
    ]


def lesson_labels() -> list[str]:
    """Zwróć polskie etykiety lekcji dostępnych w katalogu.

    Returns
    -------
    list[str]
        Etykiety ``label_pl`` zachowujące kolejność katalogu lekcji.
    """

    return [lesson.label_pl for lesson in load_lesson_catalog()]


def lesson_by_label(label: str) -> LessonCatalogItem | None:
    """Znajdź lekcję po polskiej etykiecie widocznej w GUI.

    Parameters
    ----------
    label:
        Polska etykieta lekcji z kontrolki wyboru.

    Returns
    -------
    LessonCatalogItem | None
        Dopasowana lekcja albo ``None``, gdy etykieta nie istnieje w katalogu.
    """

    for lesson in load_lesson_catalog():
        if lesson.label_pl == label:
            return lesson
    return None
