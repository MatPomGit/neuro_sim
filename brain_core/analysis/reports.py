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
from .signal_metrics import comparative_report, reportable_signal_metrics
from .spectral import compute_band_powers

REQUIRED_CLINICAL_SEVERITY_KEYS = ("small", "medium", "large")
DEFAULT_VALIDATION_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "validation_registry.md"
)
VALIDATION_REGISTRY_COLUMNS = (
    "benchmark",
    "level",
    "qualitative_validation_level",
    "source",
    "expected_effect",
    "compliance_criteria",
    "tolerance",
    "limitations",
    "status",
)
VALIDATION_METRIC_REGISTRY_COLUMNS = (
    "technical_name",
    "polish_label",
    "validation_data_source",
    "interpretation_range",
    "limitations",
)


def _metric_catalog_by_name() -> dict[str, dict[str, object]]:
    """Zindeksuj katalog metryk EEG/sieciowych gotowych do raportowania.

    Returns
    -------
    dict[str, dict[str, object]]
        Słownik nazwa metryki → metadane interpretacyjne po polsku.
    """

    return {str(item["name"]): dict(item) for item in reportable_signal_metrics()}


def _build_eeg_bold_report_sections(
    metrics: dict[str, float],
    *,
    primary_region: str = "kanał_0",
    secondary_region: str = "kanał_1",
) -> list[dict[str, object]]:
    """Zbuduj opisowe wiersze EEG/BOLD na podstawie policzonych metryk.

    Parameters
    ----------
    metrics:
        Słownik wartości wyliczony wcześniej przez funkcje analityczne
        ``brain_core``. Funkcja nie liczy ponownie metryk, tylko dodaje warstwę
        raportową: region/pasmo, jednostkę, interpretację i ograniczenia.
    primary_region:
        Nazwa głównego kanału albo regionu używanego w metrykach EEG.
    secondary_region:
        Nazwa drugiego kanału albo regionu używanego w metrykach parowych.

    Returns
    -------
    list[dict[str, object]]
        Wiersze sekcji EEG/BOLD gotowe do Markdown, CSV i eksportu PDF.
    """

    catalog = _metric_catalog_by_name()
    metric_context = {
        "band_power_delta": ("EEG", "pasmo delta"),
        "band_power_theta": ("EEG", "pasmo theta"),
        "band_power_alpha": ("EEG", "pasmo alpha"),
        "band_power_beta": ("EEG", "pasmo beta"),
        "band_power_gamma": ("EEG", "pasmo gamma"),
        "erp_proxy_peak_to_peak": ("EEG", primary_region),
        "phase_locking_value": ("EEG", f"{primary_region}–{secondary_region}"),
        "connectivity_mean": ("EEG", "wszystkie regiony"),
        "connectivity_abs_mean": ("EEG", "wszystkie regiony"),
        "pli_proxy_mean": ("EEG", "wszystkie regiony"),
        "region_strength_mean": ("EEG", "wszystkie regiony"),
        "directional_mean": ("EEG", "wszystkie regiony"),
        "directional_abs_mean": ("EEG", "wszystkie regiony"),
        "outgoing_mean": ("EEG", "wszystkie regiony"),
    }
    rows: list[dict[str, object]] = []
    for metric_name, (modality, region_or_band) in metric_context.items():
        if metric_name not in metrics:
            continue
        metadata = catalog.get(metric_name, {})
        rows.append(
            {
                "modality": modality,
                "metric": metric_name,
                "region_or_band": region_or_band,
                "value": float(metrics[metric_name]),
                "unit": metadata.get("unit", "jednostka proxy"),
                "profile_groups": list(
                    metadata.get("profile_groups", ("healthy", "disorder", "lesion"))
                ),
                "interpretation": metadata.get(
                    "interpretation_pl",
                    "Metryka gotowa do opisowego porównania profili symulacji.",
                ),
                "limitations": metadata.get(
                    "limitations_pl",
                    "Wynik jest proxy symulacyjnym, nie samodzielnym markerem klinicznym.",
                ),
            }
        )

    bold_rows = (
        (
            "fmri_mean",
            "cały sygnał BOLD",
            "średnia amplituda BOLD proxy",
            "Średnia BOLD opisuje globalny poziom sygnału po modelowaniu hemodynamicznym.",
            "To syntetyczna miara BOLD zależna od HRF i napędu neuronalnego, "
            "bez kalibracji do danych fMRI.",
        ),
        (
            "bold_peak_to_peak",
            "cały sygnał BOLD",
            "amplituda BOLD proxy peak-to-peak",
            "Zakres BOLD pokazuje rozpiętość odpowiedzi hemodynamicznej w symulacji.",
            "Metryka nie obejmuje szumu skanera, filtracji fMRI ani modelowania przestrzennego.",
        ),
    )
    for metric_name, region_or_band, unit, interpretation, limitations in bold_rows:
        if metric_name in metrics:
            rows.append(
                {
                    "modality": "BOLD",
                    "metric": metric_name,
                    "region_or_band": region_or_band,
                    "value": float(metrics[metric_name]),
                    "unit": unit,
                    "profile_groups": ["healthy", "disorder", "lesion"],
                    "interpretation": interpretation,
                    "limitations": limitations,
                }
            )
    return rows


def _format_polish_list(values: list[str]) -> str:
    """Zwraca czytelny opis listy pojęć używany w komentarzu edukacyjnym."""
    cleaned_values = [str(value) for value in values if str(value).strip()]
    if not cleaned_values:
        return "brak wskazanych elementów"
    if len(cleaned_values) == 1:
        return cleaned_values[0]
    return ", ".join(cleaned_values[:-1]) + f" oraz {cleaned_values[-1]}"


CONDITION_LABELS_PL = {
    "standard": "standard",
    "deviant": "dewiant",
    "congruent": "zgodny",
    "incongruent": "niezgodny",
    "go": "go",
    "nogo": "no-go",
    "target": "cel",
    "non_target": "bodziec niecelowy",
}
TRIAL_METRIC_KEYS = (
    "reaction_time_s",
    "correct",
    "error_type",
    "surprise_index",
    "habituation_level",
    "readaptation_latency",
    "tone_hz",
    "abs_delta",
)


def _condition_label_pl(condition: Any) -> str:
    """Zwróć polską etykietę warunku eksperymentalnego.

    Parameters
    ----------
    condition:
        Techniczna nazwa warunku zapisana w zdarzeniu albo wyniku trialu.

    Returns
    -------
    str
        Polska etykieta warunku przeznaczona do raportu użytkownika.
    """
    condition_text = str(condition or "n/a")
    return CONDITION_LABELS_PL.get(condition_text, condition_text)


def _clinical_profile_label(clinical_profile: dict[str, Any] | None) -> str:
    """Zbuduj krótki opis profilu klinicznego do wiersza trialu.

    Parameters
    ----------
    clinical_profile:
        Metadane profilu klinicznego z konfiguracji eksperymentu.

    Returns
    -------
    str
        Jednowierszowy opis profilu lub ``n/a``, gdy profil nie jest dostępny.
    """
    if not isinstance(clinical_profile, dict) or not clinical_profile:
        return "n/a"
    profile_name = clinical_profile.get("display_name") or clinical_profile.get("id")
    mechanism = clinical_profile.get("mechanism")
    if profile_name and mechanism:
        return f"{profile_name} — {mechanism}"
    return str(profile_name or mechanism or "n/a")


