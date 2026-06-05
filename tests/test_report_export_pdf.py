"""Testy eksportu opisanego raportu PDF z wynikami i wykresami."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from brain_model.report_export import export_experiment_pdf

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
