"""Ujednolicone raportowanie analizy i benchmarków."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from brain_core.simulation.events import EVENT_TERM_EXPLANATIONS, EVENT_TERM_GLOSSARY

from .connectivity import compute_connectivity
from .information_flow import compute_information_flow
from .phase_locking import compute_phase_locking
from .signal_metrics import comparative_report
from .spectral import compute_band_powers

DEFAULT_CLINICAL_SEVERITY_THRESHOLDS = {"small": 0.0, "medium": 0.02, "large": 0.05}


def _format_polish_list(values: list[str]) -> str:
    """Zwraca czytelny opis listy pojęć używany w komentarzu edukacyjnym."""
    cleaned_values = [str(value) for value in values if str(value).strip()]
    if not cleaned_values:
        return "brak wskazanych elementów"
    if len(cleaned_values) == 1:
        return cleaned_values[0]
    return ", ".join(cleaned_values[:-1]) + f" oraz {cleaned_values[-1]}"


def _classify_clinical_difference(
    value: float,
    severity_thresholds: dict[str, Any] | None,
) -> str:
    """Klasyfikuje skalę różnicy klinicznej na podstawie jawnych progów profilu.

    Parameters
    ----------
    value:
        Wartość metryki różnicy, zwykle średnia albo maksymalna różnica
        bezwzględna aktywności względem profilu referencyjnego.
    severity_thresholds:
        Progi z sekcji ``clinical_profile.severity_level``. Wartości ``medium``
        i ``large`` są traktowane jako dolne granice odpowiednio średniej
        oraz dużej różnicy.

    Returns
    -------
    str
        Polska etykieta: ``mała różnica``, ``średnia różnica`` albo
        ``duża różnica``.
    """
    thresholds = dict(DEFAULT_CLINICAL_SEVERITY_THRESHOLDS)
    if severity_thresholds:
        thresholds.update(
            {key: float(v) for key, v in severity_thresholds.items()}
        )

    if value >= thresholds["large"]:
        return "duża różnica"
    if value >= thresholds["medium"]:
        return "średnia różnica"
    return "mała różnica"


def _describe_observed_direction(signed_difference: float) -> str:
    """Opisuje kierunek zmiany aktywności względem profilu referencyjnego."""
    if signed_difference > 0.0:
        return "wzrost aktywności"
    if signed_difference < 0.0:
        return "spadek aktywności"
    return "bez zmian aktywności"


def _build_educational_comment(
    *,
    profile: dict[str, Any],
    region: str,
    time_s: float,
    severity_label: str,
    observed_direction: str,
) -> str:
    """Tworzy dydaktyczny komentarz łączący metadane profilu z wynikiem.

    Parameters
    ----------
    profile:
        Metadane profilu klinicznego zawierające mechanizm, regiony, funkcje
        poznawcze i oczekiwane efekty.
    region:
        Region z największą różnicą względem profilu referencyjnego.
    time_s:
        Czas największej różnicy w sekundach.
    severity_label:
        Polska etykieta skali różnicy.
    observed_direction:
        Kierunek zmiany aktywności względem profilu referencyjnego.

    Returns
    -------
    str
        Jednozdaniowy komentarz do raportu klinicznego.
    """
    affected_regions = _format_polish_list(profile.get("affected_regions") or [])
    cognitive_functions = _format_polish_list(profile.get("cognitive_functions") or [])
    expected_effects = profile.get("expected_effects") or {}
    if expected_effects:
        effects_description = "; ".join(
            f"{key}: {value}" for key, value in expected_effects.items()
        )
    else:
        effects_description = "brak dodatkowych oczekiwanych efektów"

    return (
        f"Mechanizm: {profile.get('mechanism', 'n/a')} Regiony wskazane w profilu "
        f"to {affected_regions}, a powiązane funkcje poznawcze to "
        f"{cognitive_functions}. Oczekiwane efekty: {effects_description}. "
        f"W symulacji największy sygnał interpretacyjny wystąpił w regionie "
        f"{region} około {time_s} s i oznacza {severity_label} "
        f"({observed_direction})."
    )


@dataclass
class AnalysisReport:
    """
    Klasa reprezentująca raport z analizy sygnałów i porównania z benchmarkiem.

    Attributes:
        payload (dict): Słownik z metrykami i porównaniami.
    """

    payload: dict

    def to_json(self) -> str:
        """
        Zwraca raport w formacie JSON.
        Returns:
            str: Raport jako tekst JSON.
        """
        return json.dumps(self.payload, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """
        Zwraca raport w formacie Markdown.
        Returns:
            str: Raport jako tekst Markdown.
        """
        metrics = self.payload.get("metrics", {})
        compare = self.payload.get("comparison", {})
        benchmark_metadata = self.payload.get("benchmark_metadata", {})
        lines = ["# Raport analizy", "", "## Metryki"]
        for name, value in metrics.items():
            lines.append(f"- **{name}**: {value}")
        lines.append("")
        if benchmark_metadata:
            lines.append("## Status walidacji")
            for benchmark_name, metadata in benchmark_metadata.items():
                level = metadata.get("level", "n/a")
                origin = metadata.get("comparison_origin_pl", "syntetyczny")
                if level == "empirical":
                    status = "walidacja empiryczna na danych referencyjnych"
                else:
                    status = (
                        "walidacja syntetyczna lub edukacyjna bez danych empirycznych"
                    )
                lines.append(
                    f"- **{benchmark_name}**: {status} "
                    f"(poziom: {level}, charakter: {origin})"
                )
            lines.append("")
        lines.append("## Porównanie z benchmarkiem")
        if benchmark_metadata:
            lines.append("### Metadane benchmarków")
            for benchmark_name, metadata in benchmark_metadata.items():
                origin = metadata.get("comparison_origin_pl", "syntetyczny")
                level = metadata.get("level", "n/a")
                lines.append(
                    f"- **{benchmark_name}**: benchmark {origin} (poziom: {level})"
                )
                lines.append(f"  - **źródło**: {metadata.get('source', 'n/a')}")
                lines.append(f"  - **zakres**: {metadata.get('scope', 'n/a')}")
                lines.append(
                    f"  - **ograniczenia**: {metadata.get('limitations', 'n/a')}"
                )
        for name, value in compare.items():
            lines.append(f"- **{name}**: {value}")

        task_activation = self.payload.get("task_activation")
        if task_activation:
            lines.extend(["", "## Regiony i funkcje pobudzone przez task"])
            lines.append(f"- **task**: {task_activation.get('task_name', 'n/a')}")
            functions = ", ".join(task_activation.get("functions", []))
            regions = ", ".join(task_activation.get("regions", []))
            lines.append(f"- **funkcje**: {functions}")
            lines.append(f"- **regiony**: {regions}")
            for region, value in task_activation.get("mean_regional_input", {}).items():
                lines.append(f"- **średnie wejście {region}**: {value}")

        event_timeline = self.payload.get("event_timeline", [])
        if event_timeline:
            lines.extend(["", "## Oś czasu eksperymentu"])
            for event in event_timeline[:30]:
                lines.append(
                    f"- **{event.get('time_s', 'n/a')} s** — "
                    f"{event.get('label_pl', event.get('event_type', 'zdarzenie'))}: "
                    f"{event.get('description_pl', 'brak opisu')}"
                )
            if len(event_timeline) > 30:
                lines.append(
                    f"- ... pominięto {len(event_timeline) - 30} dalszych zdarzeń."
                )
            lines.extend(["", "### Słownik pojęć osi czasu"])
            for english_name, polish_name in EVENT_TERM_GLOSSARY.items():
                explanation = EVENT_TERM_EXPLANATIONS.get(english_name, "brak opisu")
                lines.append(f"- **{english_name}**: {polish_name} — {explanation}")

        snn_comparison = self.payload.get("snn_comparison")
        if snn_comparison:
            lines.extend(
                ["", "## Porównanie przebiegu bez SNN i z lokalnym obwodem SNN"]
            )
            lines.append(f"- **status SNN**: {snn_comparison.get('status_pl', 'n/a')}")
            lines.append(
                f"- **regiony SNN**: {', '.join(snn_comparison.get('regions') or [])}"
            )
            lines.append(f"- **tryb SNN**: {snn_comparison.get('mode', 'n/a')}")
            lines.append(f"- **sync_dt [s]**: {snn_comparison.get('sync_dt_s', 'n/a')}")
            lines.append(
                f"- **maksymalna amplituda sprzężenia**: "
                f"{snn_comparison.get('max_feedback_amplitude', 'n/a')}"
            )
            lines.append(
                f"- **jednostki wejścia/wyjścia**: "
                f"{snn_comparison.get('input_rate_unit', 'n/a')} / "
                f"{snn_comparison.get('output_activity_unit', 'n/a')}"
            )
            mode_metrics = snn_comparison.get("mode_metrics") or {}
            if mode_metrics:
                for mode_name in ("baseline", "report_only_snn", "closed_loop_snn"):
                    if mode_name in mode_metrics:
                        lines.append(f"- **{mode_name}**")
                        for region, stats in mode_metrics[mode_name].items():
                            lines.append(f"  - **{region}**")
                            for metric_name, metric_value in stats.items():
                                lines.append(f"    - {metric_name}: {metric_value}")
            else:
                for region, stats in (
                    snn_comparison.get("region_differences") or {}
                ).items():
                    lines.append(f"- **{region}**")
                    lines.append(
                        f"  - średnia aktywność bez SNN: "
                        f"{stats.get('mean_without_snn', 'n/a')}"
                    )
                    lines.append(
                        f"  - średnia aktywność z SNN: "
                        f"{stats.get('mean_with_snn', 'n/a')}"
                    )
                    lines.append(
                        f"  - średnia różnica bezwzględna: "
                        f"{stats.get('mean_abs_difference', 'n/a')}"
                    )
                    lines.append(
                        f"  - maksymalna różnica bezwzględna: "
                        f"{stats.get('max_abs_difference', 'n/a')}"
                    )

        roving_report = self.payload.get("roving_oddball")
        if roving_report:
            lines.extend(["", "## Raport roving oddball"])
            lines.append(
                f"- **standard**: {roving_report.get('standard_count', 'n/a')} triali"
            )
            lines.append(
                f"- **deviant**: {roving_report.get('deviant_count', 'n/a')} triali"
            )
            lines.append(
                f"- **nowy standard**: "
                f"{roving_report.get('new_standard_count', 'n/a')} triali"
            )
            lines.append(
                f"- **średni surprise_index**: "
                f"{roving_report.get('mean_surprise_index', 'n/a')}"
            )
            lines.append(
                f"- **tempo habituacji**: "
                f"{roving_report.get('habituation_rate', 'n/a')}"
            )
            lines.append(
                f"- **latency readaptacji**: "
                f"{roving_report.get('mean_readaptation_latency', 'n/a')}"
            )

        roving_profile_comparison = self.payload.get("roving_profile_comparison")
        if roving_profile_comparison:
            lines.extend(["", "## Porównanie profili roving oddball"])
            lines.append(
                f"- **ten sam seed**: "
                f"{roving_profile_comparison.get('same_seed', 'n/a')}"
            )
            lines.append(
                f"- **ta sama sekwencja**: "
                f"{roving_profile_comparison.get('same_sequence', 'n/a')}"
            )
            for profile in roving_profile_comparison.get("profiles") or []:
                lines.append(f"- **profil**: {profile.get('profile_id', 'n/a')}")
                lines.append(f"  - grupa: {profile.get('profile_group', 'n/a')}")
                lines.append(
                    f"  - średni surprise_index: "
                    f"{profile.get('mean_surprise_index', 'n/a')}"
                )
                lines.append(
                    f"  - tempo habituacji: "
                    f"{profile.get('habituation_rate', 'n/a')}"
                )
                lines.append(
                    f"  - latency readaptacji: "
                    f"{profile.get('mean_readaptation_latency', 'n/a')}"
                )

        clinical_differences = self.payload.get("clinical_differences", [])
        if clinical_differences:
            lines.extend(["", "## Raport różnic profili klinicznych"])
            for item in clinical_differences:
                lines.append(f"- **profil**: {item.get('profile_id', 'n/a')}")
                lines.append(f"  - **region**: {item.get('region', 'n/a')}")
                lines.append(f"  - **czas_s**: {item.get('time_s', 'n/a')}")
                lines.append(
                    f"  - **funkcja poznawcza**: "
                    f"{item.get('cognitive_function', 'n/a')}"
                )
                lines.append(f"  - **mechanizm**: {item.get('mechanism', 'n/a')}")
                lines.append(
                    f"  - **średnia różnica bezwzględna**: "
                    f"{item.get('mean_abs_difference', 'n/a')}"
                )
                lines.append(
                    f"  - **klasyfikacja różnicy**: "
                    f"{item.get('difference_classification', 'n/a')}"
                )
                lines.append(
                    f"  - **metryka główna**: {item.get('primary_metric', 'n/a')}"
                )
                lines.append(
                    f"  - **kierunek obserwowany**: "
                    f"{item.get('observed_direction', 'n/a')}"
                )
                lines.append(
                    f"  - **komentarz dydaktyczny**: "
                    f"{item.get('educational_comment', 'n/a')}"
                )
        return "\n".join(lines)

    def to_csv_rows(self) -> list[dict[str, str]]:
        """
        Zwraca raport jako listę wierszy do CSV.
        Returns:
            list[dict[str, str]]: Lista słowników z sekcją, metryką i wartością.
        """
        rows: list[dict[str, str]] = []
        for section in ("metrics", "comparison"):
            for key, value in self.payload.get(section, {}).items():
                rows.append({"section": section, "metric": key, "value": str(value)})
        for benchmark_name, metadata in self.payload.get(
            "benchmark_metadata", {}
        ).items():
            level = metadata.get("level", "n/a")
            if level == "empirical":
                validation_status = "empirical"
            else:
                validation_status = "synthetic"
            rows.append(
                {
                    "section": "validation_status",
                    "metric": benchmark_name,
                    "value": validation_status,
                }
            )
            for key, value in metadata.items():
                rows.append(
                    {
                        "section": "benchmark_metadata",
                        "metric": f"{benchmark_name}_{key}",
                        "value": str(value),
                    }
                )
        task_activation = self.payload.get("task_activation")
        if task_activation:
            rows.append(
                {
                    "section": "task_activation",
                    "metric": "functions",
                    "value": ", ".join(task_activation.get("functions", [])),
                }
            )
            rows.append(
                {
                    "section": "task_activation",
                    "metric": "regions",
                    "value": ", ".join(task_activation.get("regions", [])),
                }
            )
            for region, value in task_activation.get("mean_regional_input", {}).items():
                rows.append(
                    {
                        "section": "task_activation",
                        "metric": f"mean_regional_input_{region}",
                        "value": str(value),
                    }
                )

        for idx, event in enumerate(self.payload.get("event_timeline", [])):
            rows.append(
                {
                    "section": "event_timeline",
                    "metric": f"event_{idx}",
                    "value": (
                        f"{event.get('time_s', 'n/a')}|"
                        f"{event.get('event_type', 'n/a')}|"
                        f"{str(event.get('description_pl', 'n/a')).replace('|', ' ')}"
                    ),
                }
            )

        for english_name, polish_name in EVENT_TERM_GLOSSARY.items():
            explanation = EVENT_TERM_EXPLANATIONS.get(english_name, "brak opisu")
            rows.append(
                {
                    "section": "event_glossary",
                    "metric": english_name,
                    "value": f"{polish_name} — {explanation}",
                }
            )

        snn_comparison = self.payload.get("snn_comparison")
        if snn_comparison:
            rows.append(
                {
                    "section": "snn_comparison",
                    "metric": "status_pl",
                    "value": str(snn_comparison.get("status_pl", "n/a")),
                }
            )
            for metadata_name in ("mode", "sync_dt_s", "max_feedback_amplitude"):
                rows.append(
                    {
                        "section": "snn_comparison",
                        "metric": metadata_name,
                        "value": str(snn_comparison.get(metadata_name, "n/a")),
                    }
                )
            mode_metrics = snn_comparison.get("mode_metrics") or {}
            if mode_metrics:
                for mode_name, regions in mode_metrics.items():
                    for region, stats in regions.items():
                        for metric_name, metric_value in stats.items():
                            rows.append(
                                {
                                    "section": "snn_comparison",
                                    "metric": f"{mode_name}_{region}_{metric_name}",
                                    "value": str(metric_value),
                                }
                            )
            else:
                for region, stats in (
                    snn_comparison.get("region_differences") or {}
                ).items():
                    for metric_name, metric_value in stats.items():
                        rows.append(
                            {
                                "section": "snn_comparison",
                                "metric": f"{region}_{metric_name}",
                                "value": str(metric_value),
                            }
                        )

        roving_report = self.payload.get("roving_oddball")
        if roving_report:
            for metric in (
                "standard_count",
                "deviant_count",
                "new_standard_count",
                "mean_surprise_index",
                "habituation_rate",
                "mean_readaptation_latency",
            ):
                rows.append(
                    {
                        "section": "roving_oddball",
                        "metric": metric,
                        "value": str(roving_report.get(metric, "n/a")),
                    }
                )

        roving_profile_comparison = self.payload.get("roving_profile_comparison")
        if roving_profile_comparison:
            rows.append(
                {
                    "section": "roving_profile_comparison",
                    "metric": "same_seed",
                    "value": str(roving_profile_comparison.get("same_seed", "n/a")),
                }
            )
            rows.append(
                {
                    "section": "roving_profile_comparison",
                    "metric": "same_sequence",
                    "value": str(roving_profile_comparison.get("same_sequence", "n/a")),
                }
            )
            for profile in roving_profile_comparison.get("profiles") or []:
                profile_id = profile.get("profile_id", "n/a")
                rows.append(
                    {
                        "section": "roving_profile_comparison",
                        "metric": f"{profile_id}_profile_group",
                        "value": str(profile.get("profile_group", "n/a")),
                    }
                )
                for metric in (
                    "mean_surprise_index",
                    "habituation_rate",
                    "mean_readaptation_latency",
                ):
                    rows.append(
                        {
                            "section": "roving_profile_comparison",
                            "metric": f"{profile_id}_{metric}",
                            "value": str(profile.get(metric, "n/a")),
                        }
                    )

        for item in self.payload.get("clinical_differences", []):
            profile_id = item.get("profile_id", "n/a")
            for metric in (
                "region",
                "time_s",
                "cognitive_function",
                "mechanism",
                "mean_abs_difference",
                "max_abs_difference",
                "primary_metric",
                "expected_direction",
                "observed_direction",
                "difference_classification",
                "educational_comment",
            ):
                rows.append(
                    {
                        "section": "clinical_differences",
                        "metric": f"{profile_id}_{metric}",
                        "value": str(item.get(metric, "n/a")),
                    }
                )
        return rows


def build_roving_oddball_report(
    trial_results: list[dict[str, Any]],
    *,
    profile_id: str | None = None,
) -> dict[str, object]:
    """Agreguje metryki sekwencji roving oddball z wyników triali.

    Parameters
    ----------
    trial_results:
        Lista wyników triali zawierająca warunki ``standard`` i ``deviant``
        oraz metryki ``surprise_index``, ``habituation_level`` i
        ``readaptation_latency``.
    profile_id:
        Opcjonalny identyfikator profilu klinicznego dodawany do raportu
        porównawczego.

    Returns
    -------
    dict[str, object]
        Podsumowanie liczby standardów, dewiantów, nowych standardów, średniego
        indeksu zaskoczenia, tempa habituacji i latencji readaptacji.
    """
    if not trial_results:
        return {
            "profile_id": profile_id,
            "standard_count": 0,
            "deviant_count": 0,
            "new_standard_count": 0,
            "mean_surprise_index": 0.0,
            "habituation_rate": 0.0,
            "mean_readaptation_latency": 0.0,
            "sequence_signature": [],
        }

    surprise_values = [
        float(val) if (val := result.get("surprise_index")) is not None else 0.0
        for result in trial_results
    ]
    readaptation_values = [
        float(val)
        for result in trial_results
        if (val := result.get("readaptation_latency")) is not None and float(val) > 0.0
    ]
    habituation_deltas: list[float] = []
    previous_by_run: dict[int, float] = {}
    for result in trial_results:
        if result.get("condition") != "standard":
            continue
        run_index = int(result.get("run_index", -1))
        level = float(result.get("habituation_level", 0.0))
        if run_index in previous_by_run:
            delta = level - previous_by_run[run_index]
            if delta > 0.0:
                habituation_deltas.append(delta)
        previous_by_run[run_index] = level

    sequence_signature = [
        {
            "trial_id": (
                int(val) if (val := result.get("trial_id")) is not None else index
            ),
            "condition": (
                str(val) if (val := result.get("condition")) is not None else "n/a"
            ),
            "tone_hz": (
                result.get("tone_hz") if result.get("tone_hz") is not None else "n/a"
            ),
            "is_new_standard": bool(result.get("is_new_standard")),
        }
        for index, result in enumerate(trial_results)
    ]

    summary: dict[str, object] = {
        "standard_count": sum(
            1 for result in trial_results if result.get("condition") == "standard"
        ),
        "deviant_count": sum(
            1 for result in trial_results if result.get("condition") == "deviant"
        ),
        "new_standard_count": sum(
            1 for result in trial_results if result.get("is_new_standard", False)
        ),
        "mean_surprise_index": round(float(np.mean(surprise_values)), 6),
        "habituation_rate": (
            round(float(np.mean(habituation_deltas)), 6) if habituation_deltas else 0.0
        ),
        "mean_readaptation_latency": (
            round(float(np.mean(readaptation_values)), 6)
            if readaptation_values
            else 0.0
        ),
        "sequence_signature": sequence_signature,
    }
    if profile_id is not None:
        summary["profile_id"] = profile_id
    return summary


def write_report_files(
    report: AnalysisReport, output_dir: Path, stem: str = "analysis_report"
) -> dict[str, str]:
    """
    Zapisuje raport do plików JSON, CSV i Markdown.

    Args:
        report (AnalysisReport): Raport do zapisania.
        output_dir (Path): Katalog wyjściowy.
        stem (str): Nazwa bazowa plików.

    Returns:
        dict[str, str]: Słownik ze ścieżkami do plików.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    md_path = output_dir / f"{stem}.md"

    json_path.write_text(report.to_json(), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["section", "metric", "value"])
        writer.writeheader()
        writer.writerows(report.to_csv_rows())
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def build_analysis_report(
    eeg: np.ndarray,
    fmri: np.ndarray,
    behavior: np.ndarray,
    benchmark: dict[str, np.ndarray] | None = None,
    fs: float = 100.0,
    analysis_set: list[str] | None = None,
    benchmark_metadata: dict[str, dict[str, str]] | None = None,
) -> AnalysisReport:
    """
    Buduje raport analizy sygnałów EEG, fMRI i zachowania oraz porównania z benchmarkiem.

    Args:
        eeg (np.ndarray): Sygnały EEG.
        fmri (np.ndarray): Sygnały fMRI.
        behavior (np.ndarray): Dane behawioralne.
        benchmark (dict[str, np.ndarray] | None): Słownik z benchmarkami.
        fs (float): Częstotliwość próbkowania.
        analysis_set (list[str] | None): Lista analiz do wykonania.
        benchmark_metadata (dict[str, dict[str, str]] | None): Metadane źródeł,
            zakresów, ograniczeń i poziomów benchmarków.

    Returns:
        AnalysisReport: Raport z metrykami i porównaniami.

    Raises:
        ValueError: Jeśli sygnały wejściowe są puste.
    """
    eeg = np.asarray(eeg, dtype=float)
    fmri = np.asarray(fmri, dtype=float)
    behavior = np.asarray(behavior, dtype=float)

    if eeg.size == 0 or fmri.size == 0 or behavior.size == 0:
        raise ValueError("Sygnały wejściowe do raportu analizy nie mogą być puste.")

    primary = eeg[:, 0] if eeg.ndim == 2 else eeg
    secondary = eeg[:, 1] if eeg.ndim == 2 and eeg.shape[1] > 1 else primary

    selected = set(
        analysis_set
        if analysis_set is not None
        else ["spectral", "phase_locking", "connectivity", "information_flow"]
    )
    bands = compute_band_powers(primary, fs) if "spectral" in selected else None
    plv = (
        compute_phase_locking(primary, secondary)
        if "phase_locking" in selected
        else None
    )
    net_input = eeg if eeg.ndim == 2 else np.column_stack([primary, secondary])
    conn = compute_connectivity(net_input) if "connectivity" in selected else None
    flow = (
        compute_information_flow(net_input) if "information_flow" in selected else None
    )
    erp_proxy = float(np.max(primary) - np.min(primary))

    beh_mean = float(np.mean(behavior))
    beh_std = float(np.std(behavior))

    metrics = {
        "band_power_alpha": float(bands.summary.get("alpha", 0.0)) if bands else 0.0,
        "band_power_beta": float(bands.summary.get("beta", 0.0)) if bands else 0.0,
        "erp_proxy_peak_to_peak": erp_proxy,
        "phase_locking_value": float(plv.summary["plv"]) if plv else 0.0,
        "connectivity_mean": float(conn.summary["correlation_mean"]) if conn else 0.0,
        "connectivity_abs_mean": (
            float(conn.summary["correlation_abs_mean"]) if conn else 0.0
        ),
        "pli_proxy_mean": float(conn.summary["pli_proxy_mean"]) if conn else 0.0,
        "region_strength_mean": (
            float(conn.summary["region_strength_mean"]) if conn else 0.0
        ),
        "directional_mean": float(flow.summary["directional_mean"]) if flow else 0.0,
        "behavior_mean": beh_mean,
        "behavior_std": beh_std,
        "fmri_mean": float(np.mean(fmri)),
    }

    comparison: dict[str, float] = {}
    if benchmark:
        if "eeg" in benchmark:
            comparison.update(
                {
                    f"eeg_{k}": v
                    for k, v in comparative_report(eeg, benchmark["eeg"]).items()
                }
            )
        if "fmri" in benchmark:
            comparison.update(
                {
                    f"fmri_{k}": v
                    for k, v in comparative_report(fmri, benchmark["fmri"]).items()
                }
            )
        if "behavior" in benchmark:
            comparison.update(
                {
                    f"behavior_{k}": v
                    for k, v in comparative_report(
                        behavior, benchmark["behavior"]
                    ).items()
                }
            )

    payload = {"metrics": metrics, "comparison": comparison}
    if benchmark_metadata is not None:
        payload["benchmark_metadata"] = benchmark_metadata

    return AnalysisReport(payload=payload)