def _format_trial_metric_value(value: Any) -> str:
    """Sformatuj wartość metryki trialu w sposób czytelny po polsku.

    Parameters
    ----------
    value:
        Wartość metryki zapisana w szczegółach zdarzenia.

    Returns
    -------
    str
        Krótki tekst metryki bez utraty istotnych cyfr.
    """
    if isinstance(value, bool):
        return "tak" if value else "nie"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _metric_summary_from_mapping(mapping: dict[str, Any]) -> list[str]:
    """Wyciągnij najważniejsze metryki trialu z pojedynczego słownika.

    Parameters
    ----------
    mapping:
        Słownik szczegółów zdarzenia lub payload bodźca.

    Returns
    -------
    list[str]
        Lista krótkich opisów ``nazwa=wartość`` w stabilnej kolejności.
    """
    metrics: list[str] = []
    for metric_name in TRIAL_METRIC_KEYS:
        if metric_name in mapping and mapping[metric_name] not in {None, "n/a"}:
            metrics.append(
                f"{metric_name}={_format_trial_metric_value(mapping[metric_name])}"
            )
    return metrics


def _build_trial_comment(row: dict[str, str]) -> str:
    """Zbuduj krótki komentarz dydaktyczny dla trialu.

    Parameters
    ----------
    row:
        Ujednolicony wiersz trialu z polami używanymi w eksporcie i GUI.

    Returns
    -------
    str
        Jednozdaniowy komentarz po polsku łączący warunek, zachowanie i aktywność.
    """
    condition = row.get("condition", "n/a")
    behavior = row.get("behavioral_outcome", "n/a")
    active_regions = row.get("active_regions", "n/a")
    if "niepopraw" in behavior.lower() or "błąd" in behavior.lower():
        return (
            f"Trial w warunku {condition} wymaga omówienia błędu razem z aktywnością: "
            f"{active_regions}."
        )
    if active_regions not in {
        "n/a",
        "brak aktywnych regionów",
        "brak wskazanych elementów",
    }:
        return (
            f"Trial w warunku {condition} łączy wynik behawioralny z regionami: "
            f"{active_regions}."
        )
    return (
        f"Trial w warunku {condition} interpretuj głównie przez wynik behawioralny: "
        f"{behavior}."
    )


def build_trial_observation_rows(
    event_timeline: list[dict[str, Any]],
    *,
    clinical_profile: dict[str, Any] | None = None,
    max_trials: int = 20,
) -> list[dict[str, str]]:
    """Zbuduj wspólne wiersze obserwacji triali dla Markdown, eksportu i GUI.

    Parameters
    ----------
    event_timeline:
        Chronologiczna oś czasu zdarzeń wygenerowana przez silnik symulacji.
    clinical_profile:
        Profil kliniczny użyty w eksperymencie; wartość trafia do każdego wiersza,
        aby raport i panel obserwacji pokazywały ten sam kontekst kliniczny.
    max_trials:
        Maksymalna liczba triali opisywana w raporcie.

    Returns
    -------
    list[dict[str, str]]
        Wiersze z polami: czas, warunek, aktywne regiony, profil kliniczny,
        wynik behawioralny, najważniejsze metryki i komentarz po polsku.
    """
    groups = _group_event_timeline_by_trial(event_timeline)
    profile_label = _clinical_profile_label(clinical_profile)
    rows: list[dict[str, str]] = []
    for group in groups[:max_trials]:
        stimulus = group.get("stimulus") or {}
        response = group.get("response") or {}
        correctness = group.get("correctness") or {}
        activity_changes = group.get("activity_changes") or []
        stimulus_details = stimulus.get("details") or {}
        response_details = response.get("details") or {}
        correctness_details = correctness.get("details") or {}

        active_regions: list[str] = []
        regional_input = stimulus_details.get("regional_input") or {}
        if isinstance(regional_input, dict):
            for region, value in regional_input.items():
                if float(value or 0.0) != 0.0:
                    active_regions.append(
                        f"{region} ({_format_trial_metric_value(value)})"
                    )
        for event in activity_changes[:3]:
            details = event.get("details") or {}
            region = details.get("region")
            if region:
                active_regions.append(str(region))

        metric_items: list[str] = []
        for mapping in (
            stimulus_details.get("payload") or {},
            response_details,
            correctness_details,
        ):
            if isinstance(mapping, dict):
                metric_items.extend(_metric_summary_from_mapping(mapping))
        for event in activity_changes[:2]:
            details = event.get("details") or {}
            if isinstance(details, dict):
                metric_items.extend(_metric_summary_from_mapping(details))
        unique_metrics = list(dict.fromkeys(metric_items))

        if correctness:
            behavioral_outcome = str(
                correctness.get("description_pl")
                or response.get("description_pl")
                or "n/a"
            )
        else:
            behavioral_outcome = str(response.get("description_pl") or "brak wyniku")

        row = {
            "trial_id": str(group.get("trial_id", "n/a")),
            "time_s": _format_trial_metric_value(group.get("first_time_s", "n/a")),
            "condition": _condition_label_pl(group.get("condition", "n/a")),
            "stimulus": str(stimulus.get("description_pl") or "brak zapisanego bodźca"),
            "response": str(
                response.get("description_pl") or "brak zapisanej odpowiedzi"
            ),
            "correctness": str(
                correctness.get("description_pl") or "brak oceny poprawności"
            ),
            "activity": "; ".join(
                str(event.get("description_pl") or "brak opisu")
                for event in activity_changes[:3]
            )
            or "brak istotnej zmiany w progu raportu",
            "active_regions": _format_polish_list(list(dict.fromkeys(active_regions))),
            "clinical_profile": profile_label,
            "behavioral_outcome": behavioral_outcome,
            "key_metrics": "; ".join(unique_metrics[:8]) or "brak metryk trialu",
            "comment_pl": "",
        }
        row["comment_pl"] = _build_trial_comment(row)
        rows.append(row)
    return rows


