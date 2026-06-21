"""Schema i walidacja konfiguracji eksperymentu symulacyjnego."""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain_core.data_contracts import (
    CONTRACT_B_NETWORKS_POPULATIONS,
    validate_delay_steps_contract,
    validate_regional_vector_contract,
    validate_square_matrix_contract,
)
from brain_core.simulation.signal_adapter import (
    ALLOWED_SNN_COUPLING_MODES,
    DEMO_SNN_REGION_NAME,
    SNNPopulationMapping,
)

ALLOWED_CLINICAL_PROFILE_IDS = {
    "healthy_v1",
    "dopamine_deficit",
    "gaba_dysregulation",
    "serotonin_imbalance",
    "hippocampal_lesion",
    "dlpfc_weakening",
}

ALLOWED_CLINICAL_PROFILE_KEYS = {
    "id",
    "display_name",
    "mechanism",
    "affected_regions",
    "cognitive_functions",
    "expected_effects",
    "expected_direction",
    "severity_level",
    "primary_metric",
    "tolerance",
    "applicability_scope",
    "benchmark_source",
    "amplitude_latency_mechanism",
}

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
                    "Punkt odniesienia do porównań amplitudy proxy i latencji "
                    "readaptacji."
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


class ConfigValidationError(ValueError):
    """Błąd walidacji konfiguracji eksperymentu."""


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

    cfg.model = _require_mapping(cfg.model, "model")
    cfg.integrator = _require_mapping(cfg.integrator, "integrator")
    cfg.task = _require_mapping(cfg.task, "task")
    cfg.stimulus = _require_mapping(cfg.stimulus, "stimulus")
    cfg.brain_profile = _require_mapping(cfg.brain_profile, "brain_profile")
    cfg.clinical_profile = _require_mapping(cfg.clinical_profile, "clinical_profile")
    cfg.connectome = _require_mapping(cfg.connectome, "connectome")
    cfg.pathology = _require_mapping(cfg.pathology, "pathology")
    cfg.snn = _require_mapping(cfg.snn, "snn")
    cfg.analysis = _require_mapping(cfg.analysis, "analysis")
    cfg.output = _require_mapping(cfg.output, "output")

    cfg.timestep = _require_positive_number(cfg.timestep, "timestep")
    cfg.seed = _require_non_negative_int(cfg.seed, "seed")
    if cfg.rng_seed is None:
        cfg.rng_seed = cfg.seed
    cfg.rng_seed = _require_non_negative_int(cfg.rng_seed, "rng_seed")

    _validate_integrator_config(cfg)
    _validate_model_config(cfg)
    _validate_task_config(cfg)
    _validate_stimulus_config(cfg)
    _validate_brain_profile_config(cfg)
    _validate_connectome_config(cfg)
    _validate_pathology_config(cfg)
    _validate_clinical_profile_config(cfg)
    _validate_snn_config(cfg)
    _validate_analysis_config(cfg)
    _validate_output_config(cfg)
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


def _require_mapping(value: Any, field_path: str) -> dict[str, Any]:
    """Wymaga obiektu mapującego dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, dict):
        raise ConfigValidationError(f"{field_path} musi być obiektem")
    return dict(value)


def _require_bool(value: Any, field_path: str) -> bool:
    """Wymaga wartości logicznej dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, bool):
        raise ConfigValidationError(f"{field_path} musi być wartością logiczną")
    return value


def _require_non_empty_string(value: Any, field_path: str) -> str:
    """Wymaga niepustego tekstu dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"{field_path} musi być niepustym tekstem")
    return value.strip()


def _require_number(value: Any, field_path: str) -> float:
    """Wymaga skończonej liczby dla wskazanej ścieżki konfiguracji."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigValidationError(f"{field_path} musi być liczbą")
    number = float(value)
    if not math.isfinite(number):
        raise ConfigValidationError(f"{field_path} musi być liczbą skończoną")
    return number


def _require_positive_number(value: Any, field_path: str) -> float:
    """Wymaga dodatniej skończonej liczby dla wskazanej ścieżki konfiguracji."""
    number = _require_number(value, field_path)
    if number <= 0:
        raise ConfigValidationError(f"{field_path} musi być > 0")
    return number


