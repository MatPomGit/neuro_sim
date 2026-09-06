"""Struktury wyników eksperymentów symulacyjnych."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_core.simulation.config_schema import ExperimentConfig


LEGACY_RESULT_KEYS: tuple[str, ...] = (
    "model",
    "time",
    "activity",
    "diagnostics",
    "oscillations",
    "behavior",
    "trial_events",
    "trial_results",
    "trial_report_context",
    "stimulus_sequence_signature",
    "event_timeline",
    "analysis_report",
    "task_activation",
    "clinical_profile",
    "snn_comparison",
    "save_info",
    "elapsed",
    "randomness",
)


@dataclass(frozen=True)
class ExperimentResult(Mapping[str, Any]):
    """Kompletny wynik pojedynczego uruchomienia eksperymentu.

    Obiekt jest publicznym, typowanym kontraktem wyniku. Jednocześnie implementuje
    interfejs ``Mapping`` dla kluczy historycznego API, dzięki czemu istniejący kod
    korzystający z ``result["time"]`` lub ``result.get("save_info")`` pozostaje
    zgodny podczas migracji z luźnego słownika do jawnej struktury danych.

    Parameters
    ----------
    config:
        Konfiguracja użyta do uruchomienia eksperymentu.
    signals:
        Sygnały i obiekty runtime symulacji, w tym model, czas, aktywność,
        diagnostyki, oscylacje oraz zachowanie.
    metrics:
        Metryki i pochodne podsumowania analityczne eksperymentu.
    trial_events:
        Zdarzenia prób wygenerowane przez warstwę zadaniową.
    analysis_report:
        Raport analizy w formacie gotowym do serializacji i prezentacji.
    output_dir:
        Katalog artefaktów wynikowych albo ``None``, jeśli zapis był wyłączony.
    git_info:
        Informacje Git wymagane do odtworzenia uruchomienia.
    environment_info:
        Informacje o środowisku uruchomieniowym i wersjach zależności.
    """

    config: ExperimentConfig
    signals: dict[str, Any]
    metrics: dict[str, Any]
    trial_events: list[dict[str, Any]]
    analysis_report: dict[str, Any]
    output_dir: Path | None
    git_info: dict[str, str | bool | None]
    environment_info: dict[str, Any]
    trial_results: list[dict[str, Any]]
    trial_report_context: dict[str, Any]
    stimulus_sequence_signature: dict[str, Any]
    event_timeline: list[dict[str, Any]]
    task_activation: dict[str, Any]
    clinical_profile: dict[str, Any]
    snn_comparison: dict[str, Any] | None
    save_info: dict[str, Any] | None
    elapsed: float
    randomness: dict[str, Any]

    def to_legacy_dict(self) -> dict[str, Any]:
        """Zwróć wynik w dotychczasowym słownikowym formacie API."""
        return {
            "model": self.signals.get("model"),
            "time": self.signals.get("time"),
            "activity": self.signals.get("activity"),
            "diagnostics": self.signals.get("diagnostics"),
            "oscillations": self.signals.get("oscillations"),
            "behavior": self.signals.get("behavior"),
            "trial_events": self.trial_events,
            "trial_results": self.trial_results,
            "trial_report_context": self.trial_report_context,
            "stimulus_sequence_signature": self.stimulus_sequence_signature,
            "event_timeline": self.event_timeline,
            "analysis_report": self.analysis_report,
            "task_activation": self.task_activation,
            "clinical_profile": self.clinical_profile,
            "snn_comparison": self.snn_comparison,
            "save_info": self.save_info,
            "elapsed": self.elapsed,
            "randomness": self.randomness,
        }

    def __getitem__(self, key: str) -> Any:
        """Udostępnij wartość przez klucz zgodny z historycznym API."""
        if key not in LEGACY_RESULT_KEYS:
            raise KeyError(key)
        return self.to_legacy_dict()[key]

    def __iter__(self) -> Iterator[str]:
        """Iteruj po stabilnych kluczach warstwy kompatybilności."""
        return iter(LEGACY_RESULT_KEYS)

    def __len__(self) -> int:
        """Zwróć liczbę kluczy warstwy kompatybilności."""
        return len(LEGACY_RESULT_KEYS)
