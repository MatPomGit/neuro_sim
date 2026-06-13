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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Tylko wczytaj i zwaliduj konfigurację bez uruchamiania symulacji "
            "ani tworzenia artefaktów."
        ),
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Po zapisie wyników zaloguj ścieżkę pliku run_manifest.json.",
    )
    args = parser.parse_args()

    logger = configure_simulation_logger()
    cfg = load_config(args.config)
    if args.dry_run:
        logger.info(
            "Konfiguracja poprawna. Tryb dry-run: nie uruchomiono symulacji. "
            "task=%s, seed=%s, save_results=%s.",
            cfg.task.get("name", cfg.task.get("scenario", "n/a")),
            cfg.seed,
            cfg.output.get("save_results", False),
        )
        return

    result: dict[str, Any] = run_experiment(cfg)
    save_info = result.get("save_info")
    if save_info:
        logger = configure_simulation_logger(log_file=save_info["output_dir"])
    logger.info("Zakończono eksperyment. Czas wykonania: %.3f s.", result["elapsed"])
    if save_info:
        logger.info(
            "Zapisano wyniki eksperymentu w katalogu: %s.", save_info["output_dir"]
        )
        if args.manifest:
            logger.info(
                "Manifest reprodukowalności: %s.",
                save_info.get("manifest", "brak manifestu"),
            )


if __name__ == "__main__":
    main()
