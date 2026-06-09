"""CLI uruchamiające eksperyment symulacyjny z pliku konfiguracji."""

from __future__ import annotations

import argparse
from typing import Any

from .config_loader import load_config
from .engine import run_experiment
from .logging_utils import configure_simulation_logger


def main() -> None:
    """Parsuje argumenty CLI, uruchamia eksperyment i zapisuje podsumowanie w logach."""
    parser = argparse.ArgumentParser(
        description="Uruchom eksperyment z pliku konfiguracji YAML/JSON."
    )
    parser.add_argument(
        "--config", required=True, help="Ścieżka do pliku konfiguracyjnego"
    )
    args = parser.parse_args()

    logger = configure_simulation_logger()
    cfg = load_config(args.config)
    result: dict[str, Any] = run_experiment(cfg)
    save_info = result.get("save_info")
    if save_info:
        logger = configure_simulation_logger(log_file=save_info["output_dir"])
    logger.info("Zakończono eksperyment. Czas wykonania: %.3f s.", result["elapsed"])
    if save_info:
        logger.info(
            "Zapisano wyniki eksperymentu w katalogu: %s.", save_info["output_dir"]
        )


if __name__ == "__main__":
    main()