def _require_non_negative_int(value: Any, field_path: str) -> int:
    """Wymaga nieujemnej liczby całkowitej dla wskazanej ścieżki konfiguracji."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"{field_path} musi być liczbą całkowitą")
    if value < 0:
        raise ConfigValidationError(f"{field_path} musi być >= 0")
    return int(value)


def _require_list(value: Any, field_path: str) -> list[Any]:
    """Wymaga listy dla wskazanej ścieżki konfiguracji."""
    if not isinstance(value, list):
        raise ConfigValidationError(f"{field_path} musi być listą")
    return list(value)


def _coerce_string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    """Normalizuje listę nazw regionów SNN do krotki niepustych tekstów."""
    values = _require_list(value, field_name)
    if not all(isinstance(item, str) and item.strip() for item in values):
        raise ConfigValidationError(f"{field_name} musi być listą niepustych tekstów")
    return tuple(str(item).strip() for item in values)


def _validate_model_config(cfg: ExperimentConfig) -> None:
    """Waliduje opcjonalne macierze regionalne modelu względem kontraktu B.

    Parameters
    ----------
    cfg:
        Konfiguracja eksperymentu po podstawowym sprawdzeniu typów sekcji.

    Raises
    ------
    ConfigValidationError
        Gdy lista regionów, konektywność, opóźnienia albo napędy regionalne
        mają kształt niezgodny z kontraktem danych.
    """
    if "regions" not in cfg.model:
        return

    regions = _coerce_string_tuple(cfg.model["regions"], "model.regions")
    if not regions:
        raise ConfigValidationError(
            "Kontrakt B: `networks` → `populations`: model.regions nie może być puste"
        )
    if len(set(regions)) != len(regions):
        raise ConfigValidationError(
            "Kontrakt B: `networks` → `populations`: model.regions musi być unikalne"
        )
    cfg.model["regions"] = list(regions)
    n_regions = len(regions)

    if "connectivity" in cfg.model:
        try:
            connectivity = validate_square_matrix_contract(
                cfg.model["connectivity"],
                n_regions,
                "model.connectivity",
                CONTRACT_B_NETWORKS_POPULATIONS,
            )
        except ValueError as error:
            raise ConfigValidationError(str(error)) from error
        cfg.model["connectivity"] = connectivity.tolist()

    if "delays_steps" in cfg.model:
        try:
            delays_steps = validate_delay_steps_contract(
                cfg.model["delays_steps"], n_regions
            )
        except ValueError as error:
            raise ConfigValidationError(str(error)) from error
        cfg.model["delays_steps"] = delays_steps.tolist()

    for vector_field in ("external_drive_E", "external_drive_I"):
        if vector_field in cfg.model:
            try:
                vector = validate_regional_vector_contract(
                    cfg.model[vector_field], n_regions, f"model.{vector_field}"
                )
            except ValueError as error:
                raise ConfigValidationError(str(error)) from error
            cfg.model[vector_field] = vector.tolist()


def _validate_integrator_config(cfg: ExperimentConfig) -> None:
    """Waliduje parametry integratora numerycznego."""
    if "method" not in cfg.integrator:
        raise ConfigValidationError("Brak pola integrator.method")
    method = _require_non_empty_string(cfg.integrator["method"], "integrator.method")
    if method != "euler":
        raise ConfigValidationError("integrator.method aktualnie wspiera tylko 'euler'")
    cfg.integrator["method"] = method
    if "oscillator" in cfg.integrator:
        cfg.integrator["oscillator"] = _require_mapping(
            cfg.integrator["oscillator"], "integrator.oscillator"
        )


def _validate_task_config(cfg: ExperimentConfig) -> None:
    """Waliduje parametry zadania eksperymentalnego."""
    if "scenario" not in cfg.task:
        raise ConfigValidationError("Brak pola task.scenario")
    cfg.task["scenario"] = _require_non_empty_string(
        cfg.task["scenario"], "task.scenario"
    )
    if "duration" not in cfg.task:
        raise ConfigValidationError("Brak pola task.duration")
    cfg.task["duration"] = _require_positive_number(
        cfg.task["duration"], "task.duration"
    )
    if "name" in cfg.task:
        cfg.task["name"] = _require_non_empty_string(cfg.task["name"], "task.name")
    for int_field in ("n_runs", "run_length_min", "run_length_max", "n"):
        if int_field in cfg.task:
            cfg.task[int_field] = _require_non_negative_int(
                cfg.task[int_field], f"task.{int_field}"
            )
    for number_field in ("deviant_probability", "inter_stimulus_interval", "jitter"):
        if number_field in cfg.task:
            cfg.task[number_field] = _require_number(
                cfg.task[number_field], f"task.{number_field}"
            )


def _validate_stimulus_config(cfg: ExperimentConfig) -> None:
    """Waliduje wymaganą sekcję bodźców eksperymentalnych."""
    for text_field in ("scenario", "source"):
        if text_field not in cfg.stimulus:
            raise ConfigValidationError(f"Brak pola stimulus.{text_field}")
        cfg.stimulus[text_field] = _require_non_empty_string(
            cfg.stimulus[text_field], f"stimulus.{text_field}"
        )


def _validate_brain_profile_config(cfg: ExperimentConfig) -> None:
    """Waliduje bazowy profil mózgu niezależny od profilu klinicznego."""
    if "id" not in cfg.brain_profile:
        raise ConfigValidationError("Brak pola brain_profile.id")
    cfg.brain_profile["id"] = _require_non_empty_string(
        cfg.brain_profile["id"], "brain_profile.id"
    )
    if "description" in cfg.brain_profile:
        cfg.brain_profile["description"] = _require_non_empty_string(
            cfg.brain_profile["description"], "brain_profile.description"
        )


def _validate_connectome_config(cfg: ExperimentConfig) -> None:
    """Waliduje sekcję atlasu i macierzy connectome."""
    if "atlas" not in cfg.connectome:
        raise ConfigValidationError("Brak pola connectome.atlas")
    cfg.connectome["atlas"] = _require_non_empty_string(
        cfg.connectome["atlas"], "connectome.atlas"
    )
    for text_field in ("weights", "fiber_lengths"):
        if text_field in cfg.connectome and cfg.connectome[text_field] is not None:
            cfg.connectome[text_field] = _require_non_empty_string(
                cfg.connectome[text_field], f"connectome.{text_field}"
            )


def _validate_amplitude_latency_mechanism_config(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Waliduje opis mechanizmu amplituda-latencja dla raportu roving oddball.

    Parameters
    ----------
    profile:
        Sekcja ``clinical_profile`` po podstawowej walidacji pól tekstowych.

    Returns
    -------
    dict[str, Any]
        Znormalizowane metadane sekcji raportowej.

    Raises
    ------
    ConfigValidationError
        Gdy sekcja ma niepoprawny typ, brakuje wymaganych pól albo próg nie
        jest dodatnią liczbą.
    """
    mechanism = profile.get("amplitude_latency_mechanism")
    if mechanism is None:
        mechanism = {
            "expected_amplitude_direction": profile.get(
                "expected_direction", "stable_reference"
            ),
            "expected_readaptation_direction": "stable_reference",
            "qualitative_threshold": 0.05,
            "mechanism_comment": profile.get("mechanism", "n/a"),
            "educational_comment": (
                "Brak dedykowanego opisu w konfiguracji; raport używa ogólnego "
                "mechanizmu profilu klinicznego."
            ),
        }
    if not isinstance(mechanism, dict):
        raise ConfigValidationError(
            "clinical_profile.amplitude_latency_mechanism musi być obiektem"
        )

    required_text_keys = (
        "expected_amplitude_direction",
        "expected_readaptation_direction",
        "mechanism_comment",
        "educational_comment",
    )
    normalized = dict(mechanism)
    for text_key in required_text_keys:
        if text_key not in normalized:
            raise ConfigValidationError(
                f"Brak pola clinical_profile.amplitude_latency_mechanism.{text_key}"
            )
        value = normalized[text_key]
        if not isinstance(value, str) or not value.strip():
            raise ConfigValidationError(
                "clinical_profile.amplitude_latency_mechanism."
                f"{text_key} musi być tekstem"
            )
        normalized[text_key] = value.strip()

    if "qualitative_threshold" not in normalized:
        raise ConfigValidationError(
            "Brak pola clinical_profile.amplitude_latency_mechanism."
            "qualitative_threshold"
        )
    normalized["qualitative_threshold"] = _require_number(
        normalized["qualitative_threshold"],
        "clinical_profile.amplitude_latency_mechanism.qualitative_threshold",
    )
    if normalized["qualitative_threshold"] < 0.0:
        raise ConfigValidationError(
            "clinical_profile.amplitude_latency_mechanism.qualitative_threshold "
            "musi być >= 0"
        )
    return normalized


