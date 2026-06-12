"""Eksport opisanych wyników eksperymentu do plików PDF."""

from __future__ import annotations

import datetime
import hashlib
import html
import json
import shutil
import textwrap
from pathlib import Path
from typing import Any

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from brain_core.analysis.reports import AnalysisReport, build_trial_observation_rows
from brain_model.io import REPO_ROOT, collect_environment_info, collect_git_info

A4_FIGSIZE = (8.27, 11.69)
TEXT_LEFT = 0.07
TEXT_TOP = 0.94
LINE_HEIGHT = 0.026
WRAP_WIDTH = 96


def _stringify_value(value: Any) -> str:
    """Zamień wartość raportową na krótki tekst czytelny w polskim PDF.

    Parameters
    ----------
    value:
        Wartość metryki, parametru albo pola raportowego.

    Returns
    -------
    str
        Jednowierszowy tekst z zachowaniem istotnych wartości liczbowych.
    """

    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, list):
        return ", ".join(_stringify_value(item) for item in value) or "brak"
    if isinstance(value, dict):
        return "; ".join(
            f"{key}: {_stringify_value(item)}" for key, item in value.items()
        )
    return str(value)


def _draw_wrapped_text_page(
    pdf: PdfPages,
    title: str,
    paragraphs: list[str],
    footer: str | None = None,
) -> None:
    """Dodaj do PDF stronę tekstową z automatycznym zawijaniem akapitów.

    Parameters
    ----------
    pdf:
        Otwarty obiekt `PdfPages`, do którego dopisywana jest strona.
    title:
        Polski tytuł strony.
    paragraphs:
        Lista akapitów albo linii raportu do pokazania użytkownikowi.
    footer:
        Opcjonalna stopka z informacją o źródle artefaktów.
    """

    fig = Figure(figsize=A4_FIGSIZE)
    axis = fig.add_subplot(111)
    axis.axis("off")
    y_position = TEXT_TOP
    axis.text(
        0.05,
        y_position,
        title,
        fontsize=15,
        fontweight="bold",
        va="top",
    )
    y_position -= LINE_HEIGHT * 2

    for paragraph in paragraphs:
        for raw_line in str(paragraph).splitlines():
            wrapped_lines = textwrap.wrap(raw_line, width=WRAP_WIDTH) or [""]
            for line in wrapped_lines:
                if y_position < 0.08:
                    if footer:
                        axis.text(0.05, 0.04, footer, fontsize=8, va="bottom")
                    pdf.savefig(fig)
                    fig = Figure(figsize=A4_FIGSIZE)
                    axis = fig.add_subplot(111)
                    axis.axis("off")
                    y_position = TEXT_TOP
                    axis.text(
                        0.05,
                        y_position,
                        f"{title} (c.d.)",
                        fontsize=15,
                        fontweight="bold",
                        va="top",
                    )
                    y_position -= LINE_HEIGHT * 2
                axis.text(TEXT_LEFT, y_position, line, fontsize=10.5, va="top")
                y_position -= LINE_HEIGHT
        y_position -= LINE_HEIGHT * 0.35

    if footer:
        axis.text(0.05, 0.04, footer, fontsize=8, va="bottom")
    pdf.savefig(fig)


def _flatten_mapping(mapping: dict[str, Any], prefix: str = "") -> list[str]:
    """Spłaszcz słownik konfiguracji lub metryk do linii `klucz: wartość`.

    Parameters
    ----------
    mapping:
        Słownik z parametrami eksperymentu, metrykami albo profilem klinicznym.
    prefix:
        Prefiks używany rekurencyjnie dla pól zagnieżdżonych.

    Returns
    -------
    list[str]
        Linie tekstu gotowe do umieszczenia na stronie PDF.
    """

    lines: list[str] = []
    for key, value in mapping.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            lines.extend(_flatten_mapping(value, full_key))
        else:
            lines.append(f"{full_key}: {_stringify_value(value)}")
    return lines


def _report_markdown_lines(analysis_report: dict[str, Any]) -> list[str]:
    """Zamień raport analityczny silnika na linie tekstu do PDF.

    Parameters
    ----------
    analysis_report:
        Słownik `analysis_report` zwrócony przez `run_experiment()`.

    Returns
    -------
    list[str]
        Linie raportu Markdown bez odtwarzania logiki protokołów w GUI.
    """

    if not analysis_report:
        return ["Raport analityczny jest pusty dla bieżącego uruchomienia."]
    markdown = AnalysisReport(analysis_report).to_markdown()
    return [line for line in markdown.splitlines() if line.strip()]


