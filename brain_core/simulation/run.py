from __future__ import annotations

"""CLI uruchamiające eksperyment symulacyjny z pliku konfiguracji."""

import argparse
from typing import Any

from .config_loader import load_config
from .engine import run_experiment


def main() -> None:
    """Parsuje argumenty CLI, uruchamia eksperyment i wypisuje podsumowanie."""
    parser = argparse.ArgumentParser(description="Uruchom eksperyment z pliku konfiguracji YAML/JSON.")
    parser.add_argument("--config", required=True, help="Ścieżka do pliku konfiguracyjnego")
    args = parser.parse_args()

    cfg = load_config(args.config)
    result: dict[str, Any] = run_experiment(cfg)
    print(f"Done. duration={result['elapsed']:.3f}s")
    if result["save_info"]:
        print(f"Saved: {result['save_info']['output_dir']}")


if __name__ == "__main__":
    main()
