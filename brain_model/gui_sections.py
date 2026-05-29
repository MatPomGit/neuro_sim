"""Sekcje konfiguracji i wyboru wykresów w głównym oknie GUI."""

from __future__ import annotations

import tkinter as tk
from dataclasses import fields
from tkinter import messagebox, ttk
from typing import Any

from .gui_forms import PARAMETER_DESCRIPTIONS, RULE_FIELDS, ParameterForm, Tooltip
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .scenarios import get_scenario, list_scenarios


def _build_quick_start_section(gui: Any, parent: ttk.Frame) -> None:
    """Zbuduj sekcję szybkiego uruchomienia dla początkującego użytkownika."""
    gui.sim_frame = ttk.LabelFrame(
        parent, text="Szybki start", padding=10, style="QuickStart.TLabelframe"
    )
    gui.sim_frame.pack(fill="x", pady=(0, 10))

    gui.T_var = tk.StringVar(value=gui.state.T)
    gui.scenario_var = tk.StringVar(value=gui.state.scenario)
    gui.save_results_var = tk.BooleanVar(value=gui.state.save_results)

    ttk.Label(
        gui.sim_frame,
        text="Minimalny zestaw decyzji potrzebny do uruchomienia powtarzalnej symulacji.",
        style="SectionHint.TLabel",
    ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    scenario_label = ttk.Label(gui.sim_frame, text="scenariusz")
    scenario_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    Tooltip(scenario_label, PARAMETER_DESCRIPTIONS["scenario"])
    gui.scenario_combo = ttk.Combobox(
        gui.sim_frame,
        textvariable=gui.scenario_var,
        values=list_scenarios(),
        state="readonly",
        width=18,
    )
    gui.scenario_combo.grid(row=1, column=1, sticky="ew", pady=3)

    t_label = ttk.Label(gui.sim_frame, text="czas symulacji [s]")
    t_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
    Tooltip(t_label, PARAMETER_DESCRIPTIONS["T"])
    ttk.Entry(gui.sim_frame, textvariable=gui.T_var, width=14).grid(
        row=2, column=1, sticky="ew", pady=3
    )

    save_checkbox = ttk.Checkbutton(
        gui.sim_frame, text="Zapisz wyniki po symulacji", variable=gui.save_results_var
    )
    save_checkbox.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 3))
    Tooltip(save_checkbox, PARAMETER_DESCRIPTIONS["save_results"])

    ttk.Button(
        gui.sim_frame,
        text="Uruchom symulację",
        command=gui.start_simulation,
        style="Primary.TButton",
    ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 6))

    gui.scenario_details_var = tk.StringVar(value="")
    details_label = ttk.Label(
        gui.sim_frame,
        textvariable=gui.scenario_details_var,
        justify="left",
        wraplength=500,
        style="ScenarioInfo.TLabel",
    )
    details_label.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    Tooltip(details_label, PARAMETER_DESCRIPTIONS["scenario_details"])
    gui.sim_frame.columnconfigure(1, weight=1)


