"""Testy walidacji konfiguracji eksperymentów symulacyjnych."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from brain_core.simulation.config_loader import load_config, load_config_from_string
from brain_core.simulation.config_schema import ConfigValidationError, validate_config
from brain_core.simulation.engine import run_experiment
from brain_core.simulation.signal_adapter import SNNPopulationMapping


def _valid_config_payload() -> dict[str, Any]:
    """Zwróć minimalną kompletną konfigurację zgodną z docelowym schematem."""
    return {
        "model": {},
        "integrator": {"method": "euler"},
        "timestep": 0.01,
        "seed": 7,
        "rng_seed": 7,
        "task": {"scenario": "stroop", "duration": 1.0},
        "stimulus": {"scenario": "stroop", "source": "task"},
        "brain_profile": {"id": "default"},
        "clinical_profile": {
            "id": "healthy_v1",
            "display_name": "Zdrowy profil bazowy v1",
            "mechanism": "Brak jawnie modelowanej patologii klinicznej.",
            "affected_regions": [],
            "cognitive_functions": [],
            "expected_effects": {},
            "expected_direction": "stable_reference",
            "primary_metric": "mean_abs_difference",
            "severity_level": {"small": 0.0, "medium": 0.02, "large": 0.05},
        },
        "connectome": {
            "atlas": "default_regions",
            "weights": "data/connectomes/weights.csv",
            "fiber_lengths": "data/connectomes/fiber_lengths.csv",
        },
        "pathology": {"enabled": False, "scenario": None, "mutations": []},
        "snn": {"enabled": False, "circuits": []},
        "analysis": {"sets": ["spectral", "phase_locking"]},
        "output": {"save_results": False, "label": "test", "output_dir": "outputs"},
    }


def test_complete_target_schema_accepts_seed_and_rng_seed() -> None:
    """Kompletna konfiguracja ma jawnie mapować `seed` i `rng_seed`."""
    cfg = validate_config(_valid_config_payload())

    assert cfg.seed == 7
    assert cfg.rng_seed == 7
    assert cfg.stimulus["scenario"] == "stroop"
    assert cfg.brain_profile["id"] == "default"
    assert cfg.connectome["atlas"] == "default_regions"


def test_legacy_seed_is_migrated_to_rng_seed() -> None:
    """Historyczne pole `seed` ma zachować semantykę ziarna RNG."""
    payload = _valid_config_payload()
    payload.pop("rng_seed")

    cfg = validate_config(payload)

    assert cfg.seed == 7
    assert cfg.rng_seed == 7


def test_rng_seed_without_legacy_seed_is_mapped_to_seed() -> None:
    """Docelowe pole `rng_seed` ma zasilać kompatybilne pole `seed`."""
    payload = _valid_config_payload()
    payload.pop("seed")

    cfg = validate_config(payload)

    assert cfg.seed == 7
    assert cfg.rng_seed == 7


def test_conflicting_seed_and_rng_seed_is_rejected() -> None:
    """Różne wartości `seed` i `rng_seed` mają dawać czytelny błąd migracji."""
    payload = _valid_config_payload()
    payload["rng_seed"] = 8

    with pytest.raises(ConfigValidationError, match="seed i rng_seed"):
        validate_config(payload)


def test_missing_required_section_reports_full_path() -> None:
    """Brak jawnej sekcji docelowego schematu ma wskazywać pełną nazwę sekcji."""
    payload = _valid_config_payload()
    payload.pop("stimulus")

    with pytest.raises(ConfigValidationError, match="Brak wymaganej sekcji stimulus"):
        validate_config(payload)


def test_missing_required_stimulus_field_reports_full_path() -> None:
    """Brak wymaganego pola bodźca ma wskazywać ścieżkę `stimulus.source`."""
    payload = _valid_config_payload()
    payload["stimulus"].pop("source")

    with pytest.raises(ConfigValidationError, match=r"Brak pola stimulus\.source"):
        validate_config(payload)


def test_missing_required_connectome_field_reports_full_path() -> None:
    """Brak wymaganego atlasu connectome ma wskazywać ścieżkę pola."""
    payload = _valid_config_payload()
    payload["connectome"].pop("atlas")

    with pytest.raises(ConfigValidationError, match=r"Brak pola connectome\.atlas"):
        validate_config(payload)


def test_invalid_brain_profile_id_type_reports_full_path() -> None:
    """Błędny typ profilu mózgu ma wskazywać ścieżkę `brain_profile.id`."""
    payload = _valid_config_payload()
    payload["brain_profile"]["id"] = 123

    with pytest.raises(
        ConfigValidationError, match=r"brain_profile\.id musi być niepustym tekstem"
    ):
        validate_config(payload)


def test_missing_required_brain_profile_id_reports_full_path() -> None:
    """Brak wymaganego pola brain_profile.id ma wskazywać ścieżkę pola."""
    payload = _valid_config_payload()
    payload["brain_profile"].pop("id")

    with pytest.raises(ConfigValidationError, match=r"Brak pola brain_profile\.id"):
        validate_config(payload)


def test_invalid_task_duration_type_reports_field_path() -> None:
    """Błędny typ wartości ma wskazywać ścieżkę pola `task.duration`."""
    payload = _valid_config_payload()
    payload["task"]["duration"] = "długo"

    with pytest.raises(ConfigValidationError, match="task.duration musi być liczbą"):
        validate_config(payload)


def test_yaml_and_json_use_same_validation_path() -> None:
    """Loader YAML i JSON ma zwracać taki sam obiekt po wspólnej walidacji."""
    yaml_payload = """