def _validate_pathology_config(cfg: ExperimentConfig) -> None:
    """Waliduje konfigurację patologii i mutacji stanu symulacji."""
    if "enabled" not in cfg.pathology:
        raise ConfigValidationError("Brak pola pathology.enabled")
    cfg.pathology["enabled"] = _require_bool(
        cfg.pathology["enabled"], "pathology.enabled"
    )
    mutations = cfg.pathology.get("mutations", [])
    cfg.pathology["mutations"] = _require_list(mutations, "pathology.mutations")
    scenario = cfg.pathology.get("scenario")
    if scenario is not None:
        cfg.pathology["scenario"] = _require_non_empty_string(
            scenario, "pathology.scenario"
        )
    for idx, mutation in enumerate(cfg.pathology["mutations"]):
        mutation_path = f"pathology.mutations[{idx}]"
        mutation_config = _require_mapping(mutation, mutation_path)
        for required_key in ("kind", "scope", "target"):
            if required_key not in mutation_config:
                raise ConfigValidationError(f"Brak pola {mutation_path}.{required_key}")
            mutation_config[required_key] = _require_non_empty_string(
                mutation_config[required_key], f"{mutation_path}.{required_key}"
            )
        cfg.pathology["mutations"][idx] = mutation_config


def _validate_clinical_profile_config(cfg: ExperimentConfig) -> None:
    """Waliduje metadane profilu klinicznego ładowanego z konfiguracji."""
    profile_id = cfg.clinical_profile.get("id", "healthy_v1")
    if profile_id not in ALLOWED_CLINICAL_PROFILE_IDS:
        allowed = sorted(ALLOWED_CLINICAL_PROFILE_IDS)
        raise ConfigValidationError(
            f"Nieznany clinical_profile.id: {profile_id}. Dozwolone: {allowed}"
        )

    unknown_keys = sorted(
        key for key in cfg.clinical_profile if key not in ALLOWED_CLINICAL_PROFILE_KEYS
    )
    if unknown_keys:
        raise ConfigValidationError(f"Nieznane pola clinical_profile: {unknown_keys}")

    for text_key in (
        "display_name",
        "mechanism",
        "applicability_scope",
        "benchmark_source",
    ):
        if text_key not in cfg.clinical_profile:
            raise ConfigValidationError(f"Brak pola clinical_profile.{text_key}")
        value = cfg.clinical_profile[text_key]
        if not isinstance(value, str) or not value.strip():
            raise ConfigValidationError(f"clinical_profile.{text_key} musi być tekstem")

    for list_key in ("affected_regions", "cognitive_functions"):
        value = cfg.clinical_profile.get(list_key, [])
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ConfigValidationError(
                f"clinical_profile.{list_key} musi być listą tekstów"
            )

    expected_effects = cfg.clinical_profile.get("expected_effects", {})
    if not isinstance(expected_effects, dict):
        raise ConfigValidationError(
            "clinical_profile.expected_effects musi być obiektem"
        )

    expected_direction = cfg.clinical_profile.get(
        "expected_direction", "stable_reference"
    )
    if not isinstance(expected_direction, str) or not expected_direction.strip():
        raise ConfigValidationError(
            "clinical_profile.expected_direction musi być tekstem"
        )

    primary_metric = cfg.clinical_profile.get("primary_metric", "mean_abs_difference")
    if primary_metric not in {"mean_abs_difference", "max_abs_difference"}:
        raise ConfigValidationError(
            "clinical_profile.primary_metric musi mieć wartość "
            "'mean_abs_difference' albo 'max_abs_difference'"
        )

    severity_level = cfg.clinical_profile.get(
        "severity_level", {"small": 0.0, "medium": 0.02, "large": 0.05}
    )
    if not isinstance(severity_level, dict):
        raise ConfigValidationError(
            "clinical_profile.severity_level musi być obiektem z progami"
        )
    for threshold_name in ("small", "medium", "large"):
        if threshold_name not in severity_level:
            raise ConfigValidationError(
                f"Brak progu clinical_profile.severity_level.{threshold_name}"
            )
        severity_level[threshold_name] = _require_number(
            severity_level[threshold_name],
            f"clinical_profile.severity_level.{threshold_name}",
        )
    if not (
        severity_level["small"] <= severity_level["medium"] <= severity_level["large"]
    ):
        raise ConfigValidationError(
            "Progi clinical_profile.severity_level muszą spełniać "
            "small <= medium <= large"
        )

    tolerance = cfg.clinical_profile.get("tolerance")
    if not isinstance(tolerance, dict):
        raise ConfigValidationError(
            "clinical_profile.tolerance musi być obiektem z polami absolute, "
            "relative i unit"
        )
    for tolerance_key in ("absolute", "relative"):
        if tolerance_key not in tolerance:
            raise ConfigValidationError(
                f"Brak pola clinical_profile.tolerance.{tolerance_key}"
            )
        tolerance[tolerance_key] = _require_number(
            tolerance[tolerance_key], f"clinical_profile.tolerance.{tolerance_key}"
        )
        if tolerance[tolerance_key] < 0.0:
            raise ConfigValidationError(
                f"clinical_profile.tolerance.{tolerance_key} musi być >= 0"
            )
    if "unit" not in tolerance:
        raise ConfigValidationError("Brak pola clinical_profile.tolerance.unit")
    tolerance["unit"] = _require_non_empty_string(
        tolerance["unit"], "clinical_profile.tolerance.unit"
    )

    cfg.clinical_profile["id"] = str(profile_id)
    cfg.clinical_profile["display_name"] = cfg.clinical_profile["display_name"].strip()
    cfg.clinical_profile["mechanism"] = cfg.clinical_profile["mechanism"].strip()
    cfg.clinical_profile["applicability_scope"] = cfg.clinical_profile[
        "applicability_scope"
    ].strip()
    cfg.clinical_profile["benchmark_source"] = cfg.clinical_profile[
        "benchmark_source"
    ].strip()
    cfg.clinical_profile["affected_regions"] = list(
        cfg.clinical_profile.get("affected_regions", [])
    )
    cfg.clinical_profile["cognitive_functions"] = list(
        cfg.clinical_profile.get("cognitive_functions", [])
    )
    cfg.clinical_profile["expected_effects"] = dict(expected_effects)
    cfg.clinical_profile["expected_direction"] = expected_direction.strip()
    cfg.clinical_profile["primary_metric"] = str(primary_metric)
    cfg.clinical_profile["severity_level"] = dict(severity_level)
    cfg.clinical_profile["tolerance"] = dict(tolerance)
    cfg.clinical_profile["amplitude_latency_mechanism"] = (
        _validate_amplitude_latency_mechanism_config(cfg.clinical_profile)
    )


