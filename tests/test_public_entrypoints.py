"""Testy kontraktu publicznych punktów wejścia symulatora."""

from pathlib import Path


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