def _event_timeline_lines(events: list[dict[str, Any]], limit: int = 40) -> list[str]:
    """Zbuduj opis osi czasu zdarzeń do raportu PDF.

    Parameters
    ----------
    events:
        Lista zdarzeń z pola `event_timeline` wyniku eksperymentu.
    limit:
        Maksymalna liczba zdarzeń wypisywana w PDF, aby raport pozostał czytelny.

    Returns
    -------
    list[str]
        Linie tekstowe z czasem, typem i opisem zdarzenia.
    """

    if not events:
        return ["Brak zdarzeń w `event_timeline` dla bieżącego uruchomienia."]

    lines = [f"Liczba zdarzeń: {len(events)}"]
    for event in events[:limit]:
        lines.append(
            "{time_s} s | {event_type} | {label} | {description}".format(
                time_s=event.get("time_s", "n/a"),
                event_type=event.get("event_type", "n/a"),
                label=event.get("label_pl", "n/a"),
                description=event.get("description_pl", "brak opisu"),
            )
        )
    if len(events) > limit:
        lines.append(f"Pominięto {len(events) - limit} dalszych zdarzeń w skrócie PDF.")
    return lines


def _plot_description(title: str) -> str:
    """Zwróć krótki opis sposobu czytania wykresu w raporcie PDF.

    Parameters
    ----------
    title:
        Tytuł zakładki wykresu w GUI.

    Returns
    -------
    str
        Polski opis interpretacyjny dopisywany przed stroną z wykresem.
    """

    descriptions = {
        "Aktywacje": (
            "Porównaj przebiegi aktywacji modułów w czasie i zestaw je z kanałami "
            "bodźców. Nagłe wzrosty pokazują odpowiedź modelu na zdarzenia."
        ),
        "Zachowanie": (
            "Sprawdź zmienne decyzyjne i markery odpowiedzi, aby ocenić, kiedy model "
            "osiąga próg decyzji lub zmienia dynamikę odpowiedzi."
        ),
        "Oś czasu scenariusza": (
            "Traktuj ten wykres jako mapę faz i zdarzeń eksperymentu; pomaga powiązać "
            "zmiany aktywności z bodźcami."
        ),
        "Kanały scenariusza": (
            "Kanały pokazują natężenie bodźców wejściowych, które silnik wykorzystał "
            "podczas uruchomienia."
        ),
        "Diagnostyka": (
            "Wykres zbiera zmienne diagnostyczne i neuromodulacyjne, pomocne przy "
            "interpretacji stabilności oraz błędu predykcji."
        ),
        "Moc pasm": (
            "Porównaj moc pasm theta, alpha, beta i gamma, aby opisać rytmy "
            "oscylacyjne wygenerowane przez model."
        ),
        "EEG modułów": (
            "Sygnały EEG modułów pokazują syntetyczny ślad aktywności E-I dla "
            "wybranych regionów."
        ),
        "Metryki EEG/BOLD": (
            "Wykres pokazuje gotowe wartości metryk z raportu brain_core. "
            "Jest wyłącznie warstwą prezentacji; interpretacje, jednostki i "
            "ograniczenia znajdują się w sekcji EEG/BOLD raportu."
        ),
    }
    return descriptions.get(
        title,
        "Wykres pochodzi z panelu GUI i zachowuje ten sam widok, który użytkownik "
        "wybrał po zakończeniu symulacji.",
    )


