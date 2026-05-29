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
