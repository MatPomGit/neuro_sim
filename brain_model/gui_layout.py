"""Orkiestracja głównego układu okna GUI."""

from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from tkinter import ttk

from .gui_menu import (
    _build_menu,
    _open_new_instance,
    _show_about,
    _show_usage_help,
)
from .gui_results import _apply_run_result
from .gui_sections import (
    _add_labeled_entry,
    _apply_plot_preset,
    _auto_dt_for_duration,
    _build_advanced_options_section,
    _build_quick_start_section,
    _build_results_and_plots_section,
    _focus_plots_section,
    _on_auto_dt_toggle,
    _open_advanced_settings,
    _plot_preset_keys,
    _refresh_scenario_details,
    _sync_plot_preset_from_vars,
    _toggle_advanced_options,
)
from .params import BrainParams


class LegacyPlotPlaceholder(ttk.Frame):
    """Zastępczy panel wykresów dla niepublicznej ścieżki Tk bez backendu Matplotlib Tk."""

    def __init__(self, parent: ttk.Widget) -> None:
        """Utwórz panel informujący o dostępności wykresów w interfejsie PySide6."""
        super().__init__(parent)
        self.notebook: ttk.Notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self._add_message_tab(
            "Informacja",
            "Interaktywne wykresy są dostępne w głównym interfejsie PySide6.",
        )

    def clear(self) -> None:
        """Usuń zakładki informacyjne dodane po poprzednim uruchomieniu."""
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)

    def add_plot(
        self,
        tab_title: str,
        draw_func: object,
        *args: object,
        figsize: tuple[float, float] = (10, 6),
        **kwargs: object,
    ) -> None:
        """Dodaj zastępczą zakładkę bez osadzania figury w backendzie Tk."""
        del draw_func, args, figsize, kwargs
        self._add_message_tab(
            tab_title,
            "Ten wykres jest renderowany w panelu QtPlotPanel interfejsu PySide6.",
        )

    def fit_tabs_to_count(self) -> None:
        """Zachowaj zgodność z dawnym API panelu wykresów Tk."""
        return

    def _add_message_tab(self, title: str, message: str) -> None:
        """Dodaj zakładkę z polskim komunikatem tekstowym."""
        frame = ttk.Frame(self.notebook, padding=12)
        ttk.Label(frame, text=message, anchor="center", justify="center").pack(
            fill="both", expand=True
        )
        self.notebook.add(frame, text=title)


