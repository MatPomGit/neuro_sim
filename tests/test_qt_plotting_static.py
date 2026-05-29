"""Statyczne testy separacji logiki rysowania od panelu Qt."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLOTTING_PATH = REPO_ROOT / "brain_model" / "plotting.py"
QT_PLOTTING_PATH = REPO_ROOT / "brain_model" / "qt_plotting.py"
QT_RESULTS_PATH = REPO_ROOT / "brain_model" / "qt_results.py"


def test_plotting_module_does_not_import_tk_matplotlib_backend() -> None:
    """Sprawdź, że funkcje rysujące nie zależą od backendu Tk Matplotlib."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "FigureCanvasTkAgg" not in source
    assert "NavigationToolbar2Tk" not in source
    assert "backend_tkagg" not in source
    assert "class PlotWindow" not in source


def test_qt_plot_panel_uses_qtagg_backend() -> None:
    """Sprawdź, że panel wykresów używa kanwy i paska narzędzi QtAgg."""
    source = QT_PLOTTING_PATH.read_text(encoding="utf-8")

    assert "FigureCanvasQTAgg" in source
    assert "NavigationToolbar2QT" in source
    assert "class QtPlotPanel" in source


def test_qt_results_filters_plots_by_gui_state() -> None:
    """Sprawdź, że wyniki Qt nadal dodają wykresy wyłącznie przez wybory ze stanu GUI."""
    source = QT_RESULTS_PATH.read_text(encoding="utf-8")
    plot_keys = [
        "activity",
        "simulated_brain_activity",
        "brain_region_projections",
        "region_activity_2d",
        "diagnostics",
        "behavior",
        "eeg",
        "band_power",
        "weight_trajectories",
        "weight_deltas",
        "scenario_channels",
        "scenario_timeline",
    ]

    for plot_key in plot_keys:
        assert f'state.plots.get("{plot_key}", False)' in source