def _validate_snn_config(cfg: ExperimentConfig) -> None:
    """Waliduje sekcję konfiguracji współsymulacji SNN."""
    if "enabled" not in cfg.snn:
        raise ConfigValidationError("Brak pola snn.enabled")
    cfg.snn["enabled"] = _require_bool(cfg.snn["enabled"], "snn.enabled")
    circuits = _require_list(cfg.snn.get("circuits", []), "snn.circuits")

    circuit_regions: list[str] = []
    for idx, circuit in enumerate(circuits):
        if not isinstance(circuit, dict):
            raise ConfigValidationError(f"snn.circuits[{idx}] musi być obiektem")
        region = circuit.get("region")
        if not isinstance(region, str) or not region.strip():
            raise ConfigValidationError(f"Brak pola snn.circuits[{idx}].region")
        circuit["region"] = region.strip()
        circuit_regions.append(circuit["region"])

    if len(circuit_regions) != len(set(circuit_regions)):
        raise ConfigValidationError("snn.circuits.region musi zawierać unikalne nazwy")
    if circuit_regions and circuit_regions != [DEMO_SNN_REGION_NAME]:
        raise ConfigValidationError(
            "Bieżący pilotaż SNN obsługuje dokładnie jeden obwód "
            f"demonstracyjny: {DEMO_SNN_REGION_NAME}"
        )
    for idx, circuit in enumerate(circuits):
        backend = str(circuit.get("backend", "brian2"))
        if backend != "brian2":
            raise ConfigValidationError(
                f"snn.circuits[{idx}].backend musi mieć wartość 'brian2' "
                "w bieżącym pilotażu"
            )
        circuit["backend"] = backend

    sync_dt_val = cfg.snn.get("sync_dt")
    if sync_dt_val is None:
        sync_dt = cfg.timestep
    else:
        sync_dt = _require_positive_number(sync_dt_val, "snn.sync_dt")

    ratio = sync_dt / cfg.timestep
    if abs(round(ratio) - ratio) > 1e-9:
        raise ConfigValidationError("snn.sync_dt musi być wielokrotnością timestep")

    coupling_mode = str(cfg.snn.get("mode", "report_only"))
    if coupling_mode not in ALLOWED_SNN_COUPLING_MODES:
        allowed_modes = ", ".join(ALLOWED_SNN_COUPLING_MODES)
        raise ConfigValidationError(
            f"snn.mode musi mieć jedną z wartości: {allowed_modes}"
        )

    max_feedback_amplitude = _require_positive_number(
        cfg.snn.get("max_feedback_amplitude", 0.15), "snn.max_feedback_amplitude"
    )

    input_rate_unit = str(cfg.snn.get("input_rate_unit", "Hz"))
    output_activity_unit = str(cfg.snn.get("output_activity_unit", "fraction"))
    if input_rate_unit != "Hz":
        raise ConfigValidationError("snn.input_rate_unit musi mieć wartość 'Hz'")
    if output_activity_unit != "fraction":
        raise ConfigValidationError(
            "snn.output_activity_unit musi mieć wartość 'fraction'"
        )

    neural_mass_regions_value = cfg.snn.get("neural_mass_regions")
    if neural_mass_regions_value is not None:
        neural_mass_regions = _coerce_string_tuple(
            neural_mass_regions_value, "snn.neural_mass_regions"
        )
        try:
            SNNPopulationMapping(
                snn_region_names=tuple(circuit_regions),
                neural_mass_region_names=neural_mass_regions,
            ).indices_in_neural_mass()
        except ValueError as exc:
            raise ConfigValidationError(str(exc)) from exc
        cfg.snn["neural_mass_regions"] = list(neural_mass_regions)

    cfg.snn["circuits"] = circuits
    cfg.snn["mode"] = coupling_mode
    cfg.snn["max_feedback_amplitude"] = max_feedback_amplitude
    cfg.snn["sync_dt"] = sync_dt
    cfg.snn["input_rate_unit"] = input_rate_unit
    cfg.snn["output_activity_unit"] = output_activity_unit


