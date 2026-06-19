"""Statyczne testy separacji logiki rysowania od panelu Qt."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLOTTING_PATH = REPO_ROOT / "brain_model" / "plotting.py"
QT_PLOTTING_PATH = REPO_ROOT / "brain_model" / "qt_plotting.py"
QT_RESULTS_PATH = REPO_ROOT / "brain_model" / "qt_results.py"
WEB_GUI_PATH = REPO_ROOT / "docs" / "web_gui.html"


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

    assert "def _plot_svg_underlay_background" in source
    assert "def _plot_svg_region_background" in source
    assert "def _set_svg_data_limits" in source
    assert "_plot_svg_underlay_background(ax, underlay_shapes)" in source
    assert "_plot_svg_region_background(ax, shapes)" in source
    assert "_set_svg_data_limits(ax, shapes, underlay_shapes)" in source


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


def test_draw_behavior_uses_two_axes_and_decision_time_annotations() -> None:
    """Sprawdź, że wykres zachowania ma pełny panel i wycinek decyzji 0-1 s."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert (
        'axes = fig.subplots(2, 1, sharex=False, gridspec_kw={"height_ratios": [3, 1]})'
        in source
    )
    assert "window_ax.set_xlim(0.0, 1.0)" in source
    assert 'f"t={float(decision_time):.2f} s"' in source
    assert "full_ax.annotate(" in source
    assert "window_ax.annotate(" in source
    assert "_style_lines(full_ax)" in source
    assert "_style_lines(window_ax)" in source
    assert "return [full_ax, window_ax]" in source


def test_web_behavior_plot_uses_full_and_one_second_panels() -> None:
    """Sprawdź, że webowy wykres zachowania ma pełny panel i wycinek 0-1 s."""
    source = WEB_GUI_PATH.read_text(encoding="utf-8")

    assert "function makeBehaviorPlot(time, behavior)" in source
    assert (
        'layout.xaxis2 = { title: "czas [s]", zeroline: false, range: [0, 1]' in source
    )
    assert (
        'layout.yaxis = { title: "wartość", zeroline: false, domain: [0.44, 1.0]'
        in source
    )
    assert (
        'layout.yaxis2 = { title: "wartość", zeroline: false, domain: [0.0, 0.30]'
        in source
    )
    assert "const text = `t=${decisionTime.toFixed(2)} s`;" in source
    assert 'xref: "x2"' in source
    assert (
        'Plotly.newPlot("behaviorPlot", behaviorPlot.traces, behaviorPlot.layout'
        in source
    )
    assert "#behaviorPlot { height: 620px; }" in source


def test_activity_plot_combines_activation_and_stimulus_channels() -> None:
    """Sprawdź statycznie układ aktywacji z kanałami bodźców i przewijaniem."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "def draw_activity_with_stimulus_channels" in source
    assert "fig.subplots(" in source
    assert "sharex=True" in source
    assert 'gridspec_kw={"height_ratios": [5, 1]}' in source
    assert 'activity_ax.callbacks.connect("xlim_changed"' in source
    assert 'fig.canvas.mpl_connect("scroll_event"' in source
    assert "CHANNELS" in source
    assert "build_stimulus_fn(scenario)" in source


def test_activity_plot_has_legend_visibility_selector() -> None:
    """Sprawdź statycznie przełączanie sygnałów aktywacji przez legendę."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "legend_line.set_picker" in source
    assert "line.set_visible(is_visible)" in source
    assert "legend_line.set_alpha" in source
    assert 'fig.canvas.mpl_connect("pick_event"' in source


def test_qt_activity_controls_and_scenario_are_bound() -> None:
    """Sprawdź statycznie kontrolki osi Y i przekazanie scenariusza aktywacji."""
    plotting_source = QT_PLOTTING_PATH.read_text(encoding="utf-8")
    results_source = QT_RESULTS_PATH.read_text(encoding="utf-8")

    assert "controls_factory" in plotting_source
    assert "draw_activity_with_stimulus_channels" in results_source
    assert "get_scenario(state.scenario)" in results_source
    assert "controls_factory=_create_activity_controls" in results_source
    assert 'QPushButton("Przybliż")' in results_source
    assert 'QPushButton("Oddal")' in results_source
    assert 'QPushButton("Autoskaluj Y aktywacji")' in results_source
    assert 'QPushButton("Autoskaluj wykres")' in results_source
    assert 'QPushButton("Skala Y: liniowa")' in results_source
    assert "QCheckBox(signal_label)" in results_source
    assert "checkbox.toggled.connect" in results_source
    assert "zoom_activity_time(0.75)" in results_source
    assert "zoom_activity_time(1.25)" in results_source
    assert 'scale_button.setText("Skala Y: logarytmiczna")' in results_source
    assert "activity_axis.relim(visible_only=True)" in results_source
    assert "activity_axis.autoscale_view(scalex=False, scaley=True)" in results_source
    assert "QMessageBox.warning" in results_source


def test_diagnostics_plot_uses_two_shared_panels_with_separated_series() -> None:
    """Sprawdź statycznie podział diagnostyki na dwa panele ze wspólną osią X."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")
    function_source = source.split("def draw_diagnostics", maxsplit=1)[1].split(
        "def draw_weight_trajectories", maxsplit=1
    )[0]

    theoretical_keys = [
        'diagnostics["prediction_error"]',
        'diagnostics["gw_ignition"]',
        'diagnostics["dopamine_delta"]',
    ]
    neuromodulator_keys = [
        'diagnostics["noradrenaline"]',
        'diagnostics["acetylcholine"]',
        'diagnostics["serotonin"]',
        'diagnostics["gaba"]',
        'diagnostics["glutamate"]',
        'diagnostics["endorphins"]',
        'diagnostics["cortisol"]',
    ]

    assert "ax.remove()" in function_source
    assert "axes = fig.subplots(2, 1, sharex=True)" in function_source
    assert "theoretical_ax, neuromodulator_ax = axes" in function_source
    assert 'theoretical_ax.set_title("Zmienne teoretyczne modelu")' in function_source
    assert 'neuromodulator_ax.set_title("Neuromodulatory mózgowe")' in function_source
    assert 'neuromodulator_ax.set_xlabel("Czas symulacji [s]")' in function_source
    assert "return list(axes)" in function_source

    theoretical_block = function_source.split("neuromodulator_ax.plot", maxsplit=1)[0]
    neuromodulator_block = function_source.split("neuromodulator_ax.plot", maxsplit=1)[
        1
    ]

    for theoretical_key in theoretical_keys:
        assert theoretical_key in theoretical_block
        assert theoretical_key not in neuromodulator_block
    for neuromodulator_key in neuromodulator_keys:
        assert neuromodulator_key in neuromodulator_block
        assert neuromodulator_key not in theoretical_block


def test_interpretation_box_documents_safe_removed_artist_value_error() -> None:
    """ValueError przy usuwaniu artysty Matplotlib musi być jawnie uzasadniony."""
    source = PLOTTING_PATH.read_text(encoding="utf-8")

    assert "artysta został już bezpiecznie" in source
    assert "usunięty z figury" in source
