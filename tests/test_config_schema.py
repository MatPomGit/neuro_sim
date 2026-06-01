"""Testy walidacji konfiguracji eksperymentów symulacyjnych."""

from __future__ import annotations

import pytest

from brain_core.simulation.config_schema import ConfigValidationError, validate_config


def test_missing_snn_sync_dt_follows_timestep() -> None:
    """Domyślne sync_dt ma podążać za timestep, aby GUI nie blokowało symulacji."""
    cfg = validate_config(
        {
            "timestep": 0.01,
            "task": {"duration": 1.0},
        }
    )

    assert cfg.snn["sync_dt"] == 0.01


def test_explicit_snn_sync_dt_still_must_match_timestep() -> None:
    """Jawne sync_dt nadal chroni współsymulację przed niespójnym krokiem czasu."""
    with pytest.raises(
        ConfigValidationError, match="snn.sync_dt musi być wielokrotnością"
    ):
        validate_config(
            {
                "timestep": 0.02,
                "task": {"duration": 1.0},
                "snn": {"enabled": True, "circuits": [], "sync_dt": 0.005},
            }
        )


def test_clinical_profile_validation_accepts_known_profile() -> None:
    """Profil kliniczny z katalogu konfiguracji ma przechodzić walidację schematu."""
    cfg = validate_config(
        {
            "task": {"duration": 1.0},
            "clinical_profile": {
                "id": "dopamine_deficit",
                "display_name": "Deficyt dopaminowy",
                "mechanism": "Obniżona modulacja nagrody.",
                "affected_regions": ["VAL"],
                "cognitive_functions": ["uczenie ze wzmocnieniem"],
                "expected_effects": {"learning_rate_value": "niższe"},
            },
        }
    )

    assert cfg.clinical_profile["id"] == "dopamine_deficit"


def test_clinical_profile_validation_rejects_unknown_profile() -> None:
    """Nieznany identyfikator profilu ma dawać czytelny błąd walidacji."""
    with pytest.raises(ConfigValidationError, match="Nieznany clinical_profile.id"):
        validate_config(
            {
                "task": {"duration": 1.0},
                "clinical_profile": {
                    "id": "unknown_profile",
                    "display_name": "Nieznany profil",
                    "mechanism": "Opis mechanizmu.",
                    "affected_regions": [],
                    "cognitive_functions": [],
                    "expected_effects": {},
                },
            }
        )


def test_snn_hippocampus_demo_mapping_sync_dt_and_units() -> None:
    """Konfiguracja demo SNN ma być zgodna z mapowaniem, czasem i jednostkami."""
    from brain_core.simulation.config_loader import load_config
    from brain_core.simulation.signal_adapter import SNNPopulationMapping

    cfg = load_config("configs/snn_hippocampus_demo.yaml")
    circuit_regions = tuple(circuit["region"] for circuit in cfg.snn["circuits"])
    neural_mass_regions = tuple(cfg.snn["neural_mass_regions"])
    mapping = SNNPopulationMapping(
        snn_region_names=circuit_regions,
        neural_mass_region_names=neural_mass_regions,
    )

    assert cfg.snn["enabled"] is True
    assert cfg.snn["sync_dt"] == 0.010
    assert cfg.snn["sync_dt"] / cfg.timestep == 2.0
    assert cfg.snn["input_rate_unit"] == "Hz"
    assert cfg.snn["output_activity_unit"] == "fraction"
    assert circuit_regions == ("HIP",)
    assert mapping.indices_in_neural_mass().tolist() == [10]