model: {}
integrator:
  method: euler
timestep: 0.01
seed: 7
rng_seed: 7
task:
  scenario: stroop
  duration: 1.0
stimulus:
  scenario: stroop
  source: task
brain_profile:
  id: default
clinical_profile:
  id: healthy_v1
  display_name: Zdrowy profil bazowy v1
  mechanism: Brak jawnie modelowanej patologii klinicznej.
  affected_regions: []
  cognitive_functions: []
  expected_effects: {}
connectome:
  atlas: default_regions
pathology:
  enabled: false
  scenario: null
  mutations: []
snn:
  enabled: false
  circuits: []
analysis:
  sets: [spectral]
output:
  save_results: false
  label: test
  output_dir: outputs
"""
    json_payload = json.dumps(_valid_config_payload(), ensure_ascii=False)

    yaml_cfg = load_config_from_string(yaml_payload, format_hint="yaml")
    json_cfg = load_config_from_string(json_payload, format_hint="json")

    assert yaml_cfg.seed == json_cfg.seed == 7
    assert yaml_cfg.task["duration"] == json_cfg.task["duration"] == 1.0


def test_invalid_analysis_set_type_reports_field_path() -> None:
    """Błędny typ nazwy analizy ma wskazywać konkretny element listy."""
    payload = _valid_config_payload()
    payload["analysis"]["sets"] = ["spectral", 123]

    with pytest.raises(
        ConfigValidationError, match=r"analysis\.sets\[1\] musi być niepustym tekstem"
    ):
        validate_config(payload)


def test_validate_config_does_not_mutate_raw_payload() -> None:
    """Walidacja nie może dopisywać domyślnych pól do surowej konfiguracji."""
    payload = _valid_config_payload()
    payload["snn"].pop("sync_dt", None)
    original_payload = deepcopy(payload)

    validate_config(payload)

    assert payload == original_payload


@pytest.mark.parametrize(
    "config_path",
    [
        "configs/default.yaml",
        "configs/cognitive_demo.yaml",
        "configs/roving_oddball_healthy.yaml",
        "configs/roving_oddball_lesion_hippocampus.yaml",
        "configs/roving_oddball_disorder_gaba.yaml",
        "configs/multi_region_delay_demo.yaml",
        "configs/multi_region_delay_extended.yaml",
        "configs/snn_hippocampus_demo.yaml",
        "configs/stroop.yaml",
        "configs/go_nogo.yaml",
        "configs/n_back.yaml",
        "configs/scenario_yaml_stroop_dlpfc.yaml",
        "configs/scenario_yaml_go_nogo_gaba.yaml",
        "configs/scenario_yaml_n_back_dopamine.yaml",
        "configs/scenario_yaml_stress_recovery_serotonin.yaml",
    ],
)
def test_target_schema_examples_are_loadable(config_path: str) -> None:
    """Przykładowe konfiguracje mają przechodzić docelowy schemat walidacji."""
    from pathlib import Path

    root_dir = Path(__file__).parent.parent
    cfg = load_config(root_dir / config_path)

    assert cfg.seed == cfg.rng_seed
    assert cfg.task["duration"] > 0.0
    assert isinstance(cfg.analysis["sets"], list)


def test_reproducibility_with_same_seed() -> None:
    """Ten sam seed ma zachować deterministyczne wyniki trial-level."""
    payload = _valid_config_payload()
    payload["task"] = {"name": "stroop", "scenario": "stroop", "duration": 5.0}
    cfg = validate_config(payload)

    first_run = run_experiment(cfg)
    second_run = run_experiment(cfg)

    assert first_run["trial_results"] == second_run["trial_results"]


def test_missing_snn_sync_dt_follows_timestep() -> None:
    """Domyślne sync_dt ma podążać za timestep, aby GUI nie blokowało symulacji."""
    cfg = validate_config(_valid_config_payload())

    assert cfg.snn["sync_dt"] == 0.01


def test_explicit_snn_sync_dt_still_must_match_timestep() -> None:
    """Jawne sync_dt nadal chroni współsymulację przed niespójnym krokiem czasu."""
    payload = _valid_config_payload()
    payload["timestep"] = 0.02
    payload["snn"] = {"enabled": True, "circuits": [], "sync_dt": 0.005}

    with pytest.raises(
        ConfigValidationError, match="snn.sync_dt musi być wielokrotnością"
    ):
        validate_config(payload)


def test_clinical_profile_validation_accepts_known_profile() -> None:
    """Profil kliniczny z katalogu konfiguracji ma przechodzić walidację schematu."""
    payload = _valid_config_payload()
    payload["clinical_profile"] = {
        "id": "dopamine_deficit",
        "display_name": "Deficyt dopaminowy",
        "mechanism": "Obniżona modulacja nagrody.",
        "affected_regions": ["VAL"],
        "cognitive_functions": ["uczenie ze wzmocnieniem"],
        "expected_effects": {"learning_rate_value": "niższe"},
    }

    cfg = validate_config(payload)

    assert cfg.clinical_profile["id"] == "dopamine_deficit"


def test_clinical_profile_validation_rejects_unknown_profile() -> None:
    """Nieznany identyfikator profilu ma dawać czytelny błąd walidacji."""
    payload = _valid_config_payload()
    payload["clinical_profile"] = {
        "id": "unknown_profile",
        "display_name": "Nieznany profil",
        "mechanism": "Opis mechanizmu.",
        "affected_regions": [],
        "cognitive_functions": [],
        "expected_effects": {},
    }

    with pytest.raises(ConfigValidationError, match="Nieznany clinical_profile.id"):
        validate_config(payload)


def test_snn_hippocampus_demo_mapping_sync_dt_and_units() -> None:
    """Konfiguracja demo SNN ma być zgodna z mapowaniem, czasem i jednostkami."""
    cfg = load_config("configs/snn_hippocampus_demo.yaml")
    circuit_regions = tuple(circuit["region"] for circuit in cfg.snn["circuits"])
    neural_mass_regions = tuple(cfg.snn["neural_mass_regions"])
    mapping = SNNPopulationMapping(
        snn_region_names=circuit_regions,
        neural_mass_region_names=neural_mass_regions,
    )

    assert cfg.snn["enabled"] is True
    assert cfg.snn["mode"] == "closed_loop"
    assert cfg.snn["sync_dt"] == 0.010
    assert cfg.snn["max_feedback_amplitude"] == 0.15
    assert cfg.snn["sync_dt"] / cfg.timestep == 2.0
    assert cfg.snn["input_rate_unit"] == "Hz"
    assert cfg.snn["output_activity_unit"] == "fraction"
    assert circuit_regions == ("HIP",)
    assert mapping.indices_in_neural_mass().tolist() == [10]


def test_snn_report_only_mode_is_preserved_as_requested_mode() -> None:
    """Walidator zachowuje jawnie żądany tryb SNN do raportu porównawczego."""
    payload = deepcopy(_valid_config_payload())
    payload["snn"] = {
        "enabled": True,
        "mode": "report_only",
        "sync_dt": 0.02,
        "circuits": [{"region": "HIP"}],
        "neural_mass_regions": ["VIS", "HIP"],
    }

    cfg = validate_config(payload)

    assert cfg.snn["mode"] == "report_only"
    assert cfg.snn["sync_dt"] == 0.02
    assert "requested_mode" not in cfg.snn
    assert "computed_modes" not in cfg.snn
