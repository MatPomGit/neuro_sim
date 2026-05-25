"""
Tkinter GUI for configuring and running the cognitive brain model.

The GUI intentionally uses only Python's standard library plus the project's
existing dependencies: numpy and matplotlib. It allows changing global model
parameters, Wilson-Cowan oscillator parameters, simulation time, random seed,
and selected plots before running the simulation.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import fields
from typing import Callable, Dict, Any

from .model import CognitiveBrainModel
from .params import BrainParams
from .oscillators import WilsonCowanParams
from .plotting import (
    plot_activity,
    plot_band_power,
    plot_diagnostics,
    plot_eeg_modules,
)


class ParameterForm(ttk.LabelFrame):
    """Small helper widget that builds labeled entries for a dataclass."""

    def __init__(self, parent, title: str, dataclass_type, defaults):
        super().__init__(parent, text=title, padding=10)
        self.dataclass_type = dataclass_type
        self.defaults = defaults
        self.vars: Dict[str, tk.Variable] = {}

        for row, field in enumerate(fields(dataclass_type)):
            name = field.name
            value = getattr(defaults, name)

            ttk.Label(self, text=name).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                widget = ttk.Checkbutton(self, variable=var)
                widget.grid(row=row, column=1, sticky="w", pady=3)
            else:
                var = tk.StringVar(value=str(value))
                widget = ttk.Entry(self, textvariable=var, width=14)
                widget.grid(row=row, column=1, sticky="ew", pady=3)

            self.vars[name] = var

        self.columnconfigure(1, weight=1)

    def values(self):
        kwargs = {}
        for field in fields(self.dataclass_type):
            name = field.name
            default_value = getattr(self.defaults, name)
            raw = self.vars[name].get()

            try:
                if isinstance(default_value, bool):
                    kwargs[name] = bool(raw)
                elif isinstance(default_value, int) and not isinstance(default_value, bool):
                    kwargs[name] = int(raw)
                else:
                    kwargs[name] = float(raw)
            except ValueError as exc:
                raise ValueError(f"Niepoprawna wartość parametru '{name}': {raw}") from exc

        return self.dataclass_type(**kwargs)

    def reset(self):
        for field in fields(self.dataclass_type):
            name = field.name
            value = getattr(self.defaults, name)
            self.vars[name].set(value if isinstance(value, bool) else str(value))


class BrainModelGUI(tk.Tk):
    """Main GUI window."""

    def __init__(self):
        super().__init__()
        self.title("Cognitive Brain Model - konfiguracja symulacji")
        self.geometry("920x720")
        self.minsize(860, 640)

        self.brain_defaults = BrainParams()
        self.osc_defaults = WilsonCowanParams()

        self._build_layout()

    def _build_layout(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(
            top,
            text="Parametry modelu poznawczego i oscylatorów Wilsona-Cowana",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            top,
            text="Zmień parametry przed uruchomieniem symulacji. Po kliknięciu 'Uruchom' zostaną wygenerowane wykresy matplotlib.",
        ).pack(anchor="w", pady=(3, 0))

        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes, padding=(0, 0, 8, 0))
        right = ttk.Frame(panes, padding=(8, 0, 0, 0))
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        self.sim_frame = ttk.LabelFrame(left, text="Symulacja", padding=10)
        self.sim_frame.pack(fill="x", pady=(0, 10))

        self.T_var = tk.StringVar(value="45.0")
        self.seed_var = tk.StringVar(value="7")

        ttk.Label(self.sim_frame, text="czas symulacji T [s]").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(self.sim_frame, textvariable=self.T_var, width=14).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Label(self.sim_frame, text="seed").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(self.sim_frame, textvariable=self.seed_var, width=14).grid(row=1, column=1, sticky="ew", pady=3)
        self.sim_frame.columnconfigure(1, weight=1)

        self.brain_form = ParameterForm(left, "Parametry globalne BrainParams", BrainParams, self.brain_defaults)
        self.brain_form.pack(fill="both", expand=True)

        self.osc_form = ParameterForm(right, "Parametry WilsonCowanParams", WilsonCowanParams, self.osc_defaults)
        self.osc_form.pack(fill="both", expand=True, pady=(0, 10))

        self.plots_frame = ttk.LabelFrame(right, text="Wykresy", padding=10)
        self.plots_frame.pack(fill="x")

        self.plot_vars: Dict[str, tk.BooleanVar] = {
            "activity": tk.BooleanVar(value=True),
            "diagnostics": tk.BooleanVar(value=True),
            "eeg": tk.BooleanVar(value=True),
            "band_power": tk.BooleanVar(value=True),
        }

        labels = {
            "activity": "aktywacje modułów poznawczych",
            "diagnostics": "zmienne diagnostyczne i neuromodulacyjne",
            "eeg": "sygnały EEG E-I dla wybranych modułów",
            "band_power": "moc pasm theta/alpha/beta/gamma",
        }

        for row, key in enumerate(self.plot_vars):
            ttk.Checkbutton(self.plots_frame, text=labels[key], variable=self.plot_vars[key]).grid(
                row=row, column=0, sticky="w", pady=2
            )

        bottom = ttk.Frame(root)
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="Przywróć domyślne", command=self.reset_defaults).pack(side="left")
        ttk.Button(bottom, text="Uruchom symulację", command=self.run_simulation).pack(side="right")

        self.status_var = tk.StringVar(value="Gotowe.")
        ttk.Label(root, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))

    def reset_defaults(self):
        self.T_var.set("45.0")
        self.seed_var.set("7")
        self.brain_form.reset()
        self.osc_form.reset()
        for var in self.plot_vars.values():
            var.set(True)
        self.status_var.set("Przywrócono wartości domyślne.")

    def _read_scalar_params(self):
        try:
            T = float(self.T_var.get())
            seed = int(self.seed_var.get())
        except ValueError as exc:
            raise ValueError("Niepoprawny czas symulacji lub seed.") from exc

        if T <= 0:
            raise ValueError("Czas symulacji T musi być większy od zera.")

        return T, seed

    def run_simulation(self):
        try:
            T, seed = self._read_scalar_params()
            brain_params = self.brain_form.values()
            oscillator_params = self.osc_form.values()

            if brain_params.dt <= 0:
                raise ValueError("dt musi być większe od zera.")
            if brain_params.noise < 0:
                raise ValueError("noise nie może być ujemny.")
            if oscillator_params.oscillator_noise < 0:
                raise ValueError("oscillator_noise nie może być ujemny.")

            self.status_var.set("Symulacja w toku...")
            self.update_idletasks()

            model = CognitiveBrainModel(
                params=brain_params,
                oscillator_params=oscillator_params,
                seed=seed,
            )
            time, activity, diagnostics, oscillations = model.simulate(T=T)

            if self.plot_vars["activity"].get():
                plot_activity(time, activity, model.names, model.idx)
            if self.plot_vars["diagnostics"].get():
                plot_diagnostics(time, diagnostics)
            if self.plot_vars["eeg"].get():
                plot_eeg_modules(time, oscillations, model.names, model.idx)
            if self.plot_vars["band_power"].get():
                plot_band_power(time, oscillations)

            self.status_var.set("Symulacja zakończona.")

        except Exception as exc:
            self.status_var.set("Błąd konfiguracji.")
            messagebox.showerror("Błąd", str(exc))


def run_gui():
    app = BrainModelGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
