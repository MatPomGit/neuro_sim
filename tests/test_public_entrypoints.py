"""Testy kontraktu publicznych punktów wejścia symulatora."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_installed_cli_uses_single_experiment_engine() -> None:
    """Oba polecenia CLI mają delegować do tego samego engine config-driven."""
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pyproject = tomllib.loads(pyproject_text)
    scripts = pyproject["project"]["scripts"]

    expected = "brain_core.simulation.run:main"
    assert scripts["neuro-sim"] == expected
    assert scripts["neuro-sim-run"] == expected


def test_root_main_is_only_compatibility_facade() -> None:
    """Root-level main nie może utrzymywać niezależnej logiki symulacji."""
    source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")

    assert "from brain_core.simulation.run import main" in source
    assert "CognitiveBrainModel" not in source
    assert "model.simulate" not in source
