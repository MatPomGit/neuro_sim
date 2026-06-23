"""Schema i walidacja konfiguracji eksperymentu symulacyjnego."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Literal

from brain_core.simulation.config_validators.analysis import validate_analysis_config
from brain_core.simulation.config_validators.brain_profile import (
    validate_brain_profile_config,
)
from brain_core.simulation.config_validators.clinical_profile import (
    validate_clinical_profile_config,
)
from brain_core.simulation.config_validators.common import (
    ConfigValidationError,
    require_mapping,
    require_non_negative_int,
    require_positive_number,
)
from brain_core.simulation.config_validators.connectome import (
    validate_connectome_config,
)
from brain_core.simulation.config_validators.integrator import (
    validate_integrator_config,
)
from brain_core.simulation.config_validators.model import validate_model_config
from brain_core.simulation.config_validators.output import validate_output_config
from brain_core.simulation.config_validators.pathology import validate_pathology_config
from brain_core.simulation.config_validators.snn import validate_snn_config
from brain_core.simulation.config_validators.stimulus import validate_stimulus_config
from brain_core.simulation.config_validators.task import validate_task_config

ValidationSeverity = Literal["error"]


REQUIRED_CONFIG_SECTIONS = (
    "model",
    "integrator",
    "task",
    "stimulus",
    "brain_profile",
    "clinical_profile",
    "connectome",
    "pathology",
    "snn",
    "analysis",
    "output",
)


@dataclass(frozen=True)
class ConfigValidationIssue:
    """Opis pojedynczego problemu wykrytego podczas walidacji konfiguracji.

    Parameters
    ----------
    field_path:
        Ścieżka pola konfiguracji, którego dotyczy problem.
    message:
        Czytelny komunikat po polsku opisujący naruszenie kontraktu schematu.
    severity:
        Poziom ważności problemu; obecnie walidacja konfiguracji raportuje
        błędy blokujące uruchomienie eksperymentu.
    """

    field_path: str
    message: str
    severity: ValidationSeverity = "error"


@dataclass
class ExperimentConfig:
    """Ujednolicony obiekt konfiguracji eksperymentu po walidacji.

    Parameters
    ----------
    model:
        Parametry modelu masowego lub poznawczego.
    integrator:
        Parametry integratora numerycznego.
    timestep:
        Krok czasowy symulacji w sekundach.
    seed:
        Historyczne pole ziarna generatora losowego zachowane dla zgodności.
    rng_seed:
        Docelowe pole ziarna generatora losowego; po walidacji jest zgodne z
        `seed`.
    task:
        Parametry zadania eksperymentalnego.
    stimulus:
        Jawna sekcja parametrów bodźców i prezentacji.
    brain_profile:
        Jawna sekcja bazowego profilu mózgu bez interpretacji klinicznej.
    clinical_profile:
        Metadane profilu klinicznego wykorzystywane w raportach porównań.
    connectome:
        Parametry atlasu i macierzy połączeń strukturalnych.
    pathology:
        Konfiguracja patologii lub uszkodzeń.
    snn:
        Parametry współsymulacji SNN.
    analysis:
        Lista zestawów analiz po symulacji.
    output:
        Parametry zapisu artefaktów eksperymentu.
    """

    model: dict[str, Any] = field(default_factory=dict)
    integrator: dict[str, Any] = field(default_factory=lambda: {"method": "euler"})
    timestep: float = 0.005
    seed: int = 7
    rng_seed: int | None = None
    task: dict[str, Any] = field(
        default_factory=lambda: {"scenario": "reward-learning", "duration": 45.0}
    )
    stimulus: dict[str, Any] = field(
        default_factory=lambda: {"scenario": "reward-learning", "source": "task"}
    )
    brain_profile: dict[str, Any] = field(default_factory=lambda: {"id": "default"})
    clinical_profile: dict[str, Any] = field(
        default_factory=lambda: {
            "id": "healthy_v1",
            "display_name": "Zdrowy profil bazowy v1",
            "mechanism": "Brak jawnie modelowanej patologii klinicznej.",
            "affected_regions": [],
            "cognitive_functions": [],
            "expected_effects": {},
            "expected_direction": "stable_reference",
            "severity_level": {"small": 0.0, "medium": 0.02, "large": 0.05},
            "primary_metric": "mean_abs_difference",
            "tolerance": {
                "absolute": 0.005,
                "relative": 0.0,
                "unit": "mean_abs_difference",
            },
            "applicability_scope": (
                "Porównania regresyjne profilu referencyjnego przy stałym seedzie."
            ),
            "benchmark_source": (
                "Syntetyczny profil bazowy utrzymywany w repozytorium; brak "
                "źródła klinicznego, ponieważ nie reprezentuje danych pacjentów."
            ),
            "amplitude_latency_mechanism": {
                "expected_amplitude_direction": "stable_reference",
                "expected_readaptation_direction": "stable_reference",
                "qualitative_threshold": 0.05,
                "mechanism_comment": "Profil referencyjny bez patologii.",
                "educational_comment": (
                    "Punkt odniesienia do porównań amplitudy proxy i latencji readaptacji."
                ),
            },
        }
    )
    connectome: dict[str, Any] = field(
        default_factory=lambda: {
            "atlas": "default_regions",
            "weights": "data/connectomes/weights.csv",
            "fiber_lengths": "data/connectomes/fiber_lengths.csv",
        }
    )
    pathology: dict[str, Any] = field(
        default_factory=lambda: {"enabled": False, "mutations": [], "scenario": None}
    )
    snn: dict[str, Any] = field(default_factory=lambda: {"enabled": False, "circuits": []})
    analysis: dict[str, Any] = field(
        default_factory=lambda: {
            "sets": ["spectral", "phase_locking", "connectivity", "information_flow"],
            "max_report_trials": 20,
            "include_full_trial_table": True,
        }
    )
    output: dict[str, Any] = field(
        default_factory=lambda: {
            "save_results": True,
            "label": "run",
            "output_dir": "outputs",
        }
    )


def validate_config(
    raw: dict[str, Any], *, require_sections: bool = True, collect_errors: bool = False
) -> ExperimentConfig | list[ConfigValidationIssue]:
    """Waliduje surową konfigurację i zwraca obiekt `ExperimentConfig`.

    Parameters
    ----------
    raw:
        Surowa konfiguracja odczytana z YAML/JSON.
    require_sections:
        Gdy `True`, wymaga jawnych sekcji docelowego schematu eksperymentu.
        Loader profili klinicznych może ustawić `False`, ponieważ waliduje
        fragment konfiguracji używany jako nakładka.
    collect_errors:
        Gdy `True`, zbiera problemy walidacji z wielu sekcji i zwraca listę
        `ConfigValidationIssue` bez przerywania po pierwszym błędzie.

    Returns
    -------
    ExperimentConfig | list[ConfigValidationIssue]
        Zweryfikowany obiekt konfiguracji z ujednoliconym `seed` i `rng_seed`
        albo lista problemów, gdy włączono `collect_errors`.

    Raises
    ------
    ConfigValidationError
        Gdy konfiguracja jest niepoprawna.
    """
    if collect_errors:
        return collect_config_validation_issues(raw, require_sections=require_sections)

    if not isinstance(raw, dict):
        raise ConfigValidationError("Konfiguracja musi być obiektem mapującym (dict).")

    if require_sections:
        _require_top_level_sections(raw)

    normalized_raw = _normalize_seed_fields(raw)
    cfg = ExperimentConfig(
        **{
            key: value
            for key, value in normalized_raw.items()
            if key in ExperimentConfig.__dataclass_fields__
        }
    )

    cfg.model = require_mapping(cfg.model, "model")
    cfg.integrator = require_mapping(cfg.integrator, "integrator")
    cfg.task = require_mapping(cfg.task, "task")
    cfg.stimulus = require_mapping(cfg.stimulus, "stimulus")
    cfg.brain_profile = require_mapping(cfg.brain_profile, "brain_profile")
    cfg.clinical_profile = require_mapping(cfg.clinical_profile, "clinical_profile")
    cfg.connectome = require_mapping(cfg.connectome, "connectome")
    cfg.pathology = require_mapping(cfg.pathology, "pathology")
    cfg.snn = require_mapping(cfg.snn, "snn")
    cfg.analysis = require_mapping(cfg.analysis, "analysis")
    cfg.output = require_mapping(cfg.output, "output")

    cfg.timestep = require_positive_number(cfg.timestep, "timestep")
    cfg.seed = require_non_negative_int(cfg.seed, "seed")
    if cfg.rng_seed is None:
        cfg.rng_seed = cfg.seed
    cfg.rng_seed = require_non_negative_int(cfg.rng_seed, "rng_seed")

    cfg.integrator = validate_integrator_config(cfg.integrator)
    cfg.model = validate_model_config(cfg.model)
    cfg.task = validate_task_config(cfg.task)
    cfg.stimulus = validate_stimulus_config(cfg.stimulus)
    cfg.brain_profile = validate_brain_profile_config(cfg.brain_profile)
    cfg.connectome = validate_connectome_config(cfg.connectome)
    cfg.pathology = validate_pathology_config(cfg.pathology)
    cfg.clinical_profile = validate_clinical_profile_config(
        cfg.clinical_profile, require_tolerance=not require_sections
    )
    cfg.snn = validate_snn_config(cfg.snn, cfg.timestep)
    cfg.analysis = validate_analysis_config(cfg.analysis)
    cfg.output = validate_output_config(cfg.output)
    return cfg


def collect_config_validation_issues(
    raw: dict[str, Any], *, require_sections: bool = True
) -> list[ConfigValidationIssue]:
    """Zbierz problemy walidacji konfiguracji bez przerywania po pierwszym błędzie.

    Parameters
    ----------
    raw:
        Surowa konfiguracja odczytana z YAML/JSON.
    require_sections:
        Gdy `True`, raportuje brak jawnych sekcji docelowego schematu
        eksperymentu oraz wymaganych pól `seed`/`rng_seed` i `timestep`.

    Returns
    -------
    list[ConfigValidationIssue]
        Lista błędów blokujących poprawne uruchomienie eksperymentu. Pusta
        lista oznacza, że konfiguracja przechodzi tę samą ścieżkę walidacji co
        domyślny tryb `validate_config`.
    """
    issues: list[ConfigValidationIssue] = []
    if not isinstance(raw, dict):
        return [
            ConfigValidationIssue(
                field_path="<root>",
                message="Konfiguracja musi być obiektem mapującym (dict).",
            )
        ]

    if require_sections:
        issues.extend(_collect_required_section_issues(raw))

    try:
        normalized_raw = _normalize_seed_fields(raw)
    except ConfigValidationError as exc:
        issues.append(_issue_from_error(exc))
        normalized_raw = deepcopy(raw)

    cfg = ExperimentConfig(
        **{
            key: value
            for key, value in normalized_raw.items()
            if key in ExperimentConfig.__dataclass_fields__
        }
    )

    section_names = (
        "model",
        "integrator",
        "task",
        "stimulus",
        "brain_profile",
        "clinical_profile",
        "connectome",
        "pathology",
        "snn",
        "analysis",
        "output",
    )
    for section_name in section_names:
        try:
            setattr(cfg, section_name, require_mapping(getattr(cfg, section_name), section_name))
        except ConfigValidationError as exc:
            issues.append(_issue_from_error(exc))
            setattr(cfg, section_name, {})

    validated_timestep = ExperimentConfig().timestep
    try:
        cfg.timestep = require_positive_number(cfg.timestep, "timestep")
        validated_timestep = cfg.timestep
    except ConfigValidationError as exc:
        issues.append(_issue_from_error(exc))
    _collect_scalar_seed_issues(cfg, issues)

    section_validators: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
        ("integrator", lambda: validate_integrator_config(cfg.integrator)),
        ("model", lambda: validate_model_config(cfg.model)),
        ("task", lambda: validate_task_config(cfg.task)),
        ("stimulus", lambda: validate_stimulus_config(cfg.stimulus)),
        ("brain_profile", lambda: validate_brain_profile_config(cfg.brain_profile)),
        ("connectome", lambda: validate_connectome_config(cfg.connectome)),
        ("pathology", lambda: validate_pathology_config(cfg.pathology)),
        (
            "clinical_profile",
            lambda: validate_clinical_profile_config(
                cfg.clinical_profile, require_tolerance=not require_sections
            ),
        ),
        ("snn", lambda: validate_snn_config(cfg.snn, validated_timestep)),
        ("analysis", lambda: validate_analysis_config(cfg.analysis)),
        ("output", lambda: validate_output_config(cfg.output)),
    )
    for section_name, validate_section in section_validators:
        try:
            setattr(cfg, section_name, validate_section())
        except ConfigValidationError as exc:
            issues.append(_issue_from_error(exc, fallback_field_path=section_name))

    return issues


def _collect_required_section_issues(raw: dict[str, Any]) -> list[ConfigValidationIssue]:
    """Zbierz braki wymaganych sekcji najwyższego poziomu konfiguracji."""
    issues = [
        ConfigValidationIssue(
            field_path=section_name,
            message=f"Brak wymaganej sekcji {section_name}",
        )
        for section_name in REQUIRED_CONFIG_SECTIONS
        if section_name not in raw
    ]
    if "rng_seed" not in raw and "seed" not in raw:
        issues.append(
            ConfigValidationIssue(
                field_path="rng_seed",
                message="Brak wymaganego pola rng_seed albo seed",
            )
        )
    if "timestep" not in raw:
        issues.append(
            ConfigValidationIssue(
                field_path="timestep",
                message="Brak wymaganego pola timestep",
            )
        )
    return issues


def _collect_scalar_seed_issues(cfg: ExperimentConfig, issues: list[ConfigValidationIssue]) -> None:
    """Dopisz problemy walidacji pól ziarna losowości do listy błędów."""
    try:
        cfg.seed = require_non_negative_int(cfg.seed, "seed")
    except ConfigValidationError as exc:
        issues.append(_issue_from_error(exc))
        cfg.seed = 7
    if cfg.rng_seed is None:
        cfg.rng_seed = cfg.seed
    try:
        cfg.rng_seed = require_non_negative_int(cfg.rng_seed, "rng_seed")
    except ConfigValidationError as exc:
        issues.append(_issue_from_error(exc))


def _issue_from_error(
    error: ConfigValidationError, *, fallback_field_path: str = "<root>"
) -> ConfigValidationIssue:
    """Zamień wyjątek walidacji na strukturalny opis problemu konfiguracji."""
    message = str(error)
    return ConfigValidationIssue(
        field_path=_field_path_from_message(message, fallback_field_path),
        message=message,
    )


def _field_path_from_message(message: str, fallback_field_path: str) -> str:
    """Wyznacz najlepszą ścieżkę pola na podstawie istniejącego komunikatu błędu."""
    if message.startswith("Brak pola "):
        return message.removeprefix("Brak pola ").split()[0]
    if message.startswith("Brak wymaganej sekcji "):
        return message.removeprefix("Brak wymaganej sekcji ").split()[0]
    if message.startswith("Brak wymaganego pola "):
        return message.removeprefix("Brak wymaganego pola ").split()[0]
    for token in message.split():
        clean_token = token.strip(",;:()[]{}'\"")
        if "." in clean_token or clean_token in REQUIRED_CONFIG_SECTIONS:
            return clean_token
    return fallback_field_path


def _require_top_level_sections(raw: dict[str, Any]) -> None:
    """Sprawdza obecność jawnych sekcji docelowego schematu konfiguracji."""
    for section_name in REQUIRED_CONFIG_SECTIONS:
        if section_name not in raw:
            raise ConfigValidationError(f"Brak wymaganej sekcji {section_name}")
    if "rng_seed" not in raw and "seed" not in raw:
        raise ConfigValidationError("Brak wymaganego pola rng_seed albo seed")
    if "timestep" not in raw:
        raise ConfigValidationError("Brak wymaganego pola timestep")


def _normalize_seed_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Migruje `seed` i `rng_seed` do jednej jawnej semantyki losowości."""
    normalized = deepcopy(raw)
    has_seed = "seed" in normalized
    has_rng_seed = "rng_seed" in normalized

    if has_seed and has_rng_seed and normalized["seed"] != normalized["rng_seed"]:
        raise ConfigValidationError(
            "Pola seed i rng_seed wskazują różne wartości; ustaw jedną wartość "
            "albo usuń historyczne pole seed."
        )
    if has_rng_seed:
        normalized["seed"] = normalized["rng_seed"]
    elif has_seed:
        normalized["rng_seed"] = normalized["seed"]
    return normalized
