from __future__ import annotations

from dataclasses import dataclass

COGNITIVE_MODULE_TO_REGIONS = {
    "ATT": ("ATT", "SAL", "GW"),
    "EXEC": ("EXEC", "ATT", "MOT"),
    "EPIS": ("EPIS", "HIP", "SEM"),
    "SAL": ("SAL", "INT", "ATT"),
    "DMN": ("DMN", "SEM", "HIP"),
}


@dataclass(frozen=True, slots=True)
class TaskFunctionalMapping:
    """Opis mapowania zadania poznawczego na funkcje i regiony.

    Parameters
    ----------
    task_name:
        Techniczna nazwa zadania poznawczego.
    functions:
        Polskie nazwy funkcji kognitywnych pobudzanych przez zadanie.
    regions:
        Nazwy regionów lub proxy regionów pobudzanych przez zadanie.
    module_names:
        Techniczne nazwy modułów kognitywnych użyte do powiązania z istniejącą mapą.
    """

    task_name: str
    functions: tuple[str, ...]
    regions: tuple[str, ...]
    module_names: tuple[str, ...]


TASK_FUNCTIONAL_MAPPINGS: dict[str, TaskFunctionalMapping] = {
    "stroop": TaskFunctionalMapping(
        task_name="stroop",
        functions=("uwaga", "kontrola wykonawcza", "salience"),
        regions=("ACC", "DLPFC"),
        module_names=("ATT", "EXEC", "SAL"),
    ),
    "go_nogo": TaskFunctionalMapping(
        task_name="go_nogo",
        functions=("uwaga", "kontrola wykonawcza", "salience"),
        regions=("PFC", "basal-ganglia-proxy"),
        module_names=("ATT", "EXEC", "SAL"),
    ),
    "n_back": TaskFunctionalMapping(
        task_name="n_back",
        functions=("uwaga", "kontrola wykonawcza", "pamięć robocza"),
        regions=("DLPFC", "working-memory"),
        module_names=("ATT", "EXEC"),
    ),
    "roving_oddball": TaskFunctionalMapping(
        task_name="roving_oddball",
        functions=("uwaga", "salience"),
        regions=("SAL", "ACC"),
        module_names=("ATT", "SAL"),
    ),
}

_TASK_ALIASES = {
    "go-nogo": "go_nogo",
    "n-back": "n_back",
    "roving-oddball": "roving_oddball",
}


def normalize_task_name(task_name: str) -> str:
    """Normalizuje techniczną nazwę zadania do klucza mapowania.

    Parameters
    ----------
    task_name:
        Nazwa zadania z konfiguracji lub protokołu.

    Returns
    -------
    str
        Kanoniczna nazwa zadania używana w mapowaniach.
    """
    if not isinstance(task_name, str):
        task_name = str(task_name) if task_name is not None else ""
    normalized = task_name.lower().strip()
    return _TASK_ALIASES.get(normalized, normalized)


def regions_for_module(module_name: str) -> tuple[str, ...]:
    """
    Zwraca krotkę regionów odpowiadających modułowi kognitywnemu.

    Args:
        module_name (str): Nazwa modułu kognitywnego.

    Returns:
        tuple[str, ...]: Krotka nazw regionów.

    Raises:
        ValueError: Jeśli nieznany moduł.
    """
    try:
        return COGNITIVE_MODULE_TO_REGIONS[module_name]
    except KeyError as exc:
        raise ValueError(f"Unknown cognitive module mapping: {module_name}") from exc


def mapping_for_task(task_name: str) -> TaskFunctionalMapping:
    """Zwraca mapowanie zadania na funkcje kognitywne i regiony.

    Parameters
    ----------
    task_name:
        Techniczna nazwa zadania poznawczego.

    Returns
    -------
    TaskFunctionalMapping
        Deterministyczne mapowanie task→funkcje→regiony.

    Raises
    ------
    ValueError
        Gdy zadanie nie ma zdefiniowanego mapowania.
    """
    normalized = normalize_task_name(task_name)
    try:
        return TASK_FUNCTIONAL_MAPPINGS[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown task functional mapping: {task_name}") from exc


def regions_for_task(task_name: str) -> tuple[str, ...]:
    """Zwraca regiony pobudzane przez zadanie poznawcze.

    Parameters
    ----------
    task_name:
        Techniczna nazwa zadania poznawczego.

    Returns
    -------
    tuple[str, ...]
        Krotka regionów lub proxy regionów powiązanych z zadaniem.
    """
    return mapping_for_task(task_name).regions


def functions_for_task(task_name: str) -> tuple[str, ...]:
    """Zwraca funkcje kognitywne pobudzane przez zadanie poznawcze.

    Parameters
    ----------
    task_name:
        Techniczna nazwa zadania poznawczego.

    Returns
    -------
    tuple[str, ...]
        Polskie nazwy funkcji kognitywnych powiązanych z zadaniem.
    """
    return mapping_for_task(task_name).functions