def _trial_table_rows(
    events: list[dict[str, Any]],
    clinical_profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Zbuduj wiersze tabeli triali z tych samych pól co raport analityczny.

    Parameters
    ----------
    events:
        Lista zdarzeń z polami ``trial_id``, ``condition`` i polskimi opisami.
    clinical_profile:
        Profil kliniczny dopisywany do każdego wiersza obserwacji trialu.

    Returns
    -------
    list[dict[str, str]]
        Wiersze zawierające czas, warunek, aktywne regiony, profil kliniczny,
        wynik behawioralny, metryki i komentarz po polsku.
    """
    return build_trial_observation_rows(events, clinical_profile=clinical_profile)


def _trial_observation_lines(
    events: list[dict[str, Any]],
    clinical_profile: dict[str, Any] | None = None,
) -> list[str]:
    """Zwróć opisowe linie triali do PDF i materiałów zajęciowych.

    Parameters
    ----------
    events:
        Oś czasu zdarzeń wygenerowana przez silnik.
    clinical_profile:
        Profil kliniczny użyty w eksperymencie.

    Returns
    -------
    list[str]
        Linie tekstowe z tymi samymi polami co tabela Markdown.
    """
    rows = _trial_table_rows(events, clinical_profile)
    if not rows:
        return ["Brak triali w osi czasu."]
    lines: list[str] = []
    for row in rows:
        lines.extend(
            [
                (
                    f"Trial {row['trial_id']} | czas: {row['time_s']} s | "
                    f"warunek: {row['condition']}"
                ),
                f"  Aktywne regiony: {row['active_regions']}",
                f"  Profil kliniczny: {row['clinical_profile']}",
                f"  Wynik behawioralny: {row['behavioral_outcome']}",
                f"  Najważniejsze metryki: {row['key_metrics']}",
                f"  Komentarz: {row['comment_pl']}",
            ]
        )
    return lines


def _metrics_summary_lines(
    analysis_report: dict[str, Any], limit: int = 12
) -> list[str]:
    """Zwróć skrót metryk analitycznych do raportu Markdown/HTML.

    Parameters
    ----------
    analysis_report:
        Raport analityczny zwrócony przez silnik symulacji.
    limit:
        Maksymalna liczba metryk w skrócie.

    Returns
    -------
    list[str]
        Linie listy punktowanej z nazwą i wartością metryki.
    """
    metrics = analysis_report.get("metrics", {}) if analysis_report else {}
    if not isinstance(metrics, dict) or not metrics:
        return ["- Brak metryk analitycznych w raporcie."]
    return [
        f"- **{key}**: {_stringify_value(value)}"
        for key, value in list(metrics.items())[:limit]
    ]


def _glossary_markdown_lines() -> list[str]:
    """Zwróć polski słownik pojęć używany w eksporcie raportu.

    Returns
    -------
    list[str]
        Linie Markdown z angielską nazwą techniczną i polskim objaśnieniem.
    """
    from brain_core.simulation.events import (
        EVENT_TERM_EXPLANATIONS,
        EVENT_TERM_GLOSSARY,
    )

    return [
        f"- **{key}**: {label} — {EVENT_TERM_EXPLANATIONS.get(key, 'brak opisu')}"
        for key, label in EVENT_TERM_GLOSSARY.items()
    ]


def _experiment_report_markdown(
    *,
    title: str,
    status_message: str,
    summary_text: str,
    state_config: dict[str, Any],
    event_timeline: list[dict[str, Any]],
    clinical_profile: dict[str, Any],
    analysis_report: dict[str, Any],
) -> str:
    """Złóż raport eksperymentu w formacie Markdown.

    Parameters
    ----------
    title:
        Polski tytuł raportu.
    status_message:
        Status uruchomienia pokazany użytkownikowi.
    summary_text:
        Tekstowy skrót wyniku przygotowany przez GUI lub CLI.
    state_config:
        Konfiguracja uruchomienia.
    event_timeline:
        Ujednolicona oś czasu zdarzeń.
    clinical_profile:
        Profil kliniczny użyty w eksperymencie.
    analysis_report:
        Raport analityczny z metrykami.

    Returns
    -------
    str
        Treść raportu Markdown.
    """
    lines = [f"# {title}", "", f"- **Status**: {status_message}"]
    if summary_text:
        lines.extend([f"- **Skrót**: {summary_text}", ""])
    lines.extend(["## Skrót metryk", *_metrics_summary_lines(analysis_report), ""])
    eeg_bold_sections = analysis_report.get("eeg_bold_sections", [])
    if eeg_bold_sections:
        lines.extend(["## Sekcje EEG/BOLD", ""])
        lines.extend(
            [
                "| Modalność | Metryka | Region/pasmo | Wartość | Interpretacja | Ograniczenia |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in eeg_bold_sections:
            escaped_item = {
                key: str(value).replace("|", "\\|") for key, value in item.items()
            }
            lines.append(
                "| {modality} | {metric} | {region_or_band} | {value} | "
                "{interpretation} | {limitations} |".format(**escaped_item)
            )
        lines.append("")
    lines.extend(
        [
            "## Tabela triali",
            "",
            "Kolumna **Wynik** opisuje Wynik behawioralny trialu.",
            "",
        ]
    )
    rows = _trial_table_rows(event_timeline, clinical_profile)
    if rows:
        lines.extend(
            [
                (
                    "| Trial | Warunek | Bodziec | Odpowiedź | Wynik | "
                    "Czas [s] | Aktywne regiony | Profil kliniczny | "
                    "Najważniejsze metryki | Komentarz |"
                ),
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in rows:
            escaped_row = {k: str(v).replace("|", "\\|") for k, v in row.items()}
            lines.append(
                "| {trial_id} | {condition} | {stimulus} | {response} | "
                "{behavioral_outcome} | {time_s} | {active_regions} | "
                "{clinical_profile} | {key_metrics} | {comment_pl} |".format(
                    **escaped_row
                )
            )
    else:
        lines.append("Brak triali w osi czasu.")
    lines.extend(["", "## Konfiguracja", *_flatten_mapping(state_config), ""])
    lines.extend(["## Profil kliniczny", *_flatten_mapping(clinical_profile), ""])
    lines.extend(["## Polski słownik pojęć", *_glossary_markdown_lines(), ""])
    return "\n".join(lines)


def _markdown_to_simple_html(markdown: str) -> str:
    """Przekształć ograniczony Markdown raportu do samodzielnego HTML.

    Parameters
    ----------
    markdown:
        Treść raportu Markdown wygenerowana przez `_experiment_report_markdown`.

    Returns
    -------
    str
        Prosty dokument HTML z zachowaniem treści tabelarycznych w bloku tekstowym.
    """
    escaped = html.escape(markdown)
    return (
        '<!doctype html><html lang="pl"><head><meta charset="utf-8">'
        "<title>Raport eksperymentu neuro_sim</title></head><body>"
        f"<pre>{escaped}</pre></body></html>"
    )


def export_experiment_report(
    output_path: str | Path,
    *,
    status_message: str,
    summary_text: str,
    state_config: dict[str, Any],
    event_timeline: list[dict[str, Any]],
    clinical_profile: dict[str, Any],
    analysis_report: dict[str, Any],
    title: str = "Raport eksperymentu neuro_sim",
) -> Path:
    """Eksportuj raport `.md` albo `.html` z tabelą triali, metrykami i słownikiem.

    Parameters
    ----------
    output_path:
        Ścieżka docelowa z rozszerzeniem `.md` albo `.html`.
    status_message:
        Polski status uruchomienia eksperymentu.
    summary_text:
        Krótki opis wyniku lub metryk.
    state_config:
        Konfiguracja uruchomienia zapisywana dla replikowalności.
    event_timeline:
        Ujednolicona oś czasu zdarzeń z trialami.
    clinical_profile:
        Profil kliniczny użyty w symulacji.
    analysis_report:
        Raport analityczny z metrykami.
    title:
        Tytuł raportu.

    Returns
    -------
    Path
        Ścieżka zapisanego raportu.

    Raises
    ------
    ValueError
        Gdy rozszerzenie pliku nie jest `.md` ani `.html`.
    """
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    markdown = _experiment_report_markdown(
        title=title,
        status_message=status_message,
        summary_text=summary_text,
        state_config=state_config,
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
    )
    suffix = target.suffix.lower()
    if suffix == ".md":
        content = markdown
    elif suffix == ".html":
        content = _markdown_to_simple_html(markdown)
    else:
        raise ValueError("Raport tekstowy musi mieć rozszerzenie .md albo .html.")
    target.write_text(content, encoding="utf-8")
    return target


def export_experiment_pdf(
    output_path: str | Path,
    *,
    status_message: str,
    summary_text: str,
    state_config: dict[str, Any],
    event_timeline: list[dict[str, Any]],
    clinical_profile: dict[str, Any],
    analysis_report: dict[str, Any],
    plots: list[tuple[str, Figure]],
    plot_descriptions: dict[str, str] | None = None,
) -> Path:
    """Wygeneruj gotowy PDF z opisem eksperymentu i wykresami z GUI.

    Parameters
    ----------
    output_path:
        Docelowa ścieżka pliku PDF.
    status_message:
        Komunikat zakończenia uruchomienia widoczny w GUI.
    summary_text:
        Tekstowe podsumowanie metryk przygotowane po `run_experiment()`.
    state_config:
        Konfiguracja GUI/YAML zapisana jako słownik dla replikowalności.
    event_timeline:
        Oś czasu zdarzeń zwrócona przez silnik.
    clinical_profile:
        Profil kliniczny użyty w eksperymencie.
    analysis_report:
        Raport analityczny zwrócony przez silnik.
    plots:
        Lista par `(tytuł, figura)` z aktualnych wykresów GUI.
    plot_descriptions:
        Opcjonalne opisy konkretnych wykresów, np. z dotychczasowego eksportu.

    Returns
    -------
    Path
        Ścieżka zapisanego pliku PDF.
    """

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = "Źródło: konfiguracja YAML, wynik run_experiment() i wykresy z panelu GUI."

    with PdfPages(target) as pdf:
        _draw_wrapped_text_page(
            pdf,
            "Raport eksperymentu neuro_sim",
            [
                f"Wygenerowano: {generated_at}",
                f"Status uruchomienia: {status_message}",
                "Raport zawiera opisane wyniki eksperymentu oraz wykresy wybrane "
                "w panelu GUI. Nie odtwarza logiki tasków poza silnikiem symulacji.",
            ],
            footer=footer,
        )
        _draw_wrapped_text_page(
            pdf,
            "Podsumowanie wyników",
            [summary_text or "Brak tekstowego podsumowania metryk."],
            footer=footer,
        )
        _draw_wrapped_text_page(
            pdf,
            "Konfiguracja uruchomienia",
            _flatten_mapping(state_config) or ["Brak zapisanej konfiguracji GUI."],
            footer=footer,
        )
        _draw_wrapped_text_page(
            pdf,
            "Profil kliniczny",
            _flatten_mapping(clinical_profile) or ["Brak profilu klinicznego."],
            footer=footer,
        )
        _draw_wrapped_text_page(
            pdf,
            "Oś czasu zdarzeń",
            _event_timeline_lines(event_timeline),
            footer=footer,
        )
        _draw_wrapped_text_page(
            pdf,
            "Szczegóły triali",
            _trial_observation_lines(event_timeline, clinical_profile),
            footer=footer,
        )
        _draw_wrapped_text_page(
            pdf,
            "Raport analityczny",
            _report_markdown_lines(analysis_report),
            footer=footer,
        )

        if not plots:
            _draw_wrapped_text_page(
                pdf,
                "Wykresy",
                ["Nie wybrano wykresów do eksportu PDF."],
                footer=footer,
            )
        for title, figure in plots:
            description = (plot_descriptions or {}).get(title, _plot_description(title))
            _draw_wrapped_text_page(
                pdf,
                f"Opis wykresu: {title}",
                [description],
                footer=footer,
            )
            pdf.savefig(figure)

    return target


def _control_question_lines(analysis_report: dict[str, Any]) -> list[str]:
    """Zbuduj pytania kontrolne z odpowiedziami z raportu analitycznego.

    Parameters
    ----------
    analysis_report:
        Raport analityczny zwrócony przez silnik symulacji.

    Returns
    -------
    list[str]
        Linie Markdown gotowe do zapisania w pakiecie zajęciowym.
    """
    roving_report = analysis_report.get("roving_oddball", {}) if analysis_report else {}
    if not isinstance(roving_report, dict) or not roving_report:
        return [
            "# Pytania kontrolne",
            "",
            "1. Jakie zdarzenia widać na osi czasu eksperymentu?",
            "2. Które metryki zmieniły się najmocniej po uruchomieniu scenariusza?",
            "3. Jak profil kliniczny pomaga zinterpretować wynik?",
        ]
    return [
        "# Pytania kontrolne",
        "",
        (
            "1. Ile standardów raportuje silnik? Odpowiedź: "
            f"{roving_report.get('standard_count', 'n/a')}."
        ),
        (
            "2. Ile dewiantów raportuje silnik? Odpowiedź: "
            f"{roving_report.get('deviant_count', 'n/a')}."
        ),
        (
            "3. Po czym rozpoznać readaptację? Odpowiedź: nowe standardy="
            f"{roving_report.get('new_standard_count', 'n/a')}, średnia latencja="
            f"{roving_report.get('mean_readaptation_latency', 'n/a')}."
        ),
        (
            "4. Jakie jest tempo habituacji? Odpowiedź: "
            f"{roving_report.get('habituation_rate', 'n/a')}."
        ),
    ]


def _instructor_summary_lines(
    *,
    status_message: str,
    summary_text: str,
    state_config: dict[str, Any],
    clinical_profile: dict[str, Any],
    analysis_report: dict[str, Any],
) -> list[str]:
    """Zbuduj krótki skrót dla prowadzącego zajęcia.

    Returns
    -------
    list[str]
        Linie Markdown z najważniejszymi informacjami organizacyjnymi.
    """
    scenario_path = state_config.get("scenario_config_path", "n/a")
    scenario_id = state_config.get("scenario", "n/a")
    seed = state_config.get("seed", "n/a")
    profile = clinical_profile.get("display_name") or clinical_profile.get("id", "n/a")
    return [
        "# Skrót dla prowadzącego",
        "",
        f"- Status: {status_message}",
        f"- Scenariusz: {scenario_id}",
        f"- Konfiguracja YAML: {scenario_path}",
        f"- Ziarno losowości: {seed}",
        f"- Profil kliniczny: {profile}",
        f"- Podsumowanie metryk: {summary_text or 'brak'}",
        "",
        "## Metryki do omówienia",
        *_metrics_summary_lines(analysis_report),
    ]


def _next_run_change_table_lines(
    next_run_changes: list[dict[str, Any]] | None,
) -> list[str]:
    """Zbuduj opcjonalną tabelę zmian do kolejnego uruchomienia lekcji.

    Parameters
    ----------
    next_run_changes:
        Lista propozycji zmian. Każdy słownik może zawierać pola ``element``,
        ``current_value``, ``next_value`` i ``reason``.

    Returns
    -------
    list[str]
        Linie Markdown z tabelą albo pusta lista, gdy nie podano propozycji.
    """
    if not next_run_changes:
        return []

    lines = [
        "## Co zmienić w kolejnym uruchomieniu",
        "",
        "| Element | Obecnie | Następnie | Uzasadnienie |",
        "| --- | --- | --- | --- |",
    ]
    for item in next_run_changes:
        element = str(item.get("element", "n/a")).replace("|", "\\|")
        current_value = _stringify_value(item.get("current_value", "n/a")).replace(
            "|", "\\|"
        )
        next_value = _stringify_value(item.get("next_value", "n/a")).replace("|", "\\|")
        reason = str(item.get("reason", "brak uzasadnienia")).replace("|", "\\|")
        lines.append(f"| {element} | {current_value} | {next_value} | {reason} |")
    lines.append("")
    return lines


def _lesson_plan_lines(
    *,
    status_message: str,
    summary_text: str,
    state_config: dict[str, Any],
    event_timeline: list[dict[str, Any]],
    clinical_profile: dict[str, Any],
    analysis_report: dict[str, Any],
    next_run_changes: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Zbuduj plan lekcji zgodny ze strukturą raportu zajęciowego.

    Parameters
    ----------
    status_message:
        Status zakończonego uruchomienia.
    summary_text:
        Krótki opis metryk widoczny w GUI.
    state_config:
        Migawka konfiguracji GUI/YAML.
    event_timeline:
        Oś czasu zdarzeń używana do obserwacji.
    clinical_profile:
        Profil kliniczny omawiany w lekcji.
    analysis_report:
        Raport analityczny z przewidywaniami i metrykami.
    next_run_changes:
        Opcjonalne propozycje zmian do kolejnego uruchomienia.

    Returns
    -------
    list[str]
        Linie Markdown pliku ``plan_lekcji.md``.
    """
    scenario_id = state_config.get("scenario", "n/a")
    scenario_path = state_config.get("scenario_config_path", "n/a")
    seed = state_config.get("seed", "n/a")
    profile_name = clinical_profile.get("display_name") or clinical_profile.get(
        "id", "n/a"
    )
    mechanism = clinical_profile.get("mechanism", "brak opisu mechanizmu")
    first_observations = _trial_observation_lines(event_timeline, clinical_profile)[:6]
    lines = [
        "# Plan lekcji",
        "",
        "## Cel",
        (
            "Uczestnicy łączą konfigurację YAML, profil kliniczny, przewidywanie "
            "modelu, obserwacje triali i pytania kontrolne w jeden replikowalny "
            "przebieg zajęć."
        ),
        "",
        "## Scenariusz YAML",
        f"- Plik: {scenario_path}",
        f"- Scenariusz silnika: {scenario_id}",
        f"- Ziarno losowości: {seed}",
        f"- Status uruchomienia: {status_message}",
        "",
        "## Profil",
        f"- Profil kliniczny: {profile_name}",
        f"- Mechanizm: {mechanism}",
        "",
        "## Przewidywanie",
        f"- Skrót metryk: {summary_text or 'brak'}",
        *_metrics_summary_lines(analysis_report),
        "",
        "## Obserwacja",
        *first_observations,
        "",
        "## Pytania kontrolne",
        *_control_question_lines(analysis_report)[2:],
        "",
    ]
    lines.extend(_next_run_change_table_lines(next_run_changes))
    return lines


def _sha256_file(path: Path) -> str:
    """Oblicz hash SHA-256 pliku źródłowego konfiguracji.

    Parameters
    ----------
    path:
        Ścieżka do pliku, którego integralność ma być opisana w pakiecie.

    Returns
    -------
    str
        Szesnastkowy skrót SHA-256 zawartości pliku.
    """
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_scenario_config_path(scenario_path: object) -> Path | None:
    """Zamień ścieżkę konfiguracji scenariusza na istniejący plik YAML.

    Parameters
    ----------
    scenario_path:
        Wartość pola konfiguracji GUI opisującego użyty plik YAML.

    Returns
    -------
    Path | None
        Bezwzględna ścieżka do istniejącego pliku albo ``None``, gdy ścieżka
        nie została podana lub plik nie istnieje.
    """
    if not scenario_path:
        return None

    source = Path(str(scenario_path))
    if not source.is_absolute():
        source = REPO_ROOT / source
    if not source.exists() or not source.is_file():
        return None
    return source


def _teaching_package_readme_lines(
    *,
    metadata: dict[str, Any],
    yaml_copy_name: str | None,
) -> list[str]:
    """Przygotuj polski README opisujący odtworzenie pakietu zajęciowego.

    Parameters
    ----------
    metadata:
        Metadane uruchomienia zapisane w pakiecie.
    yaml_copy_name:
        Nazwa skopiowanego pliku YAML, jeśli konfiguracja była dostępna.

    Returns
    -------
    list[str]
        Linie dokumentu Markdown gotowe do zapisu w ``README_pakietu.md``.
    """
    commit = metadata.get("git_commit") or "brak informacji"
    dirty = metadata.get("git_is_dirty")
    dirty_text = "nieznany" if dirty is None else ("tak" if dirty else "nie")
    yaml_hash = metadata.get("scenario_config_sha256") or "brak pliku YAML"
    yaml_name = yaml_copy_name or "brak skopiowanego pliku YAML"
    return [
        "# README pakietu zajęciowego",
        "",
        "Ten pakiet zawiera artefakty potrzebne do omówienia i odtworzenia "
        "uruchomienia neuro_sim na zajęciach.",
        "",
        "## Zawartość",
        "- `raport_zajeciowy.html` i `raport_zajeciowy.pdf` — raport z wyniku.",
        "- `konfiguracja_gui.json` — migawka ustawień z interfejsu.",
        f"- `{yaml_name}` — kopia użytego pliku YAML.",
        "- `environment.json` — wersja Pythona, platforma i wersje zależności.",
        "- `git_info.json` — commit, gałąź i status niezacommitowanych zmian.",
        "- `metadata_uruchomienia.json` — skrót metadanych reprodukcji.",
        "",
        "## Jak odtworzyć uruchomienie",
        "1. Przywróć kod projektu do commita zapisanego w `git_info.json`.",
        "2. Odtwórz środowisko Pythona zgodne z `environment.json`.",
        "3. Zweryfikuj integralność pliku YAML przez porównanie SHA-256 z "
        "`metadata_uruchomienia.json`.",
        "4. Uruchom scenariusz z tym samym seedem i konfiguracją GUI zapisaną "
        "w `konfiguracja_gui.json`.",
        "5. Porównaj metryki i obserwacje z raportami w pakiecie.",
        "",
        "## Kluczowe metadane",
        f"- Commit Git: `{commit}`",
        f"- Repozytorium dirty podczas eksportu: `{dirty_text}`",
        f"- Plik YAML: `{yaml_name}`",
        f"- SHA-256 YAML: `{yaml_hash}`",
        f"- Seed: `{metadata.get('seed') if metadata.get('seed') is not None else 'brak'}`",
        "",
    ]


def export_teaching_package(
    output_dir: str | Path,
    *,
    status_message: str,
    summary_text: str,
    state_config: dict[str, Any],
    event_timeline: list[dict[str, Any]],
    clinical_profile: dict[str, Any],
    analysis_report: dict[str, Any],
    plots: list[tuple[str, Figure]],
    plot_descriptions: dict[str, str] | None = None,
    next_run_changes: list[dict[str, Any]] | None = None,
) -> Path:
    """Wyeksportuj kompletny pakiet zajęciowy HTML/PDF z metadanymi.

    Parameters
    ----------
    output_dir:
        Katalog docelowy pakietu zajęciowego.
    status_message:
        Status zakończonego uruchomienia.
    summary_text:
        Skrót metryk widoczny w GUI.
    state_config:
        Migawka konfiguracji GUI/YAML wraz z seedem.
    event_timeline:
        Oś czasu zdarzeń zwrócona przez silnik.
    clinical_profile:
        Profil kliniczny z konfiguracji lub wyniku.
    analysis_report:
        Raport analityczny zwrócony przez silnik.
    plots:
        Wykresy z panelu GUI do raportu PDF.
    plot_descriptions:
        Opcjonalne opisy wykresów.
    next_run_changes:
        Opcjonalna lista zmian do tabeli „co zmienić w kolejnym uruchomieniu”.

    Returns
    -------
    Path
        Katalog zapisanego pakietu zajęciowego.
    """
    package_dir = Path(output_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    report_html = package_dir / "raport_zajeciowy.html"
    report_pdf = package_dir / "raport_zajeciowy.pdf"
    export_experiment_report(
        report_html,
        status_message=status_message,
        summary_text=summary_text,
        state_config=state_config,
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
        title="Raport zajęciowy neuro_sim",
    )
    export_experiment_pdf(
        report_pdf,
        status_message=status_message,
        summary_text=summary_text,
        state_config=state_config,
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
        plots=plots,
        plot_descriptions=plot_descriptions,
    )

    (package_dir / "konfiguracja_gui.json").write_text(
        json.dumps(state_config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    scenario_source = _resolve_scenario_config_path(
        state_config.get("scenario_config_path")
    )
    yaml_copy_name = None
    yaml_sha256 = None
    if scenario_source is not None:
        yaml_copy_name = scenario_source.name
        yaml_sha256 = _sha256_file(scenario_source)
        shutil.copy2(scenario_source, package_dir / yaml_copy_name)

    environment_info = collect_environment_info()
    git_info = collect_git_info(REPO_ROOT)
    (package_dir / "environment.json").write_text(
        json.dumps(environment_info, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (package_dir / "git_info.json").write_text(
        json.dumps(git_info, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    metadata = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "seed": state_config.get("seed"),
        "scenario": state_config.get("scenario"),
        "scenario_config_path": state_config.get("scenario_config_path"),
        "scenario_config_copy": yaml_copy_name,
        "scenario_config_sha256": yaml_sha256,
        "python_version": environment_info["python_version"],
        "platform": environment_info["platform"],
        "dependency_versions": environment_info["dependencies"],
        "git_commit": git_info["commit"],
        "git_branch": git_info["branch"],
        "git_is_dirty": git_info["is_dirty"],
    }
    (package_dir / "metadata_uruchomienia.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (package_dir / "README_pakietu.md").write_text(
        "\n".join(
            _teaching_package_readme_lines(
                metadata=metadata,
                yaml_copy_name=yaml_copy_name,
            )
        ),
        encoding="utf-8",
    )
    (package_dir / "obserwacje_triali.md").write_text(
        "\n".join(
            [
                "# Obserwacje triali",
                "",
                *_trial_observation_lines(event_timeline, clinical_profile),
            ]
        ),
        encoding="utf-8",
    )
    (package_dir / "pytania_kontrolne.md").write_text(
        "\n".join(_control_question_lines(analysis_report)), encoding="utf-8"
    )
    (package_dir / "plan_lekcji.md").write_text(
        "\n".join(
            _lesson_plan_lines(
                status_message=status_message,
                summary_text=summary_text,
                state_config=state_config,
                event_timeline=event_timeline,
                clinical_profile=clinical_profile,
                analysis_report=analysis_report,
                next_run_changes=next_run_changes,
            )
        ),
        encoding="utf-8",
    )
    (package_dir / "skrot_dla_prowadzacego.md").write_text(
        "\n".join(
            _instructor_summary_lines(
                status_message=status_message,
                summary_text=summary_text,
                state_config=state_config,
                clinical_profile=clinical_profile,
                analysis_report=analysis_report,
            )
        ),
        encoding="utf-8",
    )
    return package_dir


def export_report(
    filename: str,
    simulation_params: dict[str, Any],
    results: list[dict[str, Any]],
    plots: list[dict[str, Any]],
    title: str = "Raport badawczy symulacji poznawczej",
    author: str = "neuro_sim",
    description: str = "Automatycznie wygenerowany raport z symulacji.",
) -> None:
    """Eksportuj prosty raport badawczy do pliku PDF.

    Parameters
    ----------
    filename:
        Ścieżka do pliku PDF.
    simulation_params:
        Słownik parametrów symulacji.
    results:
        Lista słowników z wynikami, np. statystykami lub metrykami.
    plots:
        Lista słowników `figure`, `caption` i `how_to_read`.
    title:
        Tytuł raportu.
    author:
        Autor raportu.
    description:
        Opis raportu.
    """

    plot_pairs = [
        (str(plot.get("caption", "Wykres")), plot["figure"])
        for plot in plots
        if "figure" in plot
    ]
    plot_descriptions = {
        str(plot.get("caption", "Wykres")): str(plot.get("how_to_read", ""))
        for plot in plots
        if plot.get("how_to_read")
    }
    merged_metrics = {}
    for res in results:
        if isinstance(res, dict):
            merged_metrics.update(res)

    export_experiment_pdf(
        filename,
        status_message=f"Autor: {author}",
        summary_text=description,
        state_config=simulation_params,
        event_timeline=[],
        clinical_profile={},
        analysis_report={"metrics": merged_metrics},
        plots=plot_pairs,
        plot_descriptions=plot_descriptions,
    )
