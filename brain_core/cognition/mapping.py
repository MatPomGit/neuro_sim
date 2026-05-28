from __future__ import annotations

COGNITIVE_MODULE_TO_REGIONS = {
    "ATT": ("ATT", "SAL", "GW"),
    "EXEC": ("EXEC", "ATT", "MOT"),
    "EPIS": ("EPIS", "HIP", "SEM"),
    "SAL": ("SAL", "INT", "ATT"),
    "DMN": ("DMN", "SEM", "HIP"),
}


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
