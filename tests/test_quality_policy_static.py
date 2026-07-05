from __future__ import annotations

import ast
from pathlib import Path

import tomllib

PRODUCTION_DOCSTRING_SCOPES = (
    "brain_core/**/*.py",
    "brain_model/**/*.py",
    "scripts/**/*.py",
)
PRODUCTION_SCOPES_WITHOUT_DOCSTRING_IGNORES = ("analysis/**/*.py",)
STRICT_MYPY_MODULES = {
    "brain_model.oscillators",
    "brain_model.calibration",
    "brain_model.validation",
}
STRICT_NO_ANY_PATHS = (
    Path("brain_model/oscillators.py"),
    Path("brain_model/calibration.py"),
    Path("brain_model/validation.py"),
)
TEST_ANY_RETURN_BASELINE = {
    Path("tests/test_atlas_connectome.py"): 1,
    Path("tests/test_experiment_result.py"): 2,
    Path("tests/test_lesions.py"): 4,
    Path("tests/test_multiscale_engine.py"): 5,
    Path("tests/test_neuromodulation.py"): 3,
    Path("tests/test_observation_and_analysis.py"): 23,
    Path("tests/test_plasticity_protocols.py"): 3,
    Path("tests/test_spiking_population_adapter.py"): 9,
    Path("tests/test_validation_metric_registry_static.py"): 3,
    Path("tests/test_wilson_cowan_network.py"): 4,
}


def _load_pyproject() -> dict[str, object]:
    """Wczytaj konfigurację projektu jako słownik TOML."""
    repo_root = Path(__file__).resolve().parents[1]
    with (repo_root / "pyproject.toml").open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def test_production_docstring_ignores_are_precise() -> None:
    """Produkcyjny kod nie może globalnie ignorować całej rodziny reguł D."""
    pyproject = _load_pyproject()
    per_file_ignores = pyproject["tool"]["ruff"]["lint"]["per-file-ignores"]

    for scope in PRODUCTION_SCOPES_WITHOUT_DOCSTRING_IGNORES:
        assert scope not in per_file_ignores

    for scope in PRODUCTION_DOCSTRING_SCOPES:
        ignored_rules = set(per_file_ignores[scope])
        assert "D" not in ignored_rules
        assert ignored_rules <= {
            "D104",
            "D107",
            "D200",
            "D202",
            "D205",
            "D212",
            "D214",
            "D301",
            "D401",
            "D405",
            "D411",
            "D413",
            "D415",
            "D417",
        }


def test_key_scientific_modules_require_complete_type_annotations() -> None:
    """Kluczowe moduły naukowe muszą zachować zaostrzone reguły mypy."""
    pyproject = _load_pyproject()
    overrides = pyproject["tool"]["mypy"]["overrides"]
    strict_modules: set[str] = set()
    for override in overrides:
        modules = override["module"]
        if isinstance(modules, str):
            modules = [modules]
        if override.get("disallow_untyped_defs") and override.get(
            "disallow_incomplete_defs"
        ):
            strict_modules.update(modules)

    assert STRICT_MYPY_MODULES <= strict_modules


def test_key_scientific_modules_do_not_use_unjustified_any() -> None:
    """Wybrane moduły naukowe nie powinny używać `Any` jako zastępczego typu."""
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for relative_path in STRICT_NO_ANY_PATHS:
        tree = ast.parse((repo_root / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                for alias in node.names:
                    if alias.name == "Any":
                        offenders.append(f"{relative_path}:{node.lineno}: import Any")
            elif isinstance(node, ast.Name) and node.id == "Any":
                offenders.append(f"{relative_path}:{node.lineno}: Any")
            elif isinstance(node, ast.Attribute) and node.attr == "Any":
                offenders.append(f"{relative_path}:{node.lineno}: typing.Any")

    assert not offenders, "Nieuzasadnione użycie Any:\n" + "\n".join(offenders)


def test_test_functions_do_not_add_any_return_annotations() -> None:
    """Testy nie powinny zwiększać liczby funkcji testowych zwracających `Any`."""
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    observed_counts: dict[Path, int] = {}

    for test_path in sorted((repo_root / "tests").glob("test_*.py")):
        relative_path = test_path.relative_to(repo_root)
        tree = ast.parse(test_path.read_text(encoding="utf-8"))
        any_return_lines: list[int] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            return_annotation = node.returns
            if (
                isinstance(return_annotation, ast.Name)
                and return_annotation.id == "Any"
            ):
                any_return_lines.append(node.lineno)
            elif (
                isinstance(return_annotation, ast.Attribute)
                and return_annotation.attr == "Any"
            ):
                any_return_lines.append(node.lineno)
            elif (
                isinstance(return_annotation, ast.Constant)
                and isinstance(return_annotation.value, str)
                and return_annotation.value in ("Any", "typing.Any")
            ):
                any_return_lines.append(node.lineno)

        observed_count = len(any_return_lines)
        if observed_count:
            observed_counts[relative_path] = observed_count

        allowed_count = TEST_ANY_RETURN_BASELINE.get(relative_path, 0)
        if 0 < observed_count < allowed_count:
            offenders.append(
                f"{relative_path}: zaktualizuj limit bazowy -> Any "
                f"z {allowed_count} do {observed_count}"
            )
        if observed_count > allowed_count:
            lines = ", ".join(str(line_number) for line_number in any_return_lines)
            offenders.append(
                f"{relative_path}: {observed_count} adnotacji -> Any "
                f"(limit {allowed_count}; linie: {lines})"
            )

    unexpected_baseline_paths = set(TEST_ANY_RETURN_BASELINE) - {
        path for path in observed_counts if observed_counts[path] > 0
    }
    assert (
        not unexpected_baseline_paths
    ), "Usuń nieaktualne wpisy bazowe -> Any:\n" + "\n".join(
        str(path) for path in sorted(unexpected_baseline_paths)
    )
    assert not offenders, "Nowe adnotacje zwrotu -> Any w testach:\n" + "\n".join(
        offenders
    )
