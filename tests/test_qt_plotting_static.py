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


def test_plotting_functions_add_interpretation_boxes() -> None:
    """Sprawdź, że wykresy mają stałe opisy interpretacyjne dla użytkownika."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "def _add_interpretation_box" in source
    assert source.count("_add_interpretation_box(") >= 12
    assert "Mapa cieplna „Aktywność mózgu”" in source
    assert "Rzuty SVG pokazują" in source


def test_brain_projection_uses_svg_background_and_dynamic_limits() -> None:
    """Sprawdź, że rzuty SVG mają kontury tła i zakres z danych SVG."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "def _plot_svg_region_background" in source
    assert "def _set_svg_data_limits" in source
    assert "_plot_svg_region_background(ax, shapes)" in source
    assert "_set_svg_data_limits(ax, shapes)" in source


def test_eeg_modules_are_vertically_offset() -> None:
    """Sprawdź, że sygnały EEG modułów nie są rysowane bez przesunięcia."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "offset_step" in source
    assert "eeg[:, idx[name]] + offset" in source
    assert "serie przesunięte pionowo" in source


def test_plot_interpretations_are_accessible_to_mixed_audiences() -> None:
    """Sprawdź, że opisy prowadzą osoby początkujące i specjalistów."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert source.count("Dla osoby początkującej") >= 10
    assert source.count("Dla specjalisty") >= 10
    assert "kluczowe" in source
