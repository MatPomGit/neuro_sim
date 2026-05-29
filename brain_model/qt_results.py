"""Osadzanie wykresów Matplotlib w interfejsie PySide6."""

from __future__ import annotations

from typing import Any

from .gui_state import GuiState
from .plotting import (
    draw_activity,
    draw_band_power,
    draw_behavior,
    draw_brain_region_projections,
    draw_diagnostics,
    draw_eeg_modules,
    draw_region_activity_2d,
    draw_scenario_channels,
    draw_scenario_timeline,
    draw_simulated_brain_activity,
    draw_weight_deltas,
    draw_weight_trajectories,
)
from .qt_plotting import QtPlotPanel
from .scenarios import get_scenario


def apply_run_result(
    plot_panel: QtPlotPanel, state: GuiState, payload: tuple[Any, ...]
) -> bool:
    """Przenieś wynik symulacji do panelu Qt i zwróć informację, czy dodano wykresy."""
    _, _, _, model, time, activity, diagnostics, oscillations, behavior = payload
    plot_panel.clear()
    return add_selected_plots_to_panel(
        plot_panel, state, model, time, activity, diagnostics, oscillations, behavior
    )


def add_selected_plots_to_panel(
    plot_panel: QtPlotPanel,
    state: GuiState,
    model: Any,
    time: Any,
    activity: Any,
    diagnostics: Any,
    oscillations: Any,
    behavior: Any,
) -> bool:
    """Dodaj do panelu Qt tylko wykresy wybrane przez użytkownika."""
    has_plots = False
    if state.plots.get("activity", False):
        plot_panel.add_plot(
            "Aktywacje",
            draw_activity,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 7),
        )
        has_plots = True
    if state.plots.get("simulated_brain_activity", False):
        plot_panel.add_plot(
            "Aktywność mózgu",
            draw_simulated_brain_activity,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 7),
        )
        has_plots = True
    if state.plots.get("brain_region_projections", False):
        plot_panel.add_plot(
            "Rzuty mózgu SVG",
            draw_brain_region_projections,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 8),
        )
        has_plots = True
    if state.plots.get("region_activity_2d", False):
        plot_panel.add_plot(
            "Regiony 2D w czasie",
            draw_region_activity_2d,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 8),
        )
        has_plots = True
    if state.plots.get("diagnostics", False):
        plot_panel.add_plot(
            "Diagnostyka", draw_diagnostics, time, diagnostics, figsize=(11, 5)
        )
        has_plots = True
    if state.plots.get("behavior", False):
        plot_panel.add_plot(
            "Zachowanie", draw_behavior, time, behavior, figsize=(11, 5)
        )
        has_plots = True
    if state.plots.get("eeg", False):
        plot_panel.add_plot(
            "EEG modułów",
            draw_eeg_modules,
            time,
            oscillations,
            model.names,
            model.idx,
            figsize=(11, 6),
        )
        has_plots = True
    if state.plots.get("band_power", False):
        plot_panel.add_plot(
            "Moc pasm", draw_band_power, time, oscillations, figsize=(11, 8)
        )
        has_plots = True
    if state.plots.get("weight_trajectories", False):
        plot_panel.add_plot(
            "Trajektorie wag",
            draw_weight_trajectories,
            time,
            diagnostics,
            figsize=(11, 5),
        )
        has_plots = True
    if state.plots.get("weight_deltas", False):
        plot_panel.add_plot(
            "Przyrosty wag", draw_weight_deltas, time, diagnostics, figsize=(11, 5)
        )
        has_plots = True
    if state.plots.get("scenario_channels", False):
        plot_panel.add_plot(
            "Kanały scenariusza",
            draw_scenario_channels,
            time,
            get_scenario(state.scenario),
            figsize=(11, 5),
        )
        has_plots = True
    if state.plots.get("scenario_timeline", False):
        plot_panel.add_plot(
            "Oś czasu scenariusza",
            draw_scenario_timeline,
            time,
            get_scenario(state.scenario),
            figsize=(11, 4),
        )
        has_plots = True
    return has_plots
