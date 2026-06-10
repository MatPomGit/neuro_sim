"""Testy eksportu opisanego raportu PDF z wynikami i wykresami."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from brain_model.report_export import (
    _experiment_report_markdown,
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
        plots=[],
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
        "pytania_kontrolne.md",
        "skrot_dla_prowadzacego.md",
        "plan_lekcji.md",
    }
    assert expected_package_files <= {path.name for path in package_dir.iterdir()}
    lesson_plan = (package_dir / "plan_lekcji.md").read_text(encoding="utf-8")
    assert "## Cel" in lesson_plan
    assert "## Scenariusz YAML" in lesson_plan
    assert "## Profil" in lesson_plan
    assert "## Przewidywanie" in lesson_plan
    assert "## Obserwacja" in lesson_plan
    assert "## Pytania kontrolne" in lesson_plan
    assert "## Co zmienić w kolejnym uruchomieniu" in lesson_plan
    assert "pokazanie wpływu sekwencji bodźców" in lesson_plan


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
