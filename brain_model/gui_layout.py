"""Budowa układu okna, zakładek, sekcji i menu GUI."""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from dataclasses import fields, replace
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict

from .gui_forms import (
    APP_AUTHOR,
    APP_VERSION,
    LAST_UPDATED,
    PARAMETER_DESCRIPTIONS,
    RULE_FIELDS,
    ParameterForm,
    Tooltip,
)
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .plotting import (
    PlotWindow,
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
from .scenarios import get_scenario, list_scenarios


def configure_styles(root: tk.Tk) -> None:
    """Skonfiguruj spójną, spokojną paletę stylów ttk dla głównego okna GUI."""
    palette = {
        "primary": "#2563eb",
        "primary_active": "#1d4ed8",
        "panel_bg": "#f8fafc",
        "panel_border": "#dbe4ef",
        "scenario_bg": "#eef6ff",
        "warning": "#b45309",
        "advanced_fg": "#64748b",
        "text": "#0f172a",
    }

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(background=palette["panel_bg"])
    style.configure("TFrame", background=palette["panel_bg"])
    style.configure("Header.TFrame", background=palette["panel_bg"])
    style.configure(
        "HeaderTitle.TLabel",
        background=palette["panel_bg"],
        foreground=palette["text"],
        font=("TkDefaultFont", 13, "bold"),
    )
    style.configure(
        "HeaderSubtitle.TLabel",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "QuickStart.TLabelframe",
        background=palette["panel_bg"],
        bordercolor=palette["panel_border"],
        relief="solid",
    )
    style.configure(
        "QuickStart.TLabelframe.Label",
        background=palette["panel_bg"],
        foreground=palette["text"],
        font=("TkDefaultFont", 10, "bold"),
    )
    style.configure(
        "ScenarioInfo.TLabel",
        background=palette["scenario_bg"],
        foreground=palette["text"],
        padding=8,
    )
    style.configure(
        "Primary.TButton",
        background=palette["primary"],
        foreground="#ffffff",
        font=("TkDefaultFont", 10, "bold"),
        padding=(10, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", palette["primary_active"]), ("pressed", palette["primary_active"])],
        foreground=[("disabled", "#e2e8f0")],
    )
    style.configure(
        "Status.TLabel",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "Warning.Status.TLabel",
        background=palette["panel_bg"],
        foreground=palette["warning"],
        font=("TkDefaultFont", 9, "bold"),
    )
    style.configure(
        "Status.Horizontal.TProgressbar",
        background=palette["primary"],
        troughcolor="#e2e8f0",
        bordercolor=palette["panel_border"],
        lightcolor=palette["primary"],
        darkcolor=palette["primary"],
    )
    style.configure(
        "Advanced.TCheckbutton",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "Advanced.TLabelframe",
        background=palette["panel_bg"],
        bordercolor=palette["panel_border"],
    )
    style.configure(
        "Advanced.TLabelframe.Label",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "Advanced.TButton",
        background="#e2e8f0",
        foreground=palette["advanced_fg"],
        padding=(8, 4),
    )
    style.map("Advanced.TButton", background=[("active", "#cbd5e1")])


class GuiLayoutMixin:
    """Mixin zawierający budowę i aktualizację elementów układu GUI."""

    def _build_layout(self) -> None:
        """Zbuduj zakładki, sekcje konfiguracji oraz panel wykresów."""
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        config_tab = ttk.Frame(self.tabs)
        plots_tab = ttk.Frame(self.tabs)
        self.tabs.add(config_tab, text="Konfiguracja")
        self.tabs.add(plots_tab, text="Wykresy")

        root = ttk.Frame(config_tab, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root, style="Header.TFrame")
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(
            top,
            text="Parametry modelu poznawczego i oscylatorów Wilsona-Cowana",
            style="HeaderTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            top,
            text=(
                "Zmień parametry przed uruchomieniem symulacji. Po kliknięciu "
                "'Uruchom' wykresy pojawią się w zakładce Wykresy."
            ),
            style="HeaderSubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes, padding=(0, 0, 8, 0))
        right = ttk.Frame(panes, padding=(8, 0, 0, 0))
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        self._build_quick_start_section(left)
        self._build_advanced_options_section(right)
        self._build_results_and_plots_section(right)

        bottom = ttk.Frame(root)
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="Przywróć domyślne", command=self.reset_defaults).pack(side="left")
        ttk.Button(bottom, text="Zamknij", command=self.destroy).pack(side="right")
        ttk.Button(
            bottom,
            text="Uruchom symulację",
            command=self.start_simulation,
            style="Primary.TButton",
        ).pack(side="right", padx=(0, 8))

        self.status_var = tk.StringVar(value="Gotowe.")
        self.status_label = ttk.Label(
            root, textvariable=self.status_var, style="Status.TLabel"
        )
        self.status_label.pack(anchor="w", pady=(8, 0))
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(
            root,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Status.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(4, 0))
        self.summary_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.summary_var, justify="left").pack(anchor="w", pady=(4, 0))

        self.scenario_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._refresh_scenario_details()
        )
        self._refresh_scenario_details()
        self.T_var.trace_add("write", lambda *_: self._on_auto_dt_toggle())
        self._on_auto_dt_toggle()

        self.plot_panel = PlotWindow(plots_tab)
        self.plot_panel.pack(fill="both", expand=True)

    def _build_quick_start_section(self, parent: ttk.Frame) -> None:
        """Zbuduj sekcję szybkiego uruchomienia dla początkującego użytkownika."""
        self.sim_frame = ttk.LabelFrame(
            parent, text="Szybki start", padding=10, style="QuickStart.TLabelframe"
        )
        self.sim_frame.pack(fill="x", pady=(0, 10))

        self.T_var = tk.StringVar(value=self.state.T)
        self.scenario_var = tk.StringVar(value=self.state.scenario)
        self.save_results_var = tk.BooleanVar(value=self.state.save_results)

        scenario_label = ttk.Label(self.sim_frame, text="scenariusz")
        scenario_label.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        Tooltip(scenario_label, PARAMETER_DESCRIPTIONS["scenario"])
        self.scenario_combo = ttk.Combobox(
            self.sim_frame,
            textvariable=self.scenario_var,
            values=list_scenarios(),
            state="readonly",
            width=18,
        )
        self.scenario_combo.grid(row=0, column=1, sticky="ew", pady=3)

        t_label = ttk.Label(self.sim_frame, text="czas symulacji [s]")
        t_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        Tooltip(t_label, PARAMETER_DESCRIPTIONS["T"])
        ttk.Entry(self.sim_frame, textvariable=self.T_var, width=14).grid(
            row=1, column=1, sticky="ew", pady=3
        )

        save_checkbox = ttk.Checkbutton(
            self.sim_frame, text="Zapisz wyniki po symulacji", variable=self.save_results_var
        )
        save_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 3))
        Tooltip(save_checkbox, PARAMETER_DESCRIPTIONS["save_results"])

        ttk.Button(
            self.sim_frame,
            text="Uruchom symulację",
            command=self.start_simulation,
            style="Primary.TButton",
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 6))

        self.scenario_details_var = tk.StringVar(value="")
        details_label = ttk.Label(
            self.sim_frame,
            textvariable=self.scenario_details_var,
            justify="left",
            wraplength=500,
            style="ScenarioInfo.TLabel",
        )
        details_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        Tooltip(details_label, PARAMETER_DESCRIPTIONS["scenario_details"])
        self.sim_frame.columnconfigure(1, weight=1)

    def _build_advanced_options_section(self, parent: ttk.Frame) -> None:
        """Zbuduj zwijaną sekcję technicznych opcji uruchomienia symulacji."""
        self.advanced_options_visible_var = tk.BooleanVar(value=False)
        toggle = ttk.Checkbutton(
            parent,
            text="Pokaż opcje zaawansowane",
            variable=self.advanced_options_visible_var,
            command=self._toggle_advanced_options,
            style="Advanced.TCheckbutton",
        )
        toggle.pack(anchor="w", pady=(0, 4))

        self.advanced_options_frame = ttk.LabelFrame(
            parent, text="Opcje zaawansowane", padding=10, style="Advanced.TLabelframe"
        )
        self.advanced_options_frame.pack(fill="x", pady=(0, 10))

        self.seed_var = tk.StringVar(value=self.state.seed)
        self.dt_var = tk.StringVar(value=self.state.dt)
        self.auto_dt_var = tk.BooleanVar(value=self.state.auto_dt)
        self.command_var = tk.StringVar(value=self.state.command)
        self.batch_seeds_var = tk.StringVar(value=self.state.batch_seeds)
        self.batch_scenarios_var = tk.StringVar(value=self.state.batch_scenarios)
        self.sensitivity_var = tk.StringVar(value=self.state.sensitivity_params)
        self.sensitivity_delta_var = tk.StringVar(value=self.state.sensitivity_delta)

        self._add_labeled_entry(
            self.advanced_options_frame,
            0,
            "ziarno losowości",
            self.seed_var,
            PARAMETER_DESCRIPTIONS["seed"],
        )
        self._add_labeled_entry(
            self.advanced_options_frame,
            1,
            "krok czasowy dt [s]",
            self.dt_var,
            PARAMETER_DESCRIPTIONS["dt"],
        )
        auto_dt_checkbox = ttk.Checkbutton(
            self.advanced_options_frame,
            text="Automatyczny dobór dt",
            variable=self.auto_dt_var,
            command=self._on_auto_dt_toggle,
            style="Advanced.TCheckbutton",
        )
        auto_dt_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 3))
        Tooltip(auto_dt_checkbox, PARAMETER_DESCRIPTIONS["auto_dt"])

        command_label = ttk.Label(self.advanced_options_frame, text="tryb uruchomienia")
        command_label.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=3)
        cmd_combo = ttk.Combobox(
            self.advanced_options_frame,
            textvariable=self.command_var,
            values=["run", "batch"],
            state="readonly",
            width=18,
        )
        cmd_combo.grid(row=3, column=1, sticky="ew", pady=3)
        self._add_labeled_entry(
            self.advanced_options_frame,
            4,
            "ziarna serii",
            self.batch_seeds_var,
            None,
        )
        self._add_labeled_entry(
            self.advanced_options_frame,
            5,
            "scenariusze serii",
            self.batch_scenarios_var,
            None,
        )
        self._add_labeled_entry(
            self.advanced_options_frame,
            6,
            "parametry wrażliwości",
            self.sensitivity_var,
            None,
        )
        self._add_labeled_entry(
            self.advanced_options_frame,
            7,
            "delta wrażliwości",
            self.sensitivity_delta_var,
            None,
        )
        ttk.Button(
            self.advanced_options_frame,
            text="Parametry modelu i oscylatorów...",
            command=self._open_advanced_settings,
            style="Advanced.TButton",
        ).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.advanced_options_frame.columnconfigure(1, weight=1)
        self._toggle_advanced_options()

    def _add_labeled_entry(
        self,
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
        ttk.Entry(parent, textvariable=variable, width=14).grid(
            row=row, column=1, sticky="ew", pady=3
        )

    def _toggle_advanced_options(self) -> None:
        """Pokaż albo ukryj sekcję opcji zaawansowanych."""
        if self.advanced_options_visible_var.get():
            pack_options: dict[str, Any] = {"fill": "x", "pady": (0, 10)}
            if hasattr(self, "plots_frame"):
                pack_options["before"] = self.plots_frame
            self.advanced_options_frame.pack(**pack_options)
        else:
            self.advanced_options_frame.pack_forget()

    def _build_results_and_plots_section(self, parent: ttk.Frame) -> None:
        """Zbuduj panel wyników i szczegółowego wyboru wykresów z presetami."""
        self.plots_frame = ttk.LabelFrame(parent, text="Wyniki i wykresy", padding=10)
        self.plots_frame.pack(fill="both", expand=True)

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
        if not self.state.plots:
            self.state.plots = dict(default_plots)
        self.plot_vars: Dict[str, tk.BooleanVar] = {
            name: tk.BooleanVar(value=self.state.plots.get(name, value))
            for name, value in default_plots.items()
        }
        self.plot_preset_var = tk.StringVar(value="Pełne")
        preset_frame = ttk.Frame(self.plots_frame)
        preset_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(preset_frame, text="Preset wykresów:").pack(side="left", padx=(0, 8))
        for preset_name in ("Podstawowe", "Diagnostyczne", "Pełne"):
            ttk.Radiobutton(
                preset_frame,
                text=preset_name,
                value=preset_name,
                variable=self.plot_preset_var,
                command=self._apply_plot_preset,
            ).pack(side="left", padx=(0, 8))

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

        for row, key in enumerate(self.plot_vars, start=1):
            checkbox = ttk.Checkbutton(
                self.plots_frame,
                text=labels[key],
                variable=self.plot_vars[key],
                command=self._sync_plot_preset_from_vars,
            )
            checkbox.grid(row=row, column=0, sticky="w", pady=2)
            Tooltip(checkbox, plot_tooltips[key])
        self.plots_frame.columnconfigure(0, weight=1)

    def _plot_preset_keys(self, preset_name: str) -> set[str]:
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
        return set(self.plot_vars)

    def _apply_plot_preset(self) -> None:
        """Ustaw widoczność wykresów zgodnie z aktualnie wybranym presetem."""
        active_keys = self._plot_preset_keys(self.plot_preset_var.get())
        for name, var in self.plot_vars.items():
            var.set(name in active_keys)
        self._sync_state_from_controls()

    def _sync_plot_preset_from_vars(self) -> None:
        """Dopasuj nazwę presetu do aktualnych wartości pól wykresów, jeśli to możliwe."""
        active_keys = {name for name, var in self.plot_vars.items() if var.get()}
        for preset_name in ("Podstawowe", "Diagnostyczne", "Pełne"):
            if active_keys == self._plot_preset_keys(preset_name):
                self.plot_preset_var.set(preset_name)
                return
        self.plot_preset_var.set("Niestandardowe")

    def _build_menu(self) -> None:
        """Zbuduj główne menu aplikacji."""
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nowa instancja", command=self._open_new_instance)
        file_menu.add_separator()
        file_menu.add_command(label="Zapisz konfigurację...", command=self._save_current_config)
        file_menu.add_command(label="Wczytaj konfigurację...", command=self._load_existing_config)
        file_menu.add_separator()
        file_menu.add_command(label="Zamknij", command=self.destroy)
        menubar.add_cascade(label="Plik", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Konfiguracja symulacji", command=lambda: self.tabs.select(0))
        edit_menu.add_command(label="Konfiguracja wykresów", command=self._focus_plots_section)
        edit_menu.add_command(
            label="Parametry globalne (BrainParams)", command=self._open_advanced_settings
        )
        edit_menu.add_command(label="Parametry oscylatorów", command=self._open_advanced_settings)
        edit_menu.add_separator()
        edit_menu.add_command(label="Przywróć domyślne", command=self.reset_defaults)
        menubar.add_cascade(label="Edycja", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Instrukcja używania", command=self._show_usage_help)
        help_menu.add_command(label="O programie", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _focus_plots_section(self) -> None:
        """Przenieś fokus na sekcję wyboru wykresów."""
        self.tabs.select(0)
        self.plots_frame.focus_set()

    def _open_advanced_settings(self) -> None:
        """Otwórz okno edycji zaawansowanych parametrów modelu."""
        win = tk.Toplevel(self)
        win.title("Parametry zaawansowane")
        win.geometry("860x680")

        container = ttk.Frame(win, padding=10)
        container.pack(fill="both", expand=True)

        brain = ParameterForm(
            container,
            "Parametry globalne BrainParams",
            BrainParams,
            self.brain_defaults,
            include_fields=[
                f.name for f in fields(BrainParams) if f.name not in RULE_FIELDS and f.name != "dt"
            ],
        )
        brain.pack(fill="both", expand=True, pady=(0, 10))
        osc = ParameterForm(
            container, "Parametry WilsonCowanParams", WilsonCowanParams, self.osc_defaults
        )
        osc.pack(fill="both", expand=True)

        self._sync_state_from_controls()
        self._sync_advanced_forms_from_state(brain, osc)

        def save_and_close() -> None:
            """Zapisz wartości z okna zaawansowanego i zamknij okno."""
            self._sync_state_from_controls()
            try:
                self._sync_state_from_advanced_forms(brain, osc)
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

    def _refresh_scenario_details(self) -> None:
        """Odśwież opis bieżącego scenariusza w panelu konfiguracji."""
        self.state.scenario = self.scenario_var.get()
        scenario = get_scenario(self.state.scenario)
        self.scenario_details_var.set(
            f"Krótki opis: {scenario.description}\n"
            f"Przewidywane wyniki: {scenario.what_changes}\n"
            f"Sugerowany czas: {scenario.duration_hint:.1f} s"
        )

    @staticmethod
    def _auto_dt_for_duration(duration_s: float) -> float:
        """Wyznacz bezpieczny krok czasowy dla podanego czasu symulacji."""
        target_steps = 2400.0
        raw_dt = duration_s / target_steps
        return max(0.001, min(0.01, raw_dt))

    def _on_auto_dt_toggle(self) -> None:
        """Zaktualizuj krok czasowy, jeśli aktywny jest automatyczny dobór dt."""
        if self.auto_dt_var.get():
            try:
                T = float(self.T_var.get())
            except ValueError:
                return
            self.dt_var.set(f"{self._auto_dt_for_duration(T):.4f}")
            self.state.dt = self.dt_var.get()

    def _open_new_instance(self) -> None:
        """Uruchom nowe okno programu jako osobny proces."""
        try:
            root_dir = Path(__file__).resolve().parents[1]
            entrypoint = root_dir / "main_gui.py"
            if not entrypoint.exists():
                raise FileNotFoundError(f"Nie znaleziono pliku startowego: {entrypoint}")
            subprocess.Popen([sys.executable, str(entrypoint)], cwd=str(root_dir))
            self.status_var.set("Uruchomiono nową instancję programu.")
        except Exception as exc:
            messagebox.showerror("Błąd", f"Nie udało się uruchomić nowej instancji: {exc}")

    def _apply_run_result(self, payload: tuple[Any, ...]) -> None:
        """Przenieś wynik symulacji do panelu wykresów i statusu."""
        (
            msg,
            summary_text,
            save_info,
            model,
            time,
            activity,
            diagnostics,
            oscillations,
            behavior,
        ) = payload
        self._sync_state_from_controls()
        self.plot_panel.clear()
        has_plots = False
        if self.state.plots.get("activity", False):
            self.plot_panel.add_plot(
                "Aktywacje", draw_activity, time, activity, model.names, model.idx, figsize=(11, 7)
            )
            has_plots = True
        if self.state.plots.get("simulated_brain_activity", False):
            self.plot_panel.add_plot(
                "Aktywność mózgu",
                draw_simulated_brain_activity,
                time,
                activity,
                model.names,
                model.idx,
                figsize=(11, 7),
            )
            has_plots = True
        if self.state.plots.get("brain_region_projections", False):
            self.plot_panel.add_plot(
                "Rzuty mózgu SVG",
                draw_brain_region_projections,
                time,
                activity,
                model.names,
                model.idx,
                figsize=(11, 8),
            )
            has_plots = True
        if self.state.plots.get("region_activity_2d", False):
            self.plot_panel.add_plot(
                "Regiony 2D w czasie",
                draw_region_activity_2d,
                time,
                activity,
                model.names,
                model.idx,
                figsize=(11, 8),
            )
            has_plots = True
        if self.state.plots.get("diagnostics", False):
            self.plot_panel.add_plot(
                "Diagnostyka", draw_diagnostics, time, diagnostics, figsize=(11, 5)
            )
            has_plots = True
        if self.state.plots.get("behavior", False):
            self.plot_panel.add_plot("Behavior", draw_behavior, time, behavior, figsize=(11, 5))
            has_plots = True
        if self.state.plots.get("eeg", False):
            self.plot_panel.add_plot(
                "EEG modułów",
                draw_eeg_modules,
                time,
                oscillations,
                model.names,
                model.idx,
                figsize=(11, 6),
            )
            has_plots = True
        if self.state.plots.get("band_power", False):
            self.plot_panel.add_plot(
                "Moc pasm", draw_band_power, time, oscillations, figsize=(11, 8)
            )
            has_plots = True
        if self.state.plots.get("weight_trajectories", False):
            self.plot_panel.add_plot(
                "Trajektorie wag", draw_weight_trajectories, time, diagnostics, figsize=(11, 5)
            )
            has_plots = True
        if self.state.plots.get("weight_deltas", False):
            self.plot_panel.add_plot(
                "Przyrosty wag", draw_weight_deltas, time, diagnostics, figsize=(11, 5)
            )
            has_plots = True
        if self.state.plots.get("scenario_channels", False):
            self.plot_panel.add_plot(
                "Kanały scenariusza",
                draw_scenario_channels,
                time,
                get_scenario(self.state.scenario),
                figsize=(11, 5),
            )
            has_plots = True
        if self.state.plots.get("scenario_timeline", False):
            self.plot_panel.add_plot(
                "Oś czasu scenariusza",
                draw_scenario_timeline,
                time,
                get_scenario(self.state.scenario),
                figsize=(11, 4),
            )
            has_plots = True
        self.tabs.select(1 if has_plots else 0)
        self.status_label.configure(style="Status.TLabel")
        self.status_var.set(msg)
        self.summary_var.set(summary_text)
        self.progress_var.set(100.0)

    def _show_usage_help(self) -> None:
        """Pokaż użytkownikowi krótką instrukcję obsługi GUI."""
        messagebox.showinfo(
            "Instrukcja używania",
            (
                "Szybki przepływ dla początkującego:\n"
                "1) W sekcji 'Szybki start' wybierz scenariusz.\n"
                "2) Ustaw czas symulacji w sekundach.\n"
                "3) Kliknij 'Uruchom symulację'.\n"
                "4) Obejrzyj wyniki w zakładce 'Wykresy'.\n\n"
                "Opcjonalnie:\n"
                "- Zostaw włączone 'Zapisz wyniki po symulacji', aby zapisać pliki w outputs/.\n"
                "- W panelu 'Wyniki i wykresy' wybierz preset: Podstawowe, "
                "Diagnostyczne lub Pełne.\n"
                "- Rozwiń 'Opcje zaawansowane' tylko wtedy, gdy chcesz zmienić ziarno, "
                "dt, tryb serii albo analizę wrażliwości.\n\n"
                "Menu Plik zapisuje i wczytuje konfigurację bez zmiany jej dotychczasowego formatu."
            ),
        )

    def _show_about(self) -> None:
        """Pokaż informacje o wersji aplikacji."""
        messagebox.showinfo(
            "O programie",
            (
                "Cognitive Brain Model\n"
                f"Wersja: {APP_VERSION}\n"
                f"Ostatnia aktualizacja: {LAST_UPDATED}\n"
                f"Autor: {APP_AUTHOR}"
            ),
        )

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
