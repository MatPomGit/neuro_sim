"""Eksport opisanych wyników eksperymentu do plików PDF."""

from __future__ import annotations

import datetime
import html
import json
import platform
import shutil
import textwrap
from pathlib import Path
from typing import Any

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from brain_core.analysis.reports import AnalysisReport

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
    }
    return descriptions.get(
        title,
        "Wykres pochodzi z panelu GUI i zachowuje ten sam widok, który użytkownik "
        "wybrał po zakończeniu symulacji.",
    )


def _trial_table_rows(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Zbuduj wiersze tabeli triali z ujednoliconej osi czasu.

    Parameters
    ----------
    events:
        Lista zdarzeń z polami ``trial_id``, ``condition`` i polskimi opisami.

    Returns
    -------
    list[dict[str, str]]
        Wiersze tabeli zawierające trial, warunek, bodziec, odpowiedź i wynik.
    """
    grouped: dict[str, dict[str, str]] = {}
    for event in events:
        trial_id = event.get("trial_id", "n/a")
        if trial_id in {None, "n/a"}:
            continue
        key = str(trial_id)
        row = grouped.setdefault(
            key,
            {
                "trial_id": key,
                "condition": str(event.get("condition", "n/a")),
                "stimulus": "n/a",
                "response": "n/a",
                "correctness": "n/a",
                "activity": "n/a",
            },
        )
        event_type = str(event.get("event_type", ""))
        description = str(event.get("description_pl") or "n/a")
        if event_type == "stimulus_onset":
            row["stimulus"] = description
        elif event_type == "response":
            row["response"] = description
        elif event_type in {"correctness", "error"}:
            row["correctness"] = description
        elif event_type == "significant_region_activity_change":
            row["activity"] = description
    return [
        grouped[key]
        for key in sorted(
            grouped,
            key=lambda value: (0, int(value)) if value.isdigit() else (1, value),
        )
    ]


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
    lines.extend(["## Tabela triali", ""])
    rows = _trial_table_rows(event_timeline)
    if rows:
        lines.extend(
            [
                "| Trial | Warunek | Bodziec | Odpowiedź | Wynik | Zmiana aktywności |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in rows:
            escaped_row = {k: str(v).replace("|", "\\|") for k, v in row.items()}
            lines.append(
                "| {trial_id} | {condition} | {stimulus} | {response} | "
                "{correctness} | {activity} |".format(**escaped_row)
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
    scenario_path = state_config.get("scenario_config_path")
    if scenario_path:
        source = Path(str(scenario_path))
        if not source.is_absolute():
            source = Path(__file__).resolve().parents[1] / source
        if source.exists():
            shutil.copy2(source, package_dir / source.name)

    metadata = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "seed": state_config.get("seed"),
        "scenario": state_config.get("scenario"),
        "scenario_config_path": state_config.get("scenario_config_path"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
    (package_dir / "metadata_uruchomienia.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (package_dir / "pytania_kontrolne.md").write_text(
        "\n".join(_control_question_lines(analysis_report)), encoding="utf-8"
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
