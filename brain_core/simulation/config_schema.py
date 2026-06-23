"""Schema i walidacja konfiguracji eksperymentu symulacyjnego."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

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
    snn: dict[str, Any] = field(
        default_factory=lambda: {"enabled": False, "circuits": []}
    )
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
    raw: dict[str, Any], *, require_sections: bool = True
) -> ExperimentConfig:
    """Waliduje surową konfigurację i zwraca obiekt `ExperimentConfig`.

    Parameters
    ----------
    raw:
        Surowa konfiguracja odczytana z YAML/JSON.
    require_sections:
        Gdy `True`, wymaga jawnych sekcji docelowego schematu eksperymentu.
        Loader profili klinicznych może ustawić `False`, ponieważ waliduje
        fragment konfiguracji używany jako nakładka.

    Returns
    -------
    ExperimentConfig
        Zweryfikowany obiekt konfiguracji z ujednoliconym `seed` i `rng_seed`.

    Raises
    ------
    ConfigValidationError
        Gdy konfiguracja jest niepoprawna.
    """
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
