"""Schema i walidacja konfiguracji eksperymentu symulacyjnego."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain_core.simulation.signal_adapter import SNNPopulationMapping

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
}


@dataclass
class ExperimentConfig:
    """
    Ujednolicony obiekt konfiguracji eksperymentu po walidacji.

    Atrybuty:
        model (dict[str, Any]): Konfiguracja modelu.
        integrator (dict[str, Any]): Konfiguracja integratora.
        timestep (float): Krok czasowy symulacji.
        seed (int): Ziarno generatora losowego.
        task (dict[str, Any]): Konfiguracja zadania.
        pathology (dict[str, Any]): Konfiguracja patologii.
        output (dict[str, Any]): Ustawienia wyjścia.
        snn (dict[str, Any]): Konfiguracja SNN.
        analysis (dict[str, Any]): Konfiguracja analiz.
        clinical_profile (dict[str, Any]): Metadane profilu klinicznego.
    """

    model: dict[str, Any] = field(default_factory=dict)
    integrator: dict[str, Any] = field(default_factory=lambda: {"method": "euler"})
    timestep: float = 0.005
    seed: int = 7
    task: dict[str, Any] = field(
        default_factory=lambda: {"scenario": "reward-learning", "duration": 45.0}
    )
    pathology: dict[str, Any] = field(
        default_factory=lambda: {"enabled": False, "mutations": [], "scenario": None}
    )
    output: dict[str, Any] = field(
        default_factory=lambda: {
            "save_results": True,
            "label": "run",
            "output_dir": "outputs",
        }
    )
    snn: dict[str, Any] = field(
        default_factory=lambda: {"enabled": False, "circuits": []}
    )
    analysis: dict[str, Any] = field(
        default_factory=lambda: {
            "sets": ["spectral", "phase_locking", "connectivity", "information_flow"]
        }
    )
    clinical_profile: dict[str, Any] = field(
        default_factory=lambda: {
            "id": "healthy_v1",
            "display_name": "Zdrowy profil bazowy v1",
            "mechanism": "Brak jawnie modelowanej patologii klinicznej.",
            "affected_regions": [],
            "cognitive_functions": [],
            "expected_effects": {},
        }
    )


def _coerce_string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    """Normalizuje listę nazw regionów SNN do krotki niepustych tekstów.

    Parameters
    ----------
    value:
        Wartość odczytana z konfiguracji YAML/JSON.
    field_name:
        Nazwa pola używana w komunikacie błędu walidacji.

    Returns
    -------
    tuple[str, ...]
        Krotka nazw regionów zachowująca kolejność z konfiguracji.

    Raises
    ------
    ConfigValidationError
        Gdy wartość nie jest listą niepustych tekstów.
    """
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ConfigValidationError(f"{field_name} musi być listą niepustych tekstów")
    return tuple(str(item).strip() for item in value)


class ConfigValidationError(ValueError):
    """
    Błąd walidacji konfiguracji eksperymentu.
    """


def validate_config(raw: dict[str, Any]) -> ExperimentConfig:
    """
    Waliduje surową konfigurację i zwraca obiekt `ExperimentConfig`.

    Args:
        raw (dict[str, Any]): Surowa konfiguracja.

    Returns:
        ExperimentConfig: Zweryfikowany obiekt konfiguracji.

    Raises:
        ConfigValidationError: Jeśli konfiguracja jest niepoprawna.
    """
    if not isinstance(raw, dict):
        raise ConfigValidationError("Konfiguracja musi być obiektem mapującym (dict).")

    cfg = ExperimentConfig(
        **{k: v for k, v in raw.items() if k in ExperimentConfig.__dataclass_fields__}
    )

    if cfg.timestep <= 0:
        raise ConfigValidationError("timestep musi być > 0")
    if cfg.seed < 0:
        raise ConfigValidationError("seed musi być >= 0")
    if float(cfg.task.get("duration", 0.0)) <= 0:
        raise ConfigValidationError("task.duration musi być > 0")
    method = str(cfg.integrator.get("method", "euler"))
    if method != "euler":
        raise ConfigValidationError("integrator.method aktualnie wspiera tylko 'euler'")

    if not isinstance(cfg.pathology, dict):
        raise ConfigValidationError("pathology musi być obiektem")
    mutations = cfg.pathology.get("mutations", [])
    if not isinstance(mutations, list):
        raise ConfigValidationError("pathology.mutations musi być listą")
    for idx, mutation in enumerate(mutations):
        if not isinstance(mutation, dict):
            raise ConfigValidationError(f"pathology.mutations[{idx}] musi być obiektem")
        for required_key in ("kind", "scope", "target"):
            if required_key not in mutation:
                raise ConfigValidationError(
                    f"Brak pola pathology.mutations[{idx}].{required_key}"
                )

    _validate_clinical_profile_config(cfg)
    _validate_snn_config(cfg)
    _validate_analysis_config(cfg)
    cfg.output["output_dir"] = str(Path(cfg.output.get("output_dir", "outputs")))
    return cfg


def _validate_clinical_profile_config(cfg: ExperimentConfig) -> None:
    """Waliduje metadane profilu klinicznego ładowanego z konfiguracji."""
    if not isinstance(cfg.clinical_profile, dict):
        raise ConfigValidationError("clinical_profile musi być obiektem")

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
        value = cfg.clinical_profile.get(text_key, "")
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

    cfg.clinical_profile["id"] = str(profile_id)
    cfg.clinical_profile["affected_regions"] = list(
        cfg.clinical_profile.get("affected_regions", [])
    )
    cfg.clinical_profile["cognitive_functions"] = list(
        cfg.clinical_profile.get("cognitive_functions", [])
    )
    cfg.clinical_profile["expected_effects"] = dict(expected_effects)


def _validate_snn_config(cfg: ExperimentConfig) -> None:
    """Waliduje sekcję konfiguracji współsymulacji SNN."""
    if not isinstance(cfg.snn, dict):
        raise ConfigValidationError("snn musi być obiektem")
    circuits = cfg.snn.get("circuits", [])
    if not isinstance(circuits, list):
        raise ConfigValidationError("snn.circuits musi być listą")

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
        try:
            sync_dt = float(sync_dt_val)
        except (ValueError, TypeError) as exc:
            raise ConfigValidationError("snn.sync_dt musi być liczbą") from exc

    if sync_dt <= 0:
        raise ConfigValidationError("snn.sync_dt musi być > 0")
    ratio = sync_dt / cfg.timestep
    if abs(round(ratio) - ratio) > 1e-9:
        raise ConfigValidationError("snn.sync_dt musi być wielokrotnością timestep")

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

    cfg.snn["sync_dt"] = sync_dt
    cfg.snn["input_rate_unit"] = input_rate_unit
    cfg.snn["output_activity_unit"] = output_activity_unit


def _validate_analysis_config(cfg: ExperimentConfig) -> None:
    """Waliduje wybór zestawów analiz uruchamianych po symulacji."""
    if not isinstance(cfg.analysis, dict):
        raise ConfigValidationError("analysis musi być obiektem")
    sets_val = cfg.analysis.get("sets", [])
    if not isinstance(sets_val, list):
        raise ConfigValidationError("analysis.sets musi być listą")
    allowed = {"spectral", "phase_locking", "connectivity", "information_flow"}
    unknown = [name for name in sets_val if name not in allowed]
    if unknown:
        raise ConfigValidationError(f"Nieznane analysis.sets: {unknown}")
