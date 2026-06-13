"""Statyczne testy ścieżek CLI eksperymentów."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CLI_EXPERIMENT_PATHS = (
    REPO_ROOT / "main.py",
    REPO_ROOT / "brain_core/simulation/run.py",
)


def test_cli_experiment_paths_do_not_use_print() -> None:
    """Pilnuj, aby nowe ścieżki CLI eksperymentów używały loggera zamiast `print()`."""
    print_calls: list[str] = []
    for source_path in CLI_EXPERIMENT_PATHS:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                print_calls.append(f"{source_path}:{node.lineno}")

    assert print_calls == []


def test_simulation_cli_exposes_dry_run_and_manifest_flags() -> None:
    """CLI eksperymentu pozwala walidować konfigurację i wskazać manifest."""
    source = (REPO_ROOT / "brain_core/simulation/run.py").read_text(encoding="utf-8")

    assert "--dry-run" in source
    assert "--manifest" in source
    assert "run_experiment(cfg)" in source
    assert "if args.dry_run" in source
    assert source.index("if args.dry_run") < source.index("run_experiment(cfg)")
