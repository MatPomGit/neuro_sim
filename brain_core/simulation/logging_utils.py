"""Narzędzia konfiguracji logowania dla uruchomień symulacyjnych."""

from __future__ import annotations

import logging
from pathlib import Path

DEFAULT_LOGGER_NAME = "neuro_sim.simulation"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_simulation_logger(
    *,
    name: str = DEFAULT_LOGGER_NAME,
    log_file: str | Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Skonfiguruj logger konsolowy oraz opcjonalny plik `run.log`.

    Parameters
    ----------
    name:
        Nazwa loggera używanego przez ścieżkę CLI eksperymentu.
    log_file:
        Opcjonalna ścieżka pliku logu. Gdy wskazuje katalog, log zostanie
        zapisany jako `run.log` w tym katalogu.
    level:
        Minimalny poziom komunikatów logowania.

    Returns
    -------
    logging.Logger
        Skonfigurowany logger bez propagacji do loggera głównego, aby uniknąć
        zdublowanych komunikatów w konsoli.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    _ensure_stream_handler(logger, formatter, level)
    if log_file is not None:
        _ensure_file_handler(logger, _normalize_log_file(log_file), formatter, level)

    return logger


def _normalize_log_file(log_file: str | Path) -> Path:
    """Znormalizuj ścieżkę logu do konkretnego pliku `run.log`."""
    log_path = Path(log_file)
    if log_path.suffix:
        return log_path
    return log_path / "run.log"


def _ensure_stream_handler(
    logger: logging.Logger,
    formatter: logging.Formatter,
    level: int,
) -> None:
    """Dodaj handler konsolowy tylko wtedy, gdy nie został jeszcze dodany."""
    for handler in logger.handlers:
        if getattr(handler, "_neuro_sim_console", False):
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    stream_handler._neuro_sim_console = True  # type: ignore[attr-defined]
    logger.addHandler(stream_handler)


def _ensure_file_handler(
    logger: logging.Logger,
    log_file: Path,
    formatter: logging.Formatter,
    level: int,
) -> None:
    """Dodaj handler pliku logu bez duplikowania tej samej ścieżki."""
    resolved_log_file = log_file.resolve()
    for handler in logger.handlers:
        if getattr(handler, "_neuro_sim_log_file", None) == resolved_log_file:
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler._neuro_sim_log_file = resolved_log_file  # type: ignore[attr-defined]
    logger.addHandler(file_handler)