def _build_advanced_options_section(gui: Any, parent: ttk.Frame) -> None:
    """Zbuduj zwijaną sekcję technicznych opcji uruchomienia symulacji."""
    gui.advanced_options_visible_var = tk.BooleanVar(value=False)
    toggle = ttk.Checkbutton(
        parent,
        text="Pokaż opcje zaawansowane",
        variable=gui.advanced_options_visible_var,
        command=gui._toggle_advanced_options,
        style="Advanced.TCheckbutton",
    )
    toggle.pack(anchor="w", pady=(0, 4))

    gui.advanced_options_frame = ttk.LabelFrame(
        parent, text="Opcje zaawansowane", padding=10, style="Advanced.TLabelframe"
    )
    gui.advanced_options_frame.pack(fill="x", pady=(0, 10))

    gui.seed_var = tk.StringVar(value=gui.state.seed)
    gui.dt_var = tk.StringVar(value=gui.state.dt)
    gui.auto_dt_var = tk.BooleanVar(value=gui.state.auto_dt)
    gui.command_var = tk.StringVar(value=gui.state.command)
    gui.batch_seeds_var = tk.StringVar(value=gui.state.batch_seeds)
    gui.batch_scenarios_var = tk.StringVar(value=gui.state.batch_scenarios)
    gui.sensitivity_var = tk.StringVar(value=gui.state.sensitivity_params)
    gui.sensitivity_delta_var = tk.StringVar(value=gui.state.sensitivity_delta)

    gui._add_labeled_entry(
        gui.advanced_options_frame,
        0,
        "ziarno losowości",
        gui.seed_var,
        PARAMETER_DESCRIPTIONS["seed"],
    )
    gui._add_labeled_entry(
        gui.advanced_options_frame,
        1,
        "krok czasowy dt [s]",
        gui.dt_var,
        PARAMETER_DESCRIPTIONS["dt"],
    )
    auto_dt_checkbox = ttk.Checkbutton(
        gui.advanced_options_frame,
        text="Automatyczny dobór dt",
        variable=gui.auto_dt_var,
        command=gui._on_auto_dt_toggle,
        style="Advanced.TCheckbutton",
    )
    auto_dt_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 3))
    Tooltip(auto_dt_checkbox, PARAMETER_DESCRIPTIONS["auto_dt"])

    command_label = ttk.Label(gui.advanced_options_frame, text="tryb uruchomienia")
    command_label.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=3)
    cmd_combo = ttk.Combobox(
        gui.advanced_options_frame,
        textvariable=gui.command_var,
        values=["run", "batch"],
        state="readonly",
        width=18,
    )
    cmd_combo.grid(row=3, column=1, sticky="ew", pady=3)
    gui._add_labeled_entry(gui.advanced_options_frame, 4, "ziarna serii", gui.batch_seeds_var, None)
    gui._add_labeled_entry(
        gui.advanced_options_frame, 5, "scenariusze serii", gui.batch_scenarios_var, None
    )
    gui._add_labeled_entry(
        gui.advanced_options_frame, 6, "parametry wrażliwości", gui.sensitivity_var, None
    )
    gui._add_labeled_entry(
        gui.advanced_options_frame, 7, "delta wrażliwości", gui.sensitivity_delta_var, None
    )
    ttk.Button(
        gui.advanced_options_frame,
        text="Parametry modelu i oscylatorów...",
        command=gui._open_advanced_settings,
        style="Advanced.TButton",
    ).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    gui.advanced_options_frame.columnconfigure(1, weight=1)
    gui._toggle_advanced_options()


def _add_labeled_entry(
    parent: ttk.Frame,
    row: int,
    label_text: str,
    variable: tk.StringVar,
    tooltip_text: str | None,
) -> None:
    """Dodaj podpisane pole tekstowe i opcjonalną podpowiedź do formularza."""
    label = ttk.Label(parent, text=label_text)
    label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
    if tooltip_text is not None:
        Tooltip(label, tooltip_text)
    ttk.Entry(parent, textvariable=variable, width=14).grid(row=row, column=1, sticky="ew", pady=3)


def _toggle_advanced_options(gui: Any) -> None:
    """Pokaż albo ukryj sekcję opcji zaawansowanych."""
    if gui.advanced_options_visible_var.get():
        pack_options: dict[str, Any] = {"fill": "x", "pady": (0, 10)}
        if hasattr(gui, "plots_frame"):
            pack_options["before"] = gui.plots_frame
        gui.advanced_options_frame.pack(**pack_options)
    else:
        gui.advanced_options_frame.pack_forget()


