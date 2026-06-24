"""Struktury wyników eksperymentów symulacyjnych."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_core.simulation.config_schema import ExperimentConfig


@dataclass(frozen=True)
class ExperimentResult:
    """Kompletny wynik pojedynczego uruchomienia eksperymentu.

    Klasa porządkuje artefakty powstające podczas symulacji tak, aby wewnętrzna
    ścieżka wykonania operowała na jawnej strukturze danych zamiast na luźnym
    słowniku. Metoda ``to_legacy_dict`` zachowuje dotychczasowy kontrakt API dla
    istniejących odbiorców, którzy oczekują słownika z kluczami używanymi przez
    wcześniejsze wersje ``run_experiment``.

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
    trial_results:
        Wyniki punktacji poszczególnych prób behawioralnych.
    trial_report_context:
        Kontekst raportowania prób używany przez warstwę prezentacji.
    stimulus_sequence_signature:
        Deterministyczny podpis sekwencji bodźców.
    event_timeline:
        Oś czasu zdarzeń modelu i prób.
    task_activation:
        Podsumowanie aktywacji regionów i funkcji dla zadania.
    clinical_profile:
        Profil kliniczny użyty w eksperymencie.
    snn_comparison:
        Opcjonalne porównanie lokalnej symulacji SNN.
    save_info:
        Ścieżki artefaktów zwrócone przez zapis wyników.
    elapsed:
        Czas wykonania symulacji w sekundach.
    randomness:
        Sekcja replikowalności opisująca ziarna i komponenty korzystające z RNG.
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
        """Zwróć wynik w dotychczasowym słownikowym formacie API.

        Returns
        -------
        dict[str, Any]
            Słownik zgodny z wcześniejszym wynikiem ``run_experiment``. Klucze
            są utrzymywane jawnie, aby testy i odbiorcy API wykrywali każdą
            niezamierzoną zmianę kontraktu kompatybilności.
        """
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
