"""Testy eksportu opisanego raportu PDF z wynikami i wykresami."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from brain_core.analysis.reports import build_trial_observation_rows
from brain_model.report_export import (
    _experiment_report_markdown,
    _markdown_to_simple_html,
    _trial_observation_lines,
    export_experiment_pdf,
    export_experiment_report,
    export_teaching_package,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_APP_PATH = REPO_ROOT / "brain_model" / "qt_app.py"
QT_PLOTTING_PATH = REPO_ROOT / "brain_model" / "qt_plotting.py"


def test_export_experiment_pdf_writes_described_results_and_keeps_plot_open(
    tmp_path: Path,
) -> None:
    """Eksport PDF zapisuje opis wyników i nie zamyka wykresu używanego przez GUI."""
    figure, axis = plt.subplots()
    axis.plot([0.0, 1.0], [0.2, 0.8], label="aktywacja")
    axis.legend()
    output_path = tmp_path / "raport_eksperymentu.pdf"

    report_path = export_experiment_pdf(
        output_path,
        status_message="Symulacja zakończona.",
        summary_text="prediction_error_mean: 0.12",
        state_config={"scenario": "roving_oddball", "seed": "42"},
        event_timeline=[
            {
                "time_s": 0.1,
                "event_type": "stimulus_onset",
                "label_pl": "bodziec",
                "description_pl": "Początek bodźca standardowego.",
            }
        ],
        clinical_profile={"display_name": "profil zdrowy", "mechanism": "kontrola"},
        analysis_report={
            "metrics": {"prediction_error_mean": 0.12},
            "roving_oddball": {"standard_count": 4, "deviant_count": 1},
        },
        plots=[("Aktywacje", figure)],
    )

    assert report_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert plt.fignum_exists(figure.number)
    plt.close(figure)


def _sample_trial_timeline() -> list[dict[str, object]]:
    """Zwróć minimalną oś czasu z jednym trialem do testów eksportu."""
    return [
        {
            "time_s": 0.1,
            "event_type": "stimulus_onset",
            "trial_id": 1,
            "condition": "deviant",
            "label_pl": "początek bodźca",
            "description_pl": "Początek bodźca dewiacyjnego.",
            "source": "task",
            "details": {
                "regional_input": {"ACC": 0.8, "PFC": 0.4},
                "payload": {"surprise_index": 1.0, "tone_hz": 660},
            },
        },
        {
            "time_s": 0.42,
            "event_type": "response",
            "trial_id": 1,
            "condition": "deviant",
            "label_pl": "odpowiedź",
            "description_pl": "Odpowiedź w trialu 1: poprawna.",
            "source": "task_scoring",
            "details": {
                "reaction_time_s": 0.32,
                "correct": True,
                "error_type": "none",
            },
        },
        {
            "time_s": 0.42,
            "event_type": "correctness",
            "trial_id": 1,
            "condition": "deviant",
            "label_pl": "poprawność",
            "description_pl": "Trial 1: odpowiedź poprawna.",
            "source": "task_scoring",
            "details": {"correct": True, "reaction_time_s": 0.32},
        },
    ]


def _sample_trial_timeline_with_count(trial_count: int) -> list[dict[str, object]]:
    """Zwróć deterministyczną oś czasu z podaną liczbą triali."""
    events: list[dict[str, object]] = []
    for trial_id in range(1, trial_count + 1):
        events.append(
            {
                "time_s": float(trial_id),
                "event_type": "stimulus_onset",
                "trial_id": trial_id,
                "condition": "standard",
                "label_pl": "początek bodźca",
                "description_pl": f"Początek bodźca w trialu {trial_id}.",
                "source": "task",
                "details": {"regional_input": {"ACC": 0.1 * trial_id}},
            }
        )
    return events


@pytest.mark.parametrize(
    ("max_trials", "expected_rows"),
    [
        (0, 0),
        (1, 1),
        (20, 20),
        (30, 25),
    ],
)
def test_build_trial_observation_rows_respects_configured_limit(
    max_trials: int, expected_rows: int
) -> None:
    """Limit triali 0, 1, 20 i ponad liczbę triali ma być jawnie respektowany."""
    rows = build_trial_observation_rows(
        _sample_trial_timeline_with_count(25),
        max_trials=max_trials,
    )

    assert len(rows) == expected_rows
    if rows:
        assert rows[-1]["trial_id"] == str(expected_rows)


def test_markdown_export_can_switch_between_full_and_limited_trial_table() -> None:
    """Eksport Markdown/HTML ma opcję pełnej albo limitowanej tabeli triali."""
    timeline = _sample_trial_timeline_with_count(3)
    state_config = {"analysis": {"max_report_trials": 1}}

    full_markdown = _experiment_report_markdown(
        title="Raport testowy",
        status_message="OK",
        summary_text="",
        state_config=state_config,
        event_timeline=timeline,
        clinical_profile={},
        analysis_report={},
        full_trial_table=True,
    )
    limited_markdown = _experiment_report_markdown(
        title="Raport testowy",
        status_message="OK",
        summary_text="",
        state_config=state_config,
        event_timeline=timeline,
        clinical_profile={},
        analysis_report={},
        full_trial_table=False,
    )

    assert (
        "Tryb eksportu: pełna tabela triali; liczba triali: 3; "
        "pokazano: 3; pominięto: 0."
    ) in full_markdown
    assert "| 3 | standard |" in full_markdown
    assert (
        "tabela ograniczona do 1 triali; liczba triali: 3; "
        "pokazano: 1; pominięto: 2."
    ) in limited_markdown
    assert "| 1 | standard |" in limited_markdown
    assert "| 2 | standard |" not in limited_markdown

    html = _markdown_to_simple_html(full_markdown)
    assert "<pre>" not in html
    assert "<h2>Tabela triali</h2>" in html
    assert "<table>" in html
    assert "<th>Trial</th>" in html
    assert "<td>3</td>" in html


def test_html_report_keeps_escaped_pipes_inside_table_cells() -> None:
    """HTML zachowuje pionowe kreski w komórkach bez rozbijania układu tabeli."""
    markdown = "\n".join(
        [
            "| Kolumna | Opis |",
            "| --- | --- |",
            "| A | wartość lewa \\| prawa |",
        ]
    )

    html = _markdown_to_simple_html(markdown)

    assert "<td>wartość lewa | prawa</td>" in html
    assert html.count("<td>") == 2


def test_pdf_trial_lines_keep_limit_and_report_omitted_trials() -> None:
    """Skrót PDF zachowuje limit i informuje, ile triali pominięto."""
    lines = _trial_observation_lines(
        _sample_trial_timeline_with_count(3),
        max_trials=1,
    )

    joined_lines = "\n".join(lines)
    assert (
        "tabela ograniczona do 1 triali; liczba triali: 3; pokazano: 1; "
        "pominięto: 2."
    ) in joined_lines
    assert "Trial 1" in joined_lines
    assert "Bodziec: Początek bodźca w trialu 1." in joined_lines
    assert "Odpowiedź: brak zapisanej odpowiedzi" in joined_lines
    assert "Błąd/poprawność: brak oceny poprawności" in joined_lines
    assert "Zmiana aktywności: brak istotnej zmiany w progu raportu" in joined_lines
    assert "Trial 2" not in joined_lines


def test_pdf_trial_lines_report_zero_limit_without_losing_omission_count() -> None:
    """Limit 0 w PDF opisuje pominięcie bez mylenia go z brakiem triali."""
    lines = _trial_observation_lines(
        _sample_trial_timeline_with_count(2),
        max_trials=0,
    )

    joined_lines = "\n".join(lines)
    assert "liczba triali: 2; pokazano: 0; pominięto: 2" in joined_lines
    assert "Nie pokazano szczegółów triali" in joined_lines
    assert "Brak triali w osi czasu" not in joined_lines


def test_export_reports_include_detailed_trial_observations(tmp_path: Path) -> None:
    """Markdown, HTML, PDF i pakiet zajęciowy zawierają te same pola trialu."""
    event_timeline = _sample_trial_timeline()
    clinical_profile = {
        "display_name": "Profil testowy",
        "mechanism": "Kontrolowany mechanizm kliniczny.",
    }
    analysis_report = {"metrics": {"prediction_error_mean": 0.12}}

    markdown = _experiment_report_markdown(
        title="Raport testowy",
        status_message="OK",
        summary_text="prediction_error_mean: 0.12",
        state_config={"scenario": "roving_oddball"},
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
    )
    assert "| Trial | Warunek | Bodziec | Odpowiedź | Wynik |" in markdown
    assert "dewiant" in markdown
    assert "Profil testowy" in markdown
    assert "Wynik behawioralny" in markdown
    assert "reaction_time_s=0.32" in markdown
    assert "prediction_error_mean" in markdown

    html_path = tmp_path / "raport.html"
    md_path = tmp_path / "raport.md"
    export_experiment_report(
        html_path,
        status_message="OK",
        summary_text="prediction_error_mean: 0.12",
        state_config={"scenario": "roving_oddball"},
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
    )
    export_experiment_report(
        md_path,
        status_message="OK",
        summary_text="prediction_error_mean: 0.12",
        state_config={"scenario": "roving_oddball"},
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
    )
    assert "Aktywne regiony" in html_path.read_text(encoding="utf-8")
    assert "Najważniejsze metryki" in md_path.read_text(encoding="utf-8")

    figure, axis = plt.subplots()
    axis.plot([0.0, 1.0], [0.1, 0.2])
    pdf_path = export_experiment_pdf(
        tmp_path / "raport.pdf",
        status_message="OK",
        summary_text="prediction_error_mean: 0.12",
        state_config={"scenario": "roving_oddball"},
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
        plots=[("Aktywacje", figure)],
    )
    assert pdf_path.exists()
    assert "Najważniejsze metryki" in "\n".join(
        _trial_observation_lines(event_timeline, clinical_profile)
    )
    plt.close(figure)

    package_dir = export_teaching_package(
        tmp_path / "pakiet",
        status_message="OK",
        summary_text="prediction_error_mean: 0.12",
        state_config={
            "scenario": "roving_oddball",
            "scenario_config_path": "configs/roving_oddball_healthy.yaml",
            "seed": "42",
        },
        event_timeline=event_timeline,
        clinical_profile=clinical_profile,
        analysis_report=analysis_report,
        lesson_metadata={
            "label_pl": "Lekcja — roving oddball",
            "learning_goal_pl": "Wyjaśnij habituację i readaptację.",
            "profile_pl": "Profil healthy_v1.",
            "task_pl": "Roving oddball.",
            "lesson_steps_pl": ["Zapisz hipotezę.", "Przejrzyj raport."],
            "pre_run_questions_pl": ["Jak zmieni się odpowiedź na standard?"],
            "expected_observations_pl": ["Wskaż dewiant na osi czasu."],
            "expected_report_pl": ["Raport habituacji i readaptacji."],
            "post_run_questions_pl": ["Czy hipoteza była zgodna z wynikiem?"],
            "assessment_criteria_pl": [
                "Odpowiedź wskazuje trial.",
                "Interpretacja zawiera ograniczenie.",
            ],
        },
        plots=[("Aktywacje", figure)],
        next_run_changes=[
            {
                "element": "seed",
                "current_value": "42",
                "next_value": "43",
                "reason": "pokazanie wpływu sekwencji bodźców",
            }
        ],
    )
    observations_text = (package_dir / "obserwacje_triali.md").read_text(
        encoding="utf-8"
    )
    assert "# Obserwacje triali" in observations_text
    assert "Trial 1" in observations_text
    assert "ACC" in observations_text

    expected_package_files = {
        "raport_zajeciowy.html",
        "raport_zajeciowy.pdf",
        "konfiguracja_gui.json",
        "metadata_uruchomienia.json",
        "environment.json",
        "git_info.json",
        "README_pakietu.md",
        "roving_oddball_healthy.yaml",
        "pytania_kontrolne.md",
        "skrot_dla_prowadzacego.md",
        "plan_lekcji.md",
        "karta_pracy_studenta.md",
        "wykresy",
    }
    assert expected_package_files <= {path.name for path in package_dir.iterdir()}

    metadata = json.loads(
        (package_dir / "metadata_uruchomienia.json").read_text(encoding="utf-8")
    )
    environment = json.loads(
        (package_dir / "environment.json").read_text(encoding="utf-8")
    )
    git_info = json.loads((package_dir / "git_info.json").read_text(encoding="utf-8"))
    yaml_copy = package_dir / "roving_oddball_healthy.yaml"
    assert metadata["scenario_config_copy"] == yaml_copy.name
    assert (
        metadata["scenario_config_sha256"]
        == hashlib.sha256(yaml_copy.read_bytes()).hexdigest()
    )
    assert {"git_commit", "git_is_dirty", "dependency_versions"} <= set(metadata)
    assert metadata["dependency_versions"] == environment["dependencies"]
    assert metadata["git_commit"] == git_info["commit"]
    assert metadata["git_is_dirty"] == git_info["is_dirty"]
    readme_text = (package_dir / "README_pakietu.md").read_text(encoding="utf-8")
    assert "Jak odtworzyć uruchomienie" in readme_text
    assert "SHA-256 YAML" in readme_text
    lesson_plan = (package_dir / "plan_lekcji.md").read_text(encoding="utf-8")
    assert "## Cel" in lesson_plan
    assert "## Scenariusz YAML" in lesson_plan
    assert "## Profil" in lesson_plan
    assert "## Przewidywanie" in lesson_plan
    assert "## Obserwacja" in lesson_plan
    assert "## Pytania kontrolne" in lesson_plan
    assert "## Co zmienić w kolejnym uruchomieniu" in lesson_plan
    assert "## Checklista prowadzącego" in lesson_plan
    assert "## Oczekiwany raport" in lesson_plan
    assert "## Kryteria oceny odpowiedzi" in lesson_plan
    assert "pokazanie wpływu sekwencji bodźców" in lesson_plan
    worksheet = (package_dir / "karta_pracy_studenta.md").read_text(encoding="utf-8")
    assert "# Karta pracy studenta" in worksheet
    assert "Ograniczenia interpretacyjne" in worksheet
    assert (package_dir / "wykresy").is_dir()
    assert list((package_dir / "wykresy").glob("*.png"))


def test_qt_gui_exposes_pdf_export_action_and_uses_plot_figures() -> None:
    """GUI udostępnia eksport gotowego PDF po zakończonej symulacji."""
    qt_app_source = QT_APP_PATH.read_text(encoding="utf-8")
    qt_plotting_source = QT_PLOTTING_PATH.read_text(encoding="utf-8")

    assert "Eksportuj raport PDF" in qt_app_source
    assert "export_current_pdf_report" in qt_app_source
    assert "export_experiment_pdf" in qt_app_source
    assert "self.export_pdf_action.setEnabled(True)" in qt_app_source
    assert "self.plot_panel.plots_for_export()" in qt_app_source
    assert "def plots_for_export" in qt_plotting_source
    assert "self._figure_titles.append(title)" in qt_plotting_source


def test_qt_gui_exposes_lesson_package_export_after_successful_run() -> None:
    """GUI udostępnia istniejący eksport pakietu lekcji i polski komunikat."""
    qt_app_source = QT_APP_PATH.read_text(encoding="utf-8")

    assert "Eksportuj pakiet lekcji" in qt_app_source
    assert "export_teaching_package(" in qt_app_source
    assert "self.export_teaching_package_button.setEnabled(True)" in qt_app_source
    assert "Pakiet lekcji zapisano w katalogu:" in qt_app_source