def _group_event_timeline_by_trial(
    event_timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Grupuje zdarzenia osi czasu według triali w kolejności interpretacyjnej.

    Parameters
    ----------
    event_timeline:
        Chronologiczna lista zdarzeń z ujednoliconymi polami ``trial_id`` i
        ``condition``.

    Returns
    -------
    list[dict[str, Any]]
        Lista grup triali z polami: bodziec, odpowiedź, ocena poprawności,
        zmiany aktywności i komentarz mechanizmu.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for event in event_timeline:
        trial_id = event.get("trial_id", "n/a")
        if trial_id in {None, "n/a"}:
            continue
        trial_key = str(trial_id)
        group = grouped.setdefault(
            trial_key,
            {
                "trial_id": trial_id,
                "condition": event.get("condition") or "n/a",
                "stimulus": None,
                "response": None,
                "correctness": None,
                "activity_changes": [],
                "mechanism_comments": [],
                "first_time_s": event.get("time_s", 0.0) or 0.0,
            },
        )
        group["condition"] = event.get("condition") or group["condition"]
        group["first_time_s"] = min(
            float(group["first_time_s"]), float(event.get("time_s", 0.0) or 0.0)
        )
        event_type = str(event.get("event_type", ""))
        if event_type == "stimulus_onset":
            group["stimulus"] = event
        elif event_type == "response":
            group["response"] = event
        elif event_type in {"correctness", "error"}:
            group["correctness"] = event
        elif event_type == "significant_region_activity_change":
            group["activity_changes"].append(event)
        elif event_type in {"neuromodulation_change", "lesion_pathology_event"}:
            group["mechanism_comments"].append(event)

    return sorted(grouped.values(), key=lambda item: float(item["first_time_s"]))


def _trial_group_markdown_lines(
    event_timeline: list[dict[str, Any]],
    *,
    clinical_profile: dict[str, Any] | None = None,
    max_trials: int = 20,
) -> list[str]:
    """Buduje polskie linie Markdown z grupami triali i komentarzem mechanizmu.

    Parameters
    ----------
    event_timeline:
        Chronologiczna lista zdarzeń eksperymentu.
    max_trials:
        Maksymalna liczba triali opisywana w sekcji Markdown.

    Returns
    -------
    list[str]
        Linie raportu w kolejności: bodziec, odpowiedź, poprawność/błąd,
        zmiana aktywności i komentarz mechanizmu.
    """
    rows = build_trial_observation_rows(
        event_timeline,
        clinical_profile=clinical_profile,
        max_trials=max_trials,
    )
    groups = _group_event_timeline_by_trial(event_timeline)
    if not groups:
        return ["- Brak triali możliwych do pogrupowania."]
    if not rows:
        return [f"- Limit raportu triali wynosi 0; pominięto {len(groups)} triali."]

    lines: list[str] = [
        f"- Liczba triali: {len(groups)}; pokazano: {len(rows)}; "
        f"limit: {max_trials}; pominięto: {max(0, len(groups) - len(rows))}."
    ]
    for row in rows:
        lines.append(
            f"- **Trial {row['trial_id']}** — czas: {row['time_s']} s; "
            f"warunek: {row['condition']}"
        )
        lines.append(f"  - **bodziec**: {row['stimulus']}")
        lines.append(f"  - **odpowiedź**: {row['response']}")
        lines.append(f"  - **błąd/poprawność**: {row['correctness']}")
        lines.append(f"  - **zmiana aktywności**: {row['activity']}")
        lines.append(f"  - **aktywne regiony**: {row['active_regions']}")
        lines.append(f"  - **profil kliniczny**: {row['clinical_profile']}")
        lines.append(f"  - **wynik behawioralny**: {row['behavioral_outcome']}")
        lines.append(f"  - **najważniejsze metryki**: {row['key_metrics']}")
        lines.append(f"  - **komentarz mechanizmu**: {row['comment_pl']}")
    if len(groups) > max_trials:
        lines.append(f"- ... pominięto {len(groups) - max_trials} dalszych triali.")
    return lines


def _build_roving_trial_by_trial_rows(
    trial_results: list[dict[str, Any]],
    *,
    clinical_profile: dict[str, Any] | None,
) -> list[dict[str, object]]:
    """Buduje szczegółowe wiersze trial-by-trial dla roving oddball.

    Parameters
    ----------
    trial_results:
        Wyniki triali zwrócone przez silnik symulacji.
    clinical_profile:
        Profil kliniczny użyty do komentarza mechanizmu.

    Returns
    -------
    list[dict[str, object]]
        Wiersze z numerem triala, standardem, dewiantem, nowym standardem,
        odpowiedzią modelu, metrykami i komentarzem mechanizmu profilu.
    """
    profile = clinical_profile or {}
    mechanism_metadata = _roving_mechanism_metadata(profile)
    mechanism_comment = str(
        mechanism_metadata.get(
            "mechanism_comment", profile.get("mechanism", "brak opisu mechanizmu")
        )
    )
    rows: list[dict[str, object]] = []
    for index, result in enumerate(trial_results):
        condition = str(result.get("condition", "n/a"))
        metrics = result.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {
                key: result[key]
                for key in TRIAL_METRIC_KEYS
                if key in result and result[key] is not None
            }
        trial_num_raw = result.get("trial_number")
        if trial_num_raw is None or trial_num_raw == "n/a":
            trial_num_raw = result.get("trial_id")
        try:
            trial_number = int(trial_num_raw) if trial_num_raw is not None else index
        except (ValueError, TypeError):
            trial_number = index
        rows.append(
            {
                "trial_number": trial_number,
                "trial_id": result.get("trial_id", index),
                "standard": condition == "standard",
                "deviant": condition == "deviant",
                "new_standard": bool(result.get("is_new_standard", False)),
                "stimulus_type": result.get("stimulus_type", condition),
                "tone_hz": result.get("tone_hz", "n/a"),
                "model_response": result.get(
                    "model_response", result.get("observed_response")
                ),
                "expected_response": result.get("expected_response"),
                "correct": bool(result.get("correct", False)),
                "metrics": dict(metrics),
                "profile_id": result.get("profile_id", profile.get("id", "n/a")),
                "scenario": result.get("scenario", "roving_oddball"),
                "mechanism_comment": mechanism_comment,
            }
        )
    return rows


def _mean_regional_response_amplitude(trial_results: list[dict[str, Any]]) -> float:
    """Liczy prosty proxy amplitudy odpowiedzi z wejść regionalnych triali.

    Parameters
    ----------
    trial_results:
        Lista wyników triali z polem ``regional_input`` zapisanym przez silnik.

    Returns
    -------
    float
        Średnia z wartości bezwzględnych wejść regionalnych. Wartość jest
        raportowym proxy amplitudy odpowiedzi, a nie empiryczną amplitudą ERP.
    """
    amplitudes: list[float] = []
    for result in trial_results:
        regional_input = result.get("regional_input") or {}
        if not isinstance(regional_input, dict) or not regional_input:
            continue
        amplitudes.append(
            float(np.mean([abs(float(value)) for value in regional_input.values()]))
        )
    return round(float(np.mean(amplitudes)), 6) if amplitudes else 0.0


def _roving_mechanism_metadata(profile: dict[str, Any] | None) -> dict[str, Any]:
    """Zwraca zwalidowane metadane mechanizmu amplituda-latencja dla profilu."""
    if not isinstance(profile, dict):
        return {}
    metadata = profile.get("amplitude_latency_mechanism")
    return dict(metadata) if isinstance(metadata, dict) else {}


def _build_amplitude_latency_mechanism_section(
    *,
    trial_results: list[dict[str, Any]],
    summary: dict[str, object],
    clinical_profile: dict[str, Any] | None,
) -> dict[str, object]:
    """Buduje sekcję łączącą amplitudę, readaptację i komentarz mechanizmu.

    Parameters
    ----------
    trial_results:
        Wyniki triali roving oddball.
    summary:
        Agregaty sekwencji wyliczone w ``build_roving_oddball_report``.
    clinical_profile:
        Metadane profilu klinicznego z konfiguracji.

    Returns
    -------
    dict[str, object]
        Sekcja raportu ``amplitude_latency_mechanism`` dla scenariusza
        ``roving_oddball``.
    """
    clinical_profile = clinical_profile or {}
    standard_trials: list[dict[str, Any]] = []
    deviant_trials: list[dict[str, Any]] = []
    for result in trial_results:
        condition = result.get("condition")
        if condition == "standard":
            standard_trials.append(result)
        elif condition == "deviant":
            deviant_trials.append(result)
    standard_amplitude = _mean_regional_response_amplitude(standard_trials)
    deviant_amplitude = _mean_regional_response_amplitude(deviant_trials)
    response_amplitude = _mean_regional_response_amplitude(trial_results)
    metadata = _roving_mechanism_metadata(clinical_profile)
    qualitative_threshold_source = metadata.get("qualitative_threshold")
    if qualitative_threshold_source is None:
        severity_level = clinical_profile.get("severity_level")
        if isinstance(severity_level, dict):
            qualitative_threshold_source = severity_level.get("large")
    if qualitative_threshold_source is None:
        raise ValueError(
            "Profil kliniczny musi mieć amplitude_latency_mechanism."
            "qualitative_threshold albo severity_level.large."
        )

    return {
        "profile_id": clinical_profile.get("id", summary.get("profile_id", "n/a")),
        "response_amplitude": response_amplitude,
        "standard_response_amplitude": standard_amplitude,
        "deviant_response_amplitude": deviant_amplitude,
        "deviant_standard_amplitude_difference": round(
            deviant_amplitude - standard_amplitude, 6
        ),
        "mean_readaptation_latency": summary.get("mean_readaptation_latency", 0.0),
        "expected_amplitude_direction": metadata.get(
            "expected_amplitude_direction", "stable_reference"
        ),
        "expected_readaptation_direction": metadata.get(
            "expected_readaptation_direction", "stable_reference"
        ),
        "qualitative_threshold": float(qualitative_threshold_source),
        "mechanism_comment": metadata.get(
            "mechanism_comment", clinical_profile.get("mechanism", "n/a")
        ),
        "educational_comment": metadata.get(
            "educational_comment",
            "Sekcja łączy proxy amplitudy odpowiedzi z latencją readaptacji; "
            "interpretuj ją jako opis dydaktyczny modelu, nie diagnozę kliniczną.",
        ),
    }


def _require_clinical_severity_thresholds(
    severity_thresholds: dict[str, Any] | None,
) -> dict[str, float]:
    """Zweryfikuj jawne progi jakościowe profilu klinicznego.

    Parameters
    ----------
    severity_thresholds:
        Progi ``small``, ``medium`` i ``large`` zapisane w profilu klinicznym.

    Returns
    -------
    dict[str, float]
        Znormalizowane progi jakościowe.

    Raises
    ------
    ValueError
        Gdy profil nie zawiera kompletnego zestawu progów albo kolejność progów
        jest niespójna.
    """
    if not isinstance(severity_thresholds, dict):
        raise ValueError(
            "clinical_profile.severity_level musi jawnie zawierać progi "
            "small, medium i large."
        )
    missing = [
        key for key in REQUIRED_CLINICAL_SEVERITY_KEYS if key not in severity_thresholds
    ]
    if missing:
        raise ValueError(
            "Brak progów clinical_profile.severity_level: " + ", ".join(missing)
        )

    thresholds = {
        key: float(severity_thresholds[key]) for key in REQUIRED_CLINICAL_SEVERITY_KEYS
    }
    if not thresholds["small"] <= thresholds["medium"] <= thresholds["large"]:
        raise ValueError(
            "Progi clinical_profile.severity_level muszą spełniać "
            "small <= medium <= large."
        )
    return thresholds


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
    thresholds = _require_clinical_severity_thresholds(severity_thresholds)

    if value >= thresholds["large"]:
        return "duża różnica"
    if value >= thresholds["medium"]:
        return "średnia różnica"
    return "mała różnica"


def _format_qualitative_threshold(severity_thresholds: dict[str, Any] | None) -> str:
    """Sformatuj jawne progi profilu jako opis jakościowej skali różnicy.

    Parameters
    ----------
    severity_thresholds:
        Progi ``small``, ``medium`` i ``large`` z metadanych profilu klinicznego.

    Returns
    -------
    str
        Polski opis progów używany w raporcie różnic klinicznych.
    """
    thresholds = _require_clinical_severity_thresholds(severity_thresholds)
    ordered = REQUIRED_CLINICAL_SEVERITY_KEYS
    labels = {"small": "mała", "medium": "średnia", "large": "duża"}
    parts = []
    for key in ordered:
        val = thresholds[key]
        parts.append(f"{labels[key]} ≥ {val:.6g}")
    return "; ".join(parts)


def _describe_observed_direction(signed_difference: float) -> str:
    """Opisuje kierunek zmiany aktywności względem profilu referencyjnego."""
    tol = 1e-7
    if signed_difference > tol:
        return "wzrost aktywności"
    if signed_difference < -tol:
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


def _build_baseline_reference_section(profile: dict[str, Any]) -> dict[str, str] | None:
    """Zbuduj opis roli profilu `healthy_v1` w raporcie edukacyjnym.

    Parameters
    ----------
    profile:
        Metadane profilu klinicznego zapisane w payloadzie raportu.

    Returns
    -------
    dict[str, str] | None
        Słownik z polami sekcji baseline albo ``None``, jeśli raport nie
        dotyczy profilu referencyjnego `healthy_v1`.
    """
    if profile.get("id") != "healthy_v1":
        return None

    return {
        "profile_id": "healthy_v1",
        "role_pl": "punkt odniesienia dla porównań profili klinicznych",
        "interpretation_pl": (
            "Profil healthy_v1 opisuje edukacyjny stan bez jawnie modelowanej "
            "patologii i nie jest diagnozą kliniczną ani normą populacyjną."
        ),
        "primary_metric": str(profile.get("primary_metric", "mean_abs_difference")),
        "expected_direction": str(
            profile.get("expected_direction", "stable_reference")
        ),
    }


@dataclass(frozen=True)
class ValidationComplianceEntry:
    """Wiersz zgodności walidacyjnej benchmarku prezentowany w raporcie.

    Parameters
    ----------
    benchmark:
        Techniczna nazwa benchmarku z metadanych i rejestru walidacji.
    level:
        Poziom benchmarku: ``synthetic``, ``educational``,
        ``literature-inspired`` albo ``empirical``.
    tolerance:
        Opis tolerancji akceptowanej dla porównań regresyjnych.
    status:
        Aktualny status benchmarku odczytany z rejestru walidacji.
    last_comparison_result:
        Zwięzłe podsumowanie ostatnich metryk porównania zapisanych w raporcie.
    """

    benchmark: str
    level: str
    tolerance: str
    status: str
    last_comparison_result: str
    qualitative_validation_level: str
    compliance_criteria: str
    limitations: str

    def to_dict(self) -> dict[str, str]:
        """Zwróć wiersz zgodności w formie serializowalnej do JSON.

        Returns
        -------
        dict[str, str]
            Słownik z nazwą benchmarku, poziomem, tolerancją, statusem
            i wynikiem ostatniego porównania.
        """
        return {
            "benchmark": self.benchmark,
            "level": self.level,
            "tolerance": self.tolerance,
            "status": self.status,
            "last_comparison_result": self.last_comparison_result,
            "qualitative_validation_level": self.qualitative_validation_level,
            "compliance_criteria": self.compliance_criteria,
            "limitations": self.limitations,
        }


def _clean_registry_cell(value: str) -> str:
    """Oczyść komórkę tabeli Markdown z prostego formatowania kodowego."""
    return value.strip().strip("`").strip()


def load_validation_metric_registry(
    registry_path: str | Path = DEFAULT_VALIDATION_REGISTRY_PATH,
) -> dict[str, dict[str, str]]:
    """Załaduj rejestr metryk raportowych z dokumentu walidacji.

    Parameters
    ----------
    registry_path:
        Ścieżka do pliku ``docs/validation_registry.md`` zawierającego tabelę
        metryk z polskimi etykietami, źródłem danych walidacyjnych, zakresem
        interpretacji i ograniczeniami.

    Returns
    -------
    dict[str, dict[str, str]]
        Rejestr indeksowany techniczną nazwą metryki raportowanej.

    Raises
    ------
    ValueError
        Gdy plik rejestru nie istnieje albo tabela metryk jest pusta.
    """
    path = Path(registry_path)
    if not path.exists():
        return {}

    entries: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line.startswith("|") or "---" in stripped_line:
            continue
        cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
        if len(cells) != len(VALIDATION_METRIC_REGISTRY_COLUMNS):
            continue
        if cells[0].lower() == "nazwa techniczna":
            continue

        row = {
            column: _clean_registry_cell(value)
            for column, value in zip(VALIDATION_METRIC_REGISTRY_COLUMNS, cells)
        }
        metric_name = row["technical_name"]
        if metric_name:
            entries[metric_name] = row

    if not entries:
        raise ValueError(f"Rejestr walidacji nie zawiera wpisów metryk: {path}")
    return entries


def _collect_interpretation_limitations(
    metrics: dict[str, Any],
    registry_path: str | Path = DEFAULT_VALIDATION_REGISTRY_PATH,
) -> list[dict[str, str]]:
    """Zbierz ograniczenia interpretacji dla metryk obecnych w raporcie.

    Parameters
    ----------
    metrics:
        Słownik metryk raportowanych w sekcji ``metrics``.
    registry_path:
        Ścieżka do rejestru walidacji z tabelą metryk.

    Returns
    -------
    list[dict[str, str]]
        Wiersze z techniczną nazwą, polską etykietą, zakresem interpretacji
        i ograniczeniami metryki.

    Raises
    ------
    ValueError
        Gdy raportowana metryka nie ma wpisu w rejestrze metryk.
    """
    registry = load_validation_metric_registry(registry_path)
    rows: list[dict[str, str]] = []
    for metric_name in metrics:
        registry_entry = registry.get(str(metric_name))
        if registry_entry is None:
            raise ValueError(
                "Brak wpisu w rejestrze walidacji dla metryki: " f"{metric_name}"
            )
        rows.append(
            {
                "metric": str(metric_name),
                "polish_label": registry_entry.get("polish_label", "n/a"),
                "interpretation_range": registry_entry.get(
                    "interpretation_range", "n/a"
                ),
                "limitations": registry_entry.get("limitations", "n/a"),
            }
        )
    return rows


def _resolve_interpretation_limitations(
    payload: dict[str, Any],
) -> list[dict[str, str]]:
    """Zwróć sekcję ograniczeń interpretacji dla aktualnego payloadu raportu.

    Parameters
    ----------
    payload:
        Dane raportu zawierające metryki albo gotową sekcję
        ``interpretation_limitations``.

    Returns
    -------
    list[dict[str, str]]
        Wiersze sekcji „Ograniczenia interpretacji”.
    """
    existing_rows = payload.get("interpretation_limitations")
    if existing_rows is not None:
        return list(existing_rows)

    metrics = payload.get("metrics", {})
    if not metrics:
        return []
    return _collect_interpretation_limitations(metrics)


def load_validation_registry(
    registry_path: str | Path = DEFAULT_VALIDATION_REGISTRY_PATH,
) -> dict[str, dict[str, str]]:
    """Załaduj rejestr walidacji benchmarków z tabeli Markdown.

    Parameters
    ----------
    registry_path:
        Ścieżka do pliku ``docs/validation_registry.md`` zawierającego tabelę
        z kolumnami benchmarku, poziomu, tolerancji i statusu.

    Returns
    -------
    dict[str, dict[str, str]]
        Rejestr indeksowany nazwą benchmarku. Każdy wpis zawiera m.in. pola
        ``level``, ``tolerance`` i ``status``.

    Raises
    ------
    ValueError
        Gdy plik rejestru nie istnieje albo tabela nie zawiera żadnego wpisu.
    """
    path = Path(registry_path)
    if not path.exists():
        raise ValueError(f"Rejestr walidacji nie istnieje: {path}")

    entries: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line.startswith("|") or "---" in stripped_line:
            continue
        cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
        if len(cells) != len(VALIDATION_REGISTRY_COLUMNS):
            continue
        if cells[0].lower() == "benchmark":
            continue

        row = {
            column: _clean_registry_cell(value)
            for column, value in zip(VALIDATION_REGISTRY_COLUMNS, cells)
        }
        benchmark_name = row["benchmark"]
        if benchmark_name:
            entries[benchmark_name] = row

    if not entries:
        raise ValueError(f"Rejestr walidacji nie zawiera wpisów benchmarków: {path}")
    return entries


def _summarize_last_comparison(benchmark_name: str, comparison: dict[str, Any]) -> str:
    """Zbuduj krótki opis ostatnich metryk porównania dla benchmarku.

    Parameters
    ----------
    benchmark_name:
        Nazwa benchmarku, np. ``eeg`` albo ``behavior``.
    comparison:
        Słownik metryk porównawczych zapisany w raporcie, z kluczami
        prefiksowanymi nazwą benchmarku.

    Returns
    -------
    str
        Opis w formacie ``metryka=wartość`` albo ``n/a``, jeżeli raport nie
        zawiera jeszcze porównania dla danego benchmarku.
    """
    prefix = f"{benchmark_name}_"
    benchmark_metrics = {
        key.removeprefix(prefix): value
        for key, value in comparison.items()
        if key.startswith(prefix)
    }
    if not benchmark_metrics:
        return "n/a"

    preferred_order = ("mae", "rmse", "correlation")
    ordered_names = [
        metric_name
        for metric_name in preferred_order
        if metric_name in benchmark_metrics
    ]
    ordered_names.extend(
        sorted(name for name in benchmark_metrics if name not in preferred_order)
    )
    return "; ".join(
        (
            f"{metric_name}={value:.4f}"
            if isinstance(value, (float, np.floating))
            else f"{metric_name}={value}"
        )
        for metric_name in ordered_names
        if (value := benchmark_metrics[metric_name]) is not None
    )


def collect_validation_compliance(
    benchmark_metadata: dict[str, dict[str, object]],
    comparison: dict[str, Any] | None = None,
    registry_path: str | Path = DEFAULT_VALIDATION_REGISTRY_PATH,
) -> list[dict[str, str]]:
    """Połącz metadane benchmarków, rejestr walidacji i wyniki porównań.

    Parameters
    ----------
    benchmark_metadata:
        Metadane benchmarków z ``benchmark_metadata.json`` zapisane w payloadzie
        raportu. Poziom z tych metadanych pozostaje źródłem prawdy dla
        rozróżnienia ``synthetic``, ``educational``, ``literature-inspired``
        i ``empirical``.
    comparison:
        Ostatnie metryki porównawcze raportu, zwykle wynik funkcji
        ``comparative_report`` z prefiksami nazw benchmarków.
    registry_path:
        Ścieżka do tabelarycznego rejestru walidacji.

    Returns
    -------
    list[dict[str, str]]
        Lista wierszy sekcji „Zgodność walidacyjna” gotowa do serializacji.

    Raises
    ------
    ValueError
        Gdy metadane wskazują benchmark bez wpisu w rejestrze walidacji.
    """
    registry = load_validation_registry(registry_path)
    comparison_payload = comparison or {}
    entries: list[dict[str, str]] = []

    for benchmark_name, metadata in benchmark_metadata.items():
        registry_entry = registry.get(benchmark_name)
        if registry_entry is None:
            raise ValueError(
                "Brak wpisu w rejestrze walidacji dla benchmarku: " f"{benchmark_name}"
            )

        metadata_level = str(metadata.get("level", "n/a"))
        registry_level = registry_entry.get("level", "n/a")
        status = registry_entry.get("status", "n/a")
        if registry_level != metadata_level:
            status = f"{status} (uwaga: poziom w rejestrze: {registry_level})"

        entries.append(
            ValidationComplianceEntry(
                benchmark=benchmark_name,
                level=metadata_level,
                tolerance=registry_entry.get("tolerance", "n/a"),
                status=status,
                last_comparison_result=_summarize_last_comparison(
                    benchmark_name, comparison_payload
                ),
                qualitative_validation_level=registry_entry.get(
                    "qualitative_validation_level", "n/a"
                ),
                compliance_criteria=metadata.get(
                    "compliance_criteria",
                    registry_entry.get("compliance_criteria", "n/a"),
                ),
                limitations=metadata.get(
                    "limitations", registry_entry.get("limitations", "n/a")
                ),
            ).to_dict()
        )
    return entries


def _resolve_validation_compliance_rows(
    payload: dict[str, Any],
) -> list[dict[str, str]]:
    """Zwróć wiersze zgodności walidacyjnej dla aktualnego payloadu raportu.

    Parameters
    ----------
    payload:
        Dane raportu zawierające opcjonalne sekcje ``benchmark_metadata``,
        ``comparison`` i ``validation_compliance``.

    Returns
    -------
    list[dict[str, str]]
        Gotowe wiersze sekcji „Zgodność walidacyjna”. Jeśli payload zawiera już
        tę sekcję, funkcja zwraca ją bez ponownego odczytu rejestru.
    """
    existing_rows = payload.get("validation_compliance")
    if existing_rows is not None:
        return list(existing_rows)

    benchmark_metadata = payload.get("benchmark_metadata")
    if not benchmark_metadata:
        return []

    return collect_validation_compliance(
        benchmark_metadata=benchmark_metadata,
        comparison=payload.get("comparison", {}),
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
        validation_compliance = _resolve_validation_compliance_rows(self.payload)
        lines = ["# Raport analizy", "", "## Metryki"]
        for name, value in metrics.items():
            lines.append(f"- **{name}**: {value}")
        lines.append("")

        interpretation_limitations = _resolve_interpretation_limitations(self.payload)
        if interpretation_limitations:
            lines.append("## Ograniczenia interpretacji")
            lines.append(
                "| Metryka | Polska etykieta | Zakres interpretacji | Ograniczenia |"
            )
            lines.append("| --- | --- | --- | --- |")
            for item in interpretation_limitations:
                lines.append(
                    f"| {item.get('metric', 'n/a')} "
                    f"| {item.get('polish_label', 'n/a')} "
                    f"| {item.get('interpretation_range', 'n/a')} "
                    f"| {item.get('limitations', 'n/a')} |"
                )
            lines.append("")

        eeg_bold_sections = self.payload.get("eeg_bold_sections", [])
        if eeg_bold_sections:
            lines.append("## Sekcje EEG/BOLD gotowe do raportowania")
            lines.append(
                "| Modalność | Metryka | Region/pasmo | Wartość | Jednostka | "
                "Interpretacja | Ograniczenia |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for item in eeg_bold_sections:
                lines.append(
                    f"| {item.get('modality', 'n/a')} "
                    f"| {item.get('metric', 'n/a')} "
                    f"| {item.get('region_or_band', 'n/a')} "
                    f"| {item.get('value', 'n/a')} "
                    f"| {item.get('unit', 'n/a')} "
                    f"| {item.get('interpretation', 'n/a')} "
                    f"| {item.get('limitations', 'n/a')} |"
                )
            lines.append("")

        baseline_reference = _build_baseline_reference_section(
            self.payload.get("clinical_profile", {})
        )
        if baseline_reference:
            lines.append("## Baseline healthy_v1")
            lines.append(f"- **rola**: {baseline_reference['role_pl']}")
            lines.append(
                f"- **interpretacja**: {baseline_reference['interpretation_pl']}"
            )
            lines.append(
                f"- **metryka główna**: {baseline_reference['primary_metric']}"
            )
            lines.append(
                f"- **oczekiwany kierunek**: "
                f"{baseline_reference['expected_direction']}"
            )
            lines.append("")

        if benchmark_metadata:
            lines.append("## Status walidacji")
            for benchmark_name, metadata in benchmark_metadata.items():
                level = metadata.get("level", "n/a")
                origin = metadata.get("comparison_origin_pl", "syntetyczny")
                if level == "empirical":
                    status = "walidacja empiryczna na danych referencyjnych"
                elif level == "literature-inspired":
                    status = "walidacja inspirowana literaturą bez danych empirycznych"
                elif level == "educational":
                    status = "walidacja edukacyjna bez danych empirycznych"
                else:
                    status = "walidacja syntetyczna bez danych empirycznych"
                lines.append(
                    f"- **{benchmark_name}**: {status} "
                    f"(poziom: {level}, charakter: {origin})"
                )
            lines.append("")
        if validation_compliance:
            lines.append("## Zgodność walidacyjna")
            lines.append(
                "| Benchmark | Poziom | Poziom walidacji jakościowej | "
                "Kryteria zgodności | Tolerancja | Ograniczenia | Status | "
                "Wynik ostatniego porównania |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
            for item in validation_compliance:
                lines.append(
                    f"| {item.get('benchmark', 'n/a')} "
                    f"| {item.get('level', 'n/a')} "
                    f"| {item.get('qualitative_validation_level', 'n/a')} "
                    f"| {item.get('compliance_criteria', 'n/a')} "
                    f"| {item.get('tolerance', 'n/a')} "
                    f"| {item.get('limitations', 'n/a')} "
                    f"| {item.get('status', 'n/a')} "
                    f"| {item.get('last_comparison_result', 'n/a')} |"
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
                lines.append(
                    f"  - **kryteria zgodności**: "
                    f"{metadata.get('compliance_criteria', 'n/a')}"
                )
                compliance_checks = metadata.get("compliance_checks")
                if compliance_checks:
                    lines.append(
                        "  - **strukturalne kryteria zgodności**: "
                        f"{json.dumps(compliance_checks, ensure_ascii=False)}"
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
            lines.extend(
                [
                    "",
                    "### Grupy triali: bodziec → odpowiedź → wynik → aktywność → mechanizm",
                ]
            )
            analysis_config = self.payload.get("analysis", {})
            max_report_trials = 20
            if isinstance(analysis_config, dict):
                configured_limit = analysis_config.get("max_report_trials", 20)
                if isinstance(configured_limit, int) and not isinstance(
                    configured_limit, bool
                ):
                    max_report_trials = max(0, configured_limit)
            lines.extend(
                _trial_group_markdown_lines(
                    event_timeline,
                    clinical_profile=self.payload.get("clinical_profile", {}),
                    max_trials=max_report_trials,
                )
            )
            lines.extend(["", "### Chronologiczny skrót zdarzeń"])
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
            lines.append(
                f"- **żądany tryb SNN**: "
                f"{snn_comparison.get('requested_mode', 'n/a')}"
            )
            computed_modes = snn_comparison.get("computed_modes") or []
            lines.append(
                f"- **policzone warianty**: "
                f"{', '.join(computed_modes) if computed_modes else 'n/a'}"
            )
            lines.append(
                "- **zakres porównania**: "
                f"{snn_comparison.get('comparison_scope_pl', 'n/a')}"
            )
            comparison_note = snn_comparison.get("comparison_note_pl")
            if comparison_note:
                lines.append(f"- **uwaga porównawcza**: {comparison_note}")
            elif snn_comparison.get("requested_mode") == "report_only":
                lines.append(
                    "- **uwaga porównawcza**: "
                    "closed_loop_snn jest dodatkowym wariantem porównawczym liczonym "
                    "także wtedy, gdy żądany tryb SNN to report_only."
                )
            lines.append(f"- **sync_dt [s]**: {snn_comparison.get('sync_dt_s', 'n/a')}")
            lines.append(
                f"- **maksymalna amplituda sprzężenia**: "
                f"{snn_comparison.get('max_feedback_amplitude', 'n/a')}"
            )
            feedback_warning = (
                snn_comparison.get("max_feedback_amplitude_warning") or {}
            )
            if feedback_warning:
                lines.append(
                    "- **limit ostrzegawczy amplitudy sprzężenia**: "
                    f"{feedback_warning.get('level', 'n/a')} — "
                    f"{feedback_warning.get('message_pl', 'n/a')} "
                    f"(informacyjny ≥ {feedback_warning.get('notice_limit', 'n/a')}, "
                    f"ostrzeżenie ≥ {feedback_warning.get('warning_limit', 'n/a')})"
                )
            lines.append(
                f"- **jednostki wejścia/wyjścia**: "
                f"{snn_comparison.get('input_rate_unit', 'n/a')} / "
                f"{snn_comparison.get('output_activity_unit', 'n/a')}"
            )
            metric_disclaimer = snn_comparison.get(
                "metric_disclaimer_pl",
                "metryka demonstracyjna SNN; nie służy do interpretacji biologicznej",
            )
            lines.append(f"- **disclaimer metryk SNN**: {metric_disclaimer}")
            mode_costs = snn_comparison.get("mode_costs") or {}
            if mode_costs:
                lines.append("- **koszt obliczeniowy wariantów SNN**")
                for mode_name in ("baseline", "report_only_snn", "closed_loop_snn"):
                    if mode_name in mode_costs:
                        cost_stats = mode_costs[mode_name]
                        lines.append(
                            f"  - **{mode_name}**: "
                            f"model_runs={cost_stats.get('model_runs', 'n/a')}, "
                            f"simulated_steps={cost_stats.get('simulated_steps', 'n/a')}, "
                            f"snn_updates={cost_stats.get('snn_updates', 'n/a')}, "
                            f"feedback_applications="
                            f"{cost_stats.get('feedback_applications', 'n/a')}"
                        )
            mode_metrics = snn_comparison.get("mode_metrics") or {}
            if mode_metrics:
                for mode_name in ("baseline", "report_only_snn", "closed_loop_snn"):
                    if mode_name in mode_metrics:
                        lines.append(f"- **{mode_name}**")
                        for region, stats in mode_metrics[mode_name].items():
                            lines.append(f"  - **{region}**")
                            for metric_name, metric_value in stats.items():
                                lines.append(
                                    f"    - {metric_name}: {metric_value} "
                                    f"({metric_disclaimer})"
                                )
            else:
                for region, stats in (
                    snn_comparison.get("region_differences") or {}
                ).items():
                    lines.append(f"- **{region}**")
                    lines.append(
                        f"  - średnia aktywność bez SNN: "
                        f"{stats.get('mean_without_snn', 'n/a')} "
                        f"({metric_disclaimer})"
                    )
                    lines.append(
                        f"  - średnia aktywność z SNN: "
                        f"{stats.get('mean_with_snn', 'n/a')} "
                        f"({metric_disclaimer})"
                    )
                    lines.append(
                        f"  - średnia różnica bezwzględna: "
                        f"{stats.get('mean_abs_difference', 'n/a')} "
                        f"({metric_disclaimer})"
                    )
                    lines.append(
                        f"  - maksymalna różnica bezwzględna: "
                        f"{stats.get('max_abs_difference', 'n/a')} "
                        f"({metric_disclaimer})"
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
                f"- **latencja readaptacji**: "
                f"{roving_report.get('mean_readaptation_latency', 'n/a')}"
            )
            mechanism = roving_report.get("amplitude_latency_mechanism") or {}
            if mechanism:
                lines.extend(["", "### Amplituda-latencja-mechanizm"])
                lines.append(f"- **profil**: {mechanism.get('profile_id', 'n/a')}")
                lines.append(
                    f"- **amplituda odpowiedzi proxy**: "
                    f"{mechanism.get('response_amplitude', 'n/a')}"
                )
                lines.append(
                    f"- **różnica amplitudy dewiant-standard**: "
                    f"{mechanism.get('deviant_standard_amplitude_difference', 'n/a')}"
                )
                lines.append(
                    f"- **średnia latencja readaptacji**: "
                    f"{mechanism.get('mean_readaptation_latency', 'n/a')}"
                )
                lines.append(
                    f"- **oczekiwany kierunek amplitudy**: "
                    f"{mechanism.get('expected_amplitude_direction', 'n/a')}"
                )
                lines.append(
                    f"- **oczekiwany kierunek readaptacji**: "
                    f"{mechanism.get('expected_readaptation_direction', 'n/a')}"
                )
                lines.append(
                    f"- **komentarz mechanizmu**: "
                    f"{mechanism.get('mechanism_comment', 'n/a')}"
                )
                lines.append(
                    f"- **komentarz dydaktyczny**: "
                    f"{mechanism.get('educational_comment', 'n/a')}"
                )
            trial_rows = roving_report.get("trial_by_trial") or []
            if trial_rows:
                lines.extend(["", "### Trial-by-trial roving oddball"])
                lines.append(
                    "| Trial | Standard | Dewiant | Nowy standard | Odpowiedź "
                    "| Metryki | Profil/scenariusz | Komentarz mechanizmu |"
                )
                lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
                for row in trial_rows:
                    metrics_text = "; ".join(
                        f"{key}={_format_trial_metric_value(value)}"
                        for key, value in (row.get("metrics") or {}).items()
                    )
                    profile_context = (
                        f"{row.get('profile_id', 'n/a')} / {row.get('scenario', 'n/a')}"
                    )
                    lines.append(
                        f"| {row.get('trial_number', row.get('trial_id', 'n/a'))} "
                        f"| {'tak' if row.get('standard') else 'nie'} "
                        f"| {'tak' if row.get('deviant') else 'nie'} "
                        f"| {'tak' if row.get('new_standard') else 'nie'} "
                        f"| {row.get('model_response', 'brak')} "
                        f"| {metrics_text or 'brak metryk'} "
                        f"| {profile_context} "
                        f"| {row.get('mechanism_comment', 'n/a')} |"
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
                    f"  - latencja readaptacji: "
                    f"{profile.get('mean_readaptation_latency', 'n/a')}"
                )
                mechanism = profile.get("amplitude_latency_mechanism") or {}
                if mechanism:
                    lines.append(
                        f"  - amplituda odpowiedzi proxy: "
                        f"{mechanism.get('response_amplitude', 'n/a')}"
                    )
                    lines.append(
                        f"  - mechanizm profilu: "
                        f"{mechanism.get('mechanism_comment', 'n/a')}"
                    )
            comparisons = roving_profile_comparison.get("comparisons") or []
            if comparisons:
                lines.extend(["", "### Porównanie healthy/disorder/lesion"])
                for item in comparisons:
                    lines.append(
                        f"- **{item.get('reference_profile_id', 'healthy_v1')} → "
                        f"{item.get('profile_id', 'n/a')}** "
                        f"({item.get('profile_group', 'n/a')})"
                    )
                    lines.append(
                        f"  - oczekiwany kierunek amplitudy: "
                        f"{item.get('expected_amplitude_direction', 'n/a')}"
                    )
                    lines.append(
                        f"  - oczekiwany kierunek readaptacji: "
                        f"{item.get('expected_readaptation_direction', 'n/a')}"
                    )
                    lines.append(
                        f"  - obserwowana różnica amplitudy: "
                        f"{item.get('observed_amplitude_difference', 'n/a')}"
                    )
                    lines.append(
                        f"  - obserwowana różnica readaptacji: "
                        f"{item.get('observed_readaptation_difference', 'n/a')}"
                    )
                    lines.append(
                        f"  - kierunek obserwowany: "
                        f"{item.get('observed_difference_comment', 'n/a')}"
                    )
                    lines.append(
                        f"  - próg jakościowy: {item.get('qualitative_threshold', 'n/a')} "
                        f"({item.get('threshold_result', 'n/a')})"
                    )
                    lines.append(
                        f"  - komentarz dydaktyczny: "
                        f"{item.get('educational_comment', 'n/a')}"
                    )

        profile_comparison_table = self.payload.get("profile_comparison_table", [])
        if profile_comparison_table:
            lines.extend(["", "## Tabela porównania profili"])
            lines.append(
                "| Profil | Oczekiwany kierunek | Obserwowany kierunek | "
                "Próg jakościowy | Interpretacja |"
            )
            lines.append("| --- | --- | --- | --- | --- |")
            for row in profile_comparison_table:
                lines.append(
                    f"| {row.get('profile', 'n/a')} "
                    f"| {row.get('expected_direction', 'n/a')} "
                    f"| {row.get('observed_direction', 'n/a')} "
                    f"| {row.get('qualitative_threshold', 'n/a')} "
                    f"| {row.get('interpretation', 'n/a')} |"
                )

        clinical_differences = self.payload.get("clinical_differences", [])
        if clinical_differences:
            lines.extend(["", "## Raport różnic profili klinicznych"])
            for item in clinical_differences:
                lines.append(
                    f"- **profil bazowy**: "
                    f"{item.get('baseline_profile') or item.get('reference_profile_id') or 'n/a'}"
                )
                lines.append(
                    f"  - **profil porównywany**: "
                    f"{item.get('compared_profile') or item.get('profile_id') or 'n/a'}"
                )
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
                    f"  - **próg jakościowy**: "
                    f"{item.get('qualitative_threshold', 'n/a')}"
                )
                lines.append(
                    f"  - **kierunek obserwowany**: "
                    f"{item.get('observed_direction', 'n/a')}"
                )
                lines.append(
                    f"  - **komentarz dydaktyczny**: "
                    f"{item.get('educational_comment', 'n/a')}"
                )
                lines.append(
                    f"  - **zastrzeżenie niediagnostyczne**: "
                    f"{item.get('non_diagnostic_disclaimer', 'n/a')}"
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
        for item in _resolve_interpretation_limitations(self.payload):
            metric_name = item.get("metric", "n/a")
            for field_name in ("polish_label", "interpretation_range", "limitations"):
                rows.append(
                    {
                        "section": "interpretation_limitations",
                        "metric": f"{metric_name}_{field_name}",
                        "value": str(item.get(field_name, "n/a")),
                    }
                )
        for item in self.payload.get("eeg_bold_sections", []):
            metric_name = str(item.get("metric", "n/a"))
            rows.append(
                {
                    "section": "eeg_bold_sections",
                    "metric": metric_name,
                    "value": str(item.get("value", "n/a")),
                }
            )
            for field_name in (
                "modality",
                "region_or_band",
                "unit",
                "interpretation",
                "limitations",
            ):
                rows.append(
                    {
                        "section": "eeg_bold_sections",
                        "metric": f"{metric_name}_{field_name}",
                        "value": str(item.get(field_name, "n/a")),
                    }
                )
        for benchmark_name, metadata in self.payload.get(
            "benchmark_metadata", {}
        ).items():
            level = metadata.get("level", "n/a")
            rows.append(
                {
                    "section": "validation_status",
                    "metric": benchmark_name,
                    "value": str(level),
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
        for item in _resolve_validation_compliance_rows(self.payload):
            benchmark_name = item.get("benchmark", "n/a")
            for metric_name in (
                "level",
                "tolerance",
                "status",
                "last_comparison_result",
            ):
                rows.append(
                    {
                        "section": "validation_compliance",
                        "metric": f"{benchmark_name}_{metric_name}",
                        "value": str(item.get(metric_name, "n/a")),
                    }
                )

        baseline_reference = _build_baseline_reference_section(
            self.payload.get("clinical_profile", {})
        )
        if baseline_reference:
            for metric_name, value in baseline_reference.items():
                rows.append(
                    {
                        "section": "baseline_reference",
                        "metric": metric_name,
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
            for metadata_name in (
                "requested_mode",
                "sync_dt_s",
                "max_feedback_amplitude",
                "max_feedback_amplitude_warning",
                "metric_disclaimer_pl",
                "comparison_scope_pl",
                "comparison_note_pl",
            ):
                rows.append(
                    {
                        "section": "snn_comparison",
                        "metric": metadata_name,
                        "value": str(snn_comparison.get(metadata_name, "n/a")),
                    }
                )
            rows.append(
                {
                    "section": "snn_comparison",
                    "metric": "computed_modes",
                    "value": ",".join(snn_comparison.get("computed_modes") or []),
                }
            )
            mode_costs = snn_comparison.get("mode_costs") or {}
            for mode_name, cost_stats in mode_costs.items():
                for metric_name, metric_value in cost_stats.items():
                    rows.append(
                        {
                            "section": "snn_comparison",
                            "metric": f"{mode_name}_{metric_name}",
                            "value": str(metric_value),
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
            mechanism = roving_report.get("amplitude_latency_mechanism") or {}
            for metric, value in mechanism.items():
                rows.append(
                    {
                        "section": "amplitude_latency_mechanism",
                        "metric": str(metric),
                        "value": str(value),
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
                mechanism = profile.get("amplitude_latency_mechanism") or {}
                for metric, value in mechanism.items():
                    rows.append(
                        {
                            "section": "roving_profile_comparison",
                            "metric": f"{profile_id}_{metric}",
                            "value": str(value),
                        }
                    )
            for item in roving_profile_comparison.get("comparisons") or []:
                profile_id = item.get("profile_id", "n/a")
                for metric, value in item.items():
                    rows.append(
                        {
                            "section": "roving_profile_pair_comparison",
                            "metric": f"{profile_id}_{metric}",
                            "value": str(value),
                        }
                    )

        for row in self.payload.get("profile_comparison_table", []):
            profile_id = row.get("profile", "n/a")
            for metric, value in row.items():
                rows.append(
                    {
                        "section": "profile_comparison_table",
                        "metric": f"{profile_id}_{metric}",
                        "value": str(value),
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
                "baseline_profile",
                "compared_profile",
                "primary_metric",
                "qualitative_threshold",
                "expected_direction",
                "observed_direction",
                "difference_classification",
                "educational_comment",
                "non_diagnostic_disclaimer",
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
    clinical_profile: dict[str, Any] | None = None,
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
    clinical_profile:
        Opcjonalne metadane profilu klinicznego używane do sekcji
        ``amplitude_latency_mechanism``.

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
            "trial_by_trial": [],
            "amplitude_latency_mechanism": _build_amplitude_latency_mechanism_section(
                trial_results=[],
                summary={"profile_id": profile_id, "mean_readaptation_latency": 0.0},
                clinical_profile=clinical_profile,
            ),
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
        "trial_by_trial": _build_roving_trial_by_trial_rows(
            trial_results, clinical_profile=clinical_profile
        ),
    }
    if profile_id is not None:
        summary["profile_id"] = profile_id
    summary["amplitude_latency_mechanism"] = _build_amplitude_latency_mechanism_section(
        trial_results=trial_results,
        summary=summary,
        clinical_profile=clinical_profile,
    )
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
    benchmark_metadata: dict[str, dict[str, object]] | None = None,
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
        benchmark_metadata (dict[str, dict[str, object]] | None): Metadane źródeł,
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
        "band_power_delta": float(bands.summary.get("delta", 0.0)) if bands else 0.0,
        "band_power_theta": float(bands.summary.get("theta", 0.0)) if bands else 0.0,
        "band_power_alpha": float(bands.summary.get("alpha", 0.0)) if bands else 0.0,
        "band_power_beta": float(bands.summary.get("beta", 0.0)) if bands else 0.0,
        "band_power_gamma": float(bands.summary.get("gamma", 0.0)) if bands else 0.0,
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
        "directional_abs_mean": (
            float(flow.summary["directional_abs_mean"]) if flow else 0.0
        ),
        "outgoing_mean": float(flow.summary["outgoing_mean"]) if flow else 0.0,
        "behavior_mean": beh_mean,
        "behavior_std": beh_std,
        "fmri_mean": float(np.mean(fmri)),
        "bold_peak_to_peak": float(np.max(fmri) - np.min(fmri)),
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

    payload = {
        "metrics": metrics,
        "comparison": comparison,
        "eeg_bold_sections": _build_eeg_bold_report_sections(metrics),
        "interpretation_limitations": _collect_interpretation_limitations(metrics),
    }
    if benchmark_metadata is not None:
        payload["benchmark_metadata"] = benchmark_metadata
        payload["validation_compliance"] = collect_validation_compliance(
            benchmark_metadata=benchmark_metadata,
            comparison=comparison,
        )

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
    reference_profile = reference_result.get("clinical_profile", {})
    reference_profile_id = str(reference_profile.get("id", "reference_profile"))
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
        severity_thresholds = _require_clinical_severity_thresholds(
            profile.get("severity_level")
        )
        severity_label = _classify_clinical_difference(
            primary_value, severity_thresholds
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
                "baseline_profile": reference_profile_id,
                "compared_profile": profile.get("id") or profile_id,
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
                "severity_level": severity_thresholds,
                "qualitative_threshold": _format_qualitative_threshold(
                    severity_thresholds
                ),
                "difference_classification": severity_label,
                "educational_comment": educational_comment,
                "non_diagnostic_disclaimer": (
                    "Raport ma charakter dydaktyczny i symulacyjny; nie stanowi "
                    "diagnozy, normy populacyjnej ani rekomendacji klinicznej."
                ),
                "mean_abs_difference": mean_abs_difference,
                "max_abs_difference": max_abs_difference,
            }
        )

    return AnalysisReport(payload={"clinical_differences": differences})
