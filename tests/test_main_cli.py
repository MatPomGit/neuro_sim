"""Testy root-level fasady CLI po ujednoliceniu pipeline'u."""

from __future__ import annotations

import sys
from typing import Any

import main
from brain_core.simulation import run as simulation_run


def test_root_main_delegates_to_experiment_cli() -> None:
    """Root-level `main.py` ma eksportować dokładnie wspólną funkcję CLI."""
    assert main.main is simulation_run.main


def test_root_main_accepts_config_driven_dry_run(monkeypatch: Any) -> None:
    """Fasada ma obsługiwać ten sam kontrakt `--config --dry-run` co engine."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--config", "configs/default.yaml", "--dry-run"],
    )
    main.main()