def _build_results_and_plots_section(gui: Any, parent: ttk.Frame) -> None:
    """Zbuduj panel wyników i szczegółowego wyboru wykresów z presetami."""
    gui.plots_frame = ttk.LabelFrame(
        parent, text="Wyniki i wykresy", padding=10, style="Plots.TLabelframe"
    )
    gui.plots_frame.pack(fill="both", expand=True)

    default_plots = {
        "activity": True,
        "simulated_brain_activity": True,
        "brain_region_projections": True,
        "region_activity_2d": True,
        "diagnostics": True,
        "behavior": True,
        "eeg": True,
        "band_power": True,
        "weight_trajectories": True,
        "weight_deltas": True,
        "scenario_channels": True,
        "scenario_timeline": True,
    }
    if not gui.state.plots:
        gui.state.plots = dict(default_plots)
    gui.plot_vars = {
        name: tk.BooleanVar(value=gui.state.plots.get(name, value))
        for name, value in default_plots.items()
    }
    gui.plot_preset_var = tk.StringVar(value="Pełne")
    preset_frame = ttk.Frame(gui.plots_frame)
    preset_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    ttk.Label(preset_frame, text="Zestaw wykresów:").pack(side="left", padx=(0, 8))
    for preset_name in ("Podstawowe", "Diagnostyczne", "Pełne"):
        ttk.Radiobutton(
            preset_frame,
            text=preset_name,
            value=preset_name,
            variable=gui.plot_preset_var,
            command=gui._apply_plot_preset,
        ).pack(side="left", padx=(0, 8))

    ttk.Label(
        gui.plots_frame,
        text="Wybierz widoki do raportowania. Układ dwukolumnowy ogranicza przewijanie listy.",
        style="SectionHint.TLabel",
    ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))

    labels = {
        "activity": "aktywacje modułów poznawczych",
        "simulated_brain_activity": "symulowana aktywność mózgu (mapa cieplna)",
        "brain_region_projections": "4 rzuty mózgu: aktywacja regionów SVG",
        "region_activity_2d": "2D: aktywacja regionów mózgu w czasie",
        "diagnostics": "zmienne diagnostyczne i neuromodulacyjne",
        "behavior": "przebiegi decyzyjne + markery decyzji",
        "eeg": "sygnały EEG E-I dla wybranych modułów",
        "band_power": "moc pasm theta/alpha/beta/gamma",
        "weight_trajectories": "trajektorie adaptowanych wag W",
        "weight_deltas": "przyrosty wag ΔW / krok",
        "scenario_channels": "kanały bodźców scenariusza",
        "scenario_timeline": "oś czasu scenariusza (fazy i zdarzenia)",
    }

    plot_tooltips = {
        "activity": PARAMETER_DESCRIPTIONS["plot_activity"],
        "simulated_brain_activity": PARAMETER_DESCRIPTIONS["plot_simulated_brain_activity"],
        "brain_region_projections": PARAMETER_DESCRIPTIONS["plot_brain_region_projections"],
        "region_activity_2d": PARAMETER_DESCRIPTIONS["plot_region_activity_2d"],
        "diagnostics": PARAMETER_DESCRIPTIONS["plot_diagnostics"],
        "behavior": PARAMETER_DESCRIPTIONS["plot_behavior"],
        "eeg": PARAMETER_DESCRIPTIONS["plot_eeg"],
        "band_power": PARAMETER_DESCRIPTIONS["plot_band_power"],
        "weight_trajectories": PARAMETER_DESCRIPTIONS["plot_weight_trajectories"],
        "weight_deltas": PARAMETER_DESCRIPTIONS["plot_weight_deltas"],
        "scenario_channels": PARAMETER_DESCRIPTIONS["plot_scenario_channels"],
        "scenario_timeline": PARAMETER_DESCRIPTIONS["plot_scenario_timeline"],
    }

    for index, key in enumerate(gui.plot_vars):
        row = 2 + index // 2
        column = index % 2
        checkbox = ttk.Checkbutton(
            gui.plots_frame,
            text=labels[key],
            variable=gui.plot_vars[key],
            command=gui._sync_plot_preset_from_vars,
        )
        checkbox.grid(row=row, column=column, sticky="w", padx=(0, 12), pady=2)
        Tooltip(checkbox, plot_tooltips[key])
    gui.plots_frame.columnconfigure(0, weight=1)
    gui.plots_frame.columnconfigure(1, weight=1)


def _plot_preset_keys(gui: Any, preset_name: str) -> set[str]:
    """Zwróć zestaw wykresów aktywnych dla wskazanego presetu."""
    if preset_name == "Podstawowe":
        return {"activity", "behavior", "scenario_timeline"}
    if preset_name == "Diagnostyczne":
        return {
            "activity",
            "diagnostics",
            "behavior",
            "eeg",
            "band_power",
            "scenario_channels",
            "scenario_timeline",
        }
    return set(gui.plot_vars)


