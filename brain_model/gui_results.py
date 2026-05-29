"""Aktualizacja wyników symulacji i dodawanie wykresów do panelu GUI."""

from __future__ import annotations

from typing import Any

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
from .scenarios import get_scenario


def _apply_run_result(gui: Any, payload: tuple[Any, ...]) -> None:
    """Przenieś wynik symulacji do panelu wykresów i statusu."""
    (
        msg,
        summary_text,
        _save_info,
        model,
        time,
        activity,
        diagnostics,
        oscillations,
        behavior,
    ) = payload
    gui._sync_state_from_controls()
    gui.plot_panel.clear()
    has_plots = _add_selected_plots_to_panel(
        gui, model, time, activity, diagnostics, oscillations, behavior
    )
    gui.tabs.select(1 if has_plots else 0)
    gui.status_label.configure(style="Status.TLabel")
    gui.status_var.set(msg)
    gui.summary_var.set(summary_text)
    gui.progress_var.set(100.0)


def _add_selected_plots_to_panel(
    gui: Any,
    model: Any,
    time: Any,
    activity: Any,
    diagnostics: Any,
    oscillations: Any,
    behavior: Any,
) -> bool:
    """Dodaj do panelu wykresów tylko te wizualizacje, które wybrał użytkownik."""
    has_plots = False
    if gui.state.plots.get("activity", False):
        gui.plot_panel.add_plot(
            "Aktywacje", draw_activity, time, activity, model.names, model.idx, figsize=(11, 7)
        )
        has_plots = True
    if gui.state.plots.get("simulated_brain_activity", False):
        gui.plot_panel.add_plot(
            "Aktywność mózgu",
            draw_simulated_brain_activity,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 7),
        )
        has_plots = True
    if gui.state.plots.get("brain_region_projections", False):
        gui.plot_panel.add_plot(
            "Rzuty mózgu SVG",
            draw_brain_region_projections,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 8),
        )
        has_plots = True
    if gui.state.plots.get("region_activity_2d", False):
        gui.plot_panel.add_plot(
            "Regiony 2D w czasie",
            draw_region_activity_2d,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 8),
        )
        has_plots = True
    if gui.state.plots.get("diagnostics", False):
        gui.plot_panel.add_plot("Diagnostyka", draw_diagnostics, time, diagnostics, figsize=(11, 5))
        has_plots = True
    if gui.state.plots.get("behavior", False):
        gui.plot_panel.add_plot("Zachowanie", draw_behavior, time, behavior, figsize=(11, 5))
        has_plots = True
    if gui.state.plots.get("eeg", False):
        gui.plot_panel.add_plot(
            "EEG modułów",
            draw_eeg_modules,
            time,
            oscillations,
            model.names,
            model.idx,
            figsize=(11, 6),
        )
        has_plots = True
    if gui.state.plots.get("band_power", False):
        gui.plot_panel.add_plot("Moc pasm", draw_band_power, time, oscillations, figsize=(11, 8))
        has_plots = True
    if gui.state.plots.get("weight_trajectories", False):
        gui.plot_panel.add_plot(
            "Trajektorie wag", draw_weight_trajectories, time, diagnostics, figsize=(11, 5)
        )
        has_plots = True
    if gui.state.plots.get("weight_deltas", False):
        gui.plot_panel.add_plot(
            "Przyrosty wag", draw_weight_deltas, time, diagnostics, figsize=(11, 5)
        )
        has_plots = True
    if gui.state.plots.get("scenario_channels", False):
        gui.plot_panel.add_plot(
            "Kanały scenariusza",
            draw_scenario_channels,
            time,
            get_scenario(gui.state.scenario),
            figsize=(11, 5),
        )
        has_plots = True
    if gui.state.plots.get("scenario_timeline", False):
        gui.plot_panel.add_plot(
            "Oś czasu scenariusza",
            draw_scenario_timeline,
            time,
            get_scenario(gui.state.scenario),
            figsize=(11, 4),
        )
        has_plots = True
    return has_plots
