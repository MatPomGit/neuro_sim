from __future__ import annotations

import sys
from typing import Any, TypeAlias

import main

SimulationResult: TypeAlias = tuple[
    list[float],
    list[list[float]],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]


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


class _FailingSaveLogger:
    """Prosty logger testowy zapisujący komunikaty błędów z CLI."""

    def __init__(self) -> None:
        """Zainicjalizuj pustą listę komunikatów błędów."""
        self.error_messages: list[str] = []

    def info(self, message: str, *args: object) -> None:
        """Zignoruj komunikaty informacyjne nieistotne dla testu regresyjnego."""

    def error(self, message: str, *args: object) -> None:
        """Zapisz sformatowany komunikat błędu do późniejszej asercji."""
        self.error_messages.append(message % args)


class _FakeOscillatorBank:
    """Minimalny obiekt parametrów oscylatorów wymagany przez CLI."""

    params: dict[str, object] = {}


class _FakeBrainModel:
    """Deterministyczny model testowy zwracający minimalny wynik symulacji."""

    def __init__(self, *, seed: int, stimulus: str) -> None:
        """Zapisz parametry wejściowe zgodne z konstruktorem modelu produkcyjnego."""
        self.p: dict[str, object] = {"seed": seed, "stimulus": stimulus}
        self.oscillator_bank = _FakeOscillatorBank()
        self.names = ["modul"]
        self.idx = {"modul": 0}

    def simulate(self, T: float) -> SimulationResult:
        """Zwróć minimalny pięcioelementowy kontrakt symulacji bez kosztu obliczeń."""
        return (
            [0.0, T],
            [[0.0], [1.0]],
            {},
            {"metadata": {"scenario": "test"}},
            {},
        )


def test_main_cli_reraises_artifact_save_error(monkeypatch: Any, tmp_path: Any) -> None:
    """CLI przerywa uruchomienie, gdy zapis artefaktów kończy się błędem I/O."""
    import pytest

    logger = _FailingSaveLogger()
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--time", "0.02", "--seed", "3", "--save"],
    )
    monkeypatch.setattr(main, "CognitiveBrainModel", _FakeBrainModel)
    monkeypatch.setattr(main, "build_output_dir", lambda *_args, **_kwargs: tmp_path)
    monkeypatch.setattr(main, "configure_simulation_logger", lambda **_kwargs: logger)
    monkeypatch.setattr(main, "plot_activity", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "plot_diagnostics", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "plot_eeg_modules", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "plot_band_power", lambda *args, **kwargs: None)

    def raise_save_error(*_args: object, **_kwargs: object) -> dict[str, object]:
        """Zasymuluj krytyczny błąd systemu plików podczas zapisu artefaktów."""
        raise OSError("brak miejsca na dysku")

    monkeypatch.setattr(main, "save_run", raise_save_error)

    with pytest.raises(OSError, match="brak miejsca na dysku"):
        main.main()

    assert logger.error_messages == [
        "Krytyczny błąd zapisu artefaktów symulacji: brak miejsca na dysku."
    ]