def _apply_plot_preset(gui: Any) -> None:
    """Ustaw widoczność wykresów zgodnie z aktualnie wybranym presetem."""
    active_keys = gui._plot_preset_keys(gui.plot_preset_var.get())
    for name, var in gui.plot_vars.items():
        var.set(name in active_keys)
    gui._sync_state_from_controls()


def _sync_plot_preset_from_vars(gui: Any) -> None:
    """Dopasuj nazwę presetu do aktualnych wartości pól wykresów, jeśli to możliwe."""
    active_keys = {name for name, var in gui.plot_vars.items() if var.get()}
    for preset_name in ("Podstawowe", "Diagnostyczne", "Pełne"):
        if active_keys == gui._plot_preset_keys(preset_name):
            gui.plot_preset_var.set(preset_name)
            return
    gui.plot_preset_var.set("Niestandardowe")


def _focus_plots_section(gui: Any) -> None:
    """Przenieś fokus na sekcję wyboru wykresów."""
    gui.tabs.select(0)
    gui.plots_frame.focus_set()


def _open_advanced_settings(gui: Any) -> None:
    """Otwórz okno edycji zaawansowanych parametrów modelu."""
    win = tk.Toplevel(gui)
    win.title("Parametry zaawansowane")
    win.geometry("860x680")

    container = ttk.Frame(win, padding=10)
    container.pack(fill="both", expand=True)

    brain = ParameterForm(
        container,
        "Parametry globalne BrainParams",
        BrainParams,
        gui.brain_defaults,
        include_fields=[
            f.name for f in fields(BrainParams) if f.name not in RULE_FIELDS and f.name != "dt"
        ],
    )
    brain.pack(fill="both", expand=True, pady=(0, 10))
    osc = ParameterForm(
        container, "Parametry WilsonCowanParams", WilsonCowanParams, gui.osc_defaults
    )
    osc.pack(fill="both", expand=True)

    gui._sync_state_from_controls()
    gui._sync_advanced_forms_from_state(brain, osc)

    def save_and_close() -> None:
        """Zapisz wartości z okna zaawansowanego i zamknij okno."""
        gui._sync_state_from_controls()
        try:
            gui._sync_state_from_advanced_forms(brain, osc)
        except ValueError as exc:
            messagebox.showerror(
                "Niepoprawne parametry",
                f"Nie udało się zapisać parametrów zaawansowanych.\n\n{exc}",
                parent=win,
            )
            return
        win.destroy()

    btns = ttk.Frame(container)
    btns.pack(fill="x", pady=(10, 0))
    ttk.Button(btns, text="Anuluj", command=win.destroy).pack(side="right")
    ttk.Button(btns, text="Zapisz", command=save_and_close).pack(side="right", padx=(0, 8))


def _refresh_scenario_details(gui: Any) -> None:
    """Odśwież opis bieżącego scenariusza w panelu konfiguracji."""
    gui.state.scenario = gui.scenario_var.get()
    scenario = get_scenario(gui.state.scenario)
    gui.scenario_details_var.set(
        f"Krótki opis: {scenario.description}\n"
        f"Przewidywane wyniki: {scenario.what_changes}\n"
        f"Sugerowany czas: {scenario.duration_hint:.1f} s"
    )


def _auto_dt_for_duration(duration_s: float) -> float:
    """Wyznacz bezpieczny krok czasowy dla podanego czasu symulacji."""
    target_steps = 2400.0
    raw_dt = duration_s / target_steps
    return max(0.001, min(0.01, raw_dt))


def _on_auto_dt_toggle(gui: Any) -> None:
    """Zaktualizuj krok czasowy, jeśli aktywny jest automatyczny dobór dt."""
    if gui.auto_dt_var.get():
        try:
            duration_s = float(gui.T_var.get())
        except ValueError:
            return
        gui.dt_var.set(f"{gui._auto_dt_for_duration(duration_s):.4f}")
        gui.state.dt = gui.dt_var.get()
