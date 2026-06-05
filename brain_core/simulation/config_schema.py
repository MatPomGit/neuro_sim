"""Schema i walidacja konfiguracji eksperymentu symulacyjnego."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain_core.simulation.signal_adapter import (
    ALLOWED_SNN_COUPLING_MODES,
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
    stimulus: dict[str, Any] = field(default_factory=dict)
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
            "sets": ["spectral", "phase_locking", "connectivity", "information_flow"]
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
    normalized = dict(raw)
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
    """Waliduje jawną sekcję bodźców eksperymentalnych."""
    if "scenario" in cfg.stimulus:
        cfg.stimulus["scenario"] = _require_non_empty_string(
            cfg.stimulus["scenario"], "stimulus.scenario"
        )
    if "source" in cfg.stimulus:
        cfg.stimulus["source"] = _require_non_empty_string(
            cfg.stimulus["source"], "stimulus.source"
        )


def _validate_brain_profile_config(cfg: ExperimentConfig) -> None:
    """Waliduje bazowy profil mózgu niezależny od profilu klinicznego."""
    if "id" in cfg.brain_profile:
        cfg.brain_profile["id"] = _require_non_empty_string(
            cfg.brain_profile["id"], "brain_profile.id"
        )
    if "description" in cfg.brain_profile:
        cfg.brain_profile["description"] = _require_non_empty_string(
            cfg.brain_profile["description"], "brain_profile.description"
        )


def _validate_connectome_config(cfg: ExperimentConfig) -> None:
    """Waliduje sekcję atlasu i macierzy connectome."""
    for text_field in ("atlas", "weights", "fiber_lengths"):
        if text_field in cfg.connectome and cfg.connectome[text_field] is not None:
            cfg.connectome[text_field] = _require_non_empty_string(
                cfg.connectome[text_field], f"connectome.{text_field}"
            )


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

    for text_key in ("display_name", "mechanism"):
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

    cfg.clinical_profile["id"] = str(profile_id)
    cfg.clinical_profile["display_name"] = cfg.clinical_profile["display_name"].strip()
    cfg.clinical_profile["mechanism"] = cfg.clinical_profile["mechanism"].strip()
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
    for idx, set_name in enumerate(sets_val):
        sets_val[idx] = _require_non_empty_string(set_name, f"analysis.sets[{idx}]")

    allowed = {"spectral", "phase_locking", "connectivity", "information_flow"}
    unknown = [name for name in sets_val if name not in allowed]
    if unknown:
        raise ConfigValidationError(f"Nieznane analysis.sets: {unknown}")
    cfg.analysis["sets"] = sets_val


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