def _validate_analysis_config(cfg: ExperimentConfig) -> None:
    """Waliduje wybór zestawów analiz uruchamianych po symulacji."""
    sets_val = _require_list(cfg.analysis.get("sets", []), "analysis.sets")
    sets_val = [
        _require_non_empty_string(set_name, f"analysis.sets[{idx}]")
        for idx, set_name in enumerate(sets_val)
    ]
    if len(sets_val) != len(set(sets_val)):
        raise ConfigValidationError("analysis.sets musi zawierać unikalne nazwy")

    allowed = {"spectral", "phase_locking", "connectivity", "information_flow"}
    unknown = [name for name in sets_val if name not in allowed]
    if unknown:
        raise ConfigValidationError(f"Nieznane analysis.sets: {unknown}")
    cfg.analysis["sets"] = sets_val
    if "max_report_trials" in cfg.analysis:
        cfg.analysis["max_report_trials"] = _require_non_negative_int(
            cfg.analysis["max_report_trials"], "analysis.max_report_trials"
        )
    if "include_full_trial_table" in cfg.analysis:
        cfg.analysis["include_full_trial_table"] = _require_bool(
            cfg.analysis["include_full_trial_table"],
            "analysis.include_full_trial_table",
        )


def _validate_output_config(cfg: ExperimentConfig) -> None:
    """Waliduje i normalizuje parametry zapisu artefaktów eksperymentu."""
    if "save_results" not in cfg.output:
        raise ConfigValidationError("Brak pola output.save_results")
    cfg.output["save_results"] = _require_bool(
        cfg.output["save_results"], "output.save_results"
    )
    if "label" not in cfg.output:
        raise ConfigValidationError("Brak pola output.label")
    cfg.output["label"] = _require_non_empty_string(cfg.output["label"], "output.label")
    output_dir = cfg.output.get("output_dir", "outputs")
    cfg.output["output_dir"] = str(
        Path(_require_non_empty_string(output_dir, "output.output_dir"))
    )