class GuiLayoutMixin:
    """Mixin orkiestrujący główne zakładki i delegujący szczegóły układu GUI."""

    _apply_plot_preset = _apply_plot_preset
    _apply_run_result = _apply_run_result
    _build_menu = _build_menu
    _focus_plots_section = _focus_plots_section
    _on_auto_dt_toggle = _on_auto_dt_toggle
    _open_advanced_settings = _open_advanced_settings
    _open_new_instance = _open_new_instance
    _refresh_scenario_details = _refresh_scenario_details
    _show_about = _show_about
    _show_usage_help = _show_usage_help
    _sync_plot_preset_from_vars = _sync_plot_preset_from_vars
    _toggle_advanced_options = _toggle_advanced_options

    def _build_layout(self) -> None:
        """Zbuduj zakładki i połącz modułowe sekcje głównego okna."""
        self.tabs: ttk.Notebook = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        config_tab = ttk.Frame(self.tabs)
        plots_tab = ttk.Frame(self.tabs)
        self.tabs.add(config_tab, text="Konfiguracja")
        self.tabs.add(plots_tab, text="Wykresy")

        root = ttk.Frame(config_tab, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root, style="Header.TFrame")
        top.pack(fill="x", pady=(0, 12))
        top.columnconfigure(0, weight=1)

        header_text = ttk.Frame(top, style="Header.TFrame")
        header_text.grid(row=0, column=0, sticky="ew", padx=(0, 16))

        ttk.Label(
            header_text,
            text="Laboratorium symulacji modelu poznawczego",
            style="HeaderTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            header_text,
            text=(
                "Dobierz scenariusz, uruchom obliczenia i porównaj aktywność modułów "
                "oraz oscylatorów Wilsona-Cowana w jednym przepływie pracy."
            ),
            style="HeaderSubtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        workflow = ttk.Frame(top, padding=(12, 10), style="Workflow.TFrame")
        workflow.grid(row=0, column=1, sticky="ne")
        ttk.Label(workflow, text="Przepływ pracy", style="WorkflowTitle.TLabel").pack(anchor="w")
        for step in (
            "1. Wybierz scenariusz i czas",
            "2. Uruchom symulację",
            "3. Obejrzyj wykresy i metryki",
        ):
            ttk.Label(workflow, text=step, style="WorkflowStep.TLabel").pack(
                anchor="w", pady=(3, 0)
            )

        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes, padding=(0, 0, 8, 0))
        right = ttk.Frame(panes, padding=(8, 0, 0, 0))
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        _build_quick_start_section(self, left)
        _build_advanced_options_section(self, right)
        _build_results_and_plots_section(self, right)

        bottom = ttk.Frame(root, style="Footer.TFrame")
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="Przywróć domyślne", command=self.reset_defaults).pack(side="left")
        ttk.Button(bottom, text="Zamknij", command=self.destroy).pack(side="right")
        ttk.Button(
            bottom,
            text="Uruchom symulację",
            command=self.start_simulation,
            style="Primary.TButton",
        ).pack(side="right", padx=(0, 8))

        status_bar = ttk.Frame(root, padding=(0, 8, 0, 0), style="Footer.TFrame")
        status_bar.pack(fill="x")
        status_bar.columnconfigure(0, weight=1)
        status_bar.columnconfigure(1, weight=0)

        self.status_var: tk.StringVar = tk.StringVar(value="Gotowe.")
        self.status_label: ttk.Label = ttk.Label(
            status_bar, textvariable=self.status_var, style="Status.TLabel"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        self.progress_var: tk.DoubleVar = tk.DoubleVar(value=0.0)
        self.progress: ttk.Progressbar = ttk.Progressbar(
            status_bar,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Status.Horizontal.TProgressbar",
            length=220,
        )
        self.progress.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self.summary_var: tk.StringVar = tk.StringVar(value="")
        ttk.Label(
            root, textvariable=self.summary_var, justify="left", style="Footer.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        self.scenario_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._refresh_scenario_details()
        )
        self._refresh_scenario_details()
        self.T_var.trace_add("write", lambda *_args: self._on_auto_dt_toggle())
        self._on_auto_dt_toggle()

        self.plot_panel: LegacyPlotPlaceholder = LegacyPlotPlaceholder(plots_tab)
        self.plot_panel.pack(fill="both", expand=True)

    def reset_defaults(self) -> None:
        """Przywróć wartości domyślne formularzy i opcji GUI."""
        self.state.T = "12.0"
        self.state.dt = str(self.brain_defaults.dt)
        self.state.seed = "7"
        self.state.command = "run"
        self.state.batch_seeds = "7,11,19"
        self.state.batch_scenarios = "reward-learning"
        self.state.sensitivity_params = "noise,gw_threshold"
        self.state.sensitivity_delta = "0.1"
        self.state.scenario = "baseline"
        self.state.auto_dt = True
        self.state.save_results = True
        self.state.brain_params = self.brain_defaults
        self.state.oscillator_params = self.osc_defaults
        self.state.plots = {name: True for name in self.plot_vars}
        self._sync_controls_from_state()
        self.plot_preset_var.set("Pełne")
        self._refresh_scenario_details()
        self._on_auto_dt_toggle()
        try:
            self.state.dt = self.dt_var.get()
            self.state.brain_params = replace(self.state.brain_params, dt=float(self.state.dt))
        except ValueError:
            pass
        self.status_label.configure(style="Status.TLabel")
        self.status_var.set("Przywrócono wartości domyślne.")

    def _build_brain_params(self) -> BrainParams:
        """Zbuduj parametry modelu z aktualnego stanu, zachowując reguły domyślne."""
        return replace(
            self.state.brain_params,
            dt=float(self.state.dt),
            semantic_rule=self.brain_defaults.semantic_rule,
            value_rule=self.brain_defaults.value_rule,
            connectivity_adaptation=self.brain_defaults.connectivity_adaptation,
        )
