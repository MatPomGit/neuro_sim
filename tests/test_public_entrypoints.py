"""Testy kontraktu publicznych punktów wejścia symulatora."""

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_installed_cli_uses_single_experiment_engine() -> None:
    """Oba polecenia CLI mają delegować do tego samego engine config-driven."""
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    expected_entrypoint = '"brain_core.simulation.run:main"'

    assert f"neuro-sim = {expected_entrypoint}" in pyproject_text
    assert f"neuro-sim-run = {expected_entrypoint}" in pyproject_text


def test_root_main_is_only_compatibility_facade() -> None:
    """Root-level main nie może utrzymywać niezależnej logiki symulacji."""
    source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")

    assert "from brain_core.simulation.run import main" in source
    assert "CognitiveBrainModel" not in source
    assert "model.simulate" not in source


def test_importing_simulation_package_does_not_eagerly_load_engine() -> None:
    """Import publicznego pakietu nie może uruchamiać ciężkiego backendu engine."""
    command = (
        "import sys; import brain_core.simulation; "
        "assert 'brain_core.simulation.engine' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
