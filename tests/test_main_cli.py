from __future__ import annotations

import sys
from typing import Any

import main


def test_main_cli_accepts_current_simulation_result_contract(
    monkeypatch: Any,
) -> None:
    """Główne CLI uruchamia model zgodnie z pięcioelementowym kontraktem symulacji."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--time", "0.02", "--seed", "3"])
    monkeypatch.setattr(main, "plot_activity", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "plot_diagnostics", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "plot_eeg_modules", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "plot_band_power", lambda *args, **kwargs: None)

    main.main()