def build_clinical_difference_report(
    reference_result: dict,
    profile_results: dict[str, dict],
) -> AnalysisReport:
    """Buduje raport różnic między profilem referencyjnym i klinicznymi.

    Parameters
    ----------
    reference_result:
        Wynik uruchomienia referencyjnego, zwykle dla profilu `healthy_v1`.
    profile_results:
        Mapa identyfikator profilu→wynik eksperymentu dla porównywanych profili.

    Returns
    -------
    AnalysisReport
        Raport opisujący największą różnicę według regionu, czasu, funkcji
        poznawczej i mechanizmu profilu klinicznego.

    Raises
    ------
    ValueError
        Gdy aktywność referencyjna lub porównywana jest pusta.
    """
    reference_activity = np.asarray(reference_result.get("activity", []), dtype=float)
    if reference_activity.ndim == 1:
        reference_activity = reference_activity[:, np.newaxis]
    reference_time = np.asarray(reference_result.get("time", []), dtype=float)
    reference_model = reference_result.get("model")
    reference_names = list(getattr(reference_model, "names", []))
    if reference_activity.size == 0 or reference_time.size == 0:
        raise ValueError("Wynik referencyjny musi zawierać aktywność i czas.")

    differences: list[dict[str, object]] = []
    for profile_id, result in profile_results.items():
        activity = np.asarray(result.get("activity", []), dtype=float)
        if activity.ndim == 1:
            activity = activity[:, np.newaxis]
        if activity.size == 0:
            raise ValueError(f"Wynik profilu {profile_id} nie zawiera aktywności.")

        rows = min(reference_activity.shape[0], activity.shape[0])
        cols = min(reference_activity.shape[1], activity.shape[1])
        signed_delta = activity[:rows, :cols] - reference_activity[:rows, :cols]
        delta = np.abs(signed_delta)
        mean_by_region = np.mean(delta, axis=0)
        region_idx = int(np.argmax(mean_by_region))
        time_idx = int(np.argmax(delta[:, region_idx]))
        profile = result.get("clinical_profile", {})
        functions = profile.get("cognitive_functions") or result.get(
            "task_activation", {}
        ).get("functions", [])
        region = (
            reference_names[region_idx]
            if region_idx < len(reference_names)
            else f"region_{region_idx}"
        )
        mean_abs_difference = round(float(mean_by_region[region_idx]), 8)
        max_abs_difference = round(float(delta[time_idx, region_idx]), 8)
        primary_metric = str(profile.get("primary_metric", "mean_abs_difference"))
        primary_value = (
            max_abs_difference
            if primary_metric == "max_abs_difference"
            else mean_abs_difference
        )
        severity_label = _classify_clinical_difference(
            primary_value, profile.get("severity_level")
        )
        time_s = round(float(reference_time[min(time_idx, reference_time.size - 1)]), 6)
        observed_direction = _describe_observed_direction(
            float(np.mean(signed_delta[:, region_idx]))
        )
        educational_comment = _build_educational_comment(
            profile=profile,
            region=region,
            time_s=time_s,
            severity_label=severity_label,
            observed_direction=observed_direction,
        )
        differences.append(
            {
                "profile_id": profile.get("id", profile_id),
                "display_name": profile.get("display_name", profile_id),
                "region": region,
                "time_s": time_s,
                "cognitive_function": functions[0] if functions else "n/a",
                "mechanism": profile.get("mechanism", "n/a"),
                "affected_regions": list(profile.get("affected_regions") or []),
                "cognitive_functions": list(functions),
                "expected_effects": dict(profile.get("expected_effects") or {}),
                "expected_direction": profile.get("expected_direction", "n/a"),
                "observed_direction": observed_direction,
                "primary_metric": primary_metric,
                "severity_level": dict(
                    profile.get("severity_level")
                    or DEFAULT_CLINICAL_SEVERITY_THRESHOLDS
                ),
                "difference_classification": severity_label,
                "educational_comment": educational_comment,
                "mean_abs_difference": mean_abs_difference,
                "max_abs_difference": max_abs_difference,
            }
        )

    return AnalysisReport(payload={"clinical_differences": differences})
