"""
Tkinter GUI for configuring and running the cognitive brain model.

The GUI intentionally uses only Python's standard library plus the project's
existing dependencies: numpy and matplotlib. It allows changing global model
parameters, Wilson-Cowan oscillator parameters, simulation time, random seed,
and selected plots before running the simulation.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import fields
from tkinter import messagebox, ttk
from typing import Dict

from .model import CognitiveBrainModel
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .plotting import (
    PlotWindow,
    draw_activity,
    draw_band_power,
    draw_diagnostics,
    draw_eeg_modules,
)


PARAMETER_DESCRIPTIONS = {
    "T": "Czas trwania symulacji w sekundach. Typowo 10-120 s; większe wartości pokazują dłuższe trendy, ale wydłużają obliczenia.",
    "seed": "Ziarno generatora losowego. Typowo dowolna liczba całkowita; ta sama wartość daje powtarzalny przebieg szumu i oscylacji.",
    "dt": "Krok czasowy symulacji. Typowo 0.001-0.01; mniejszy krok zwiększa dokładność i koszt, większy może wygładzić lub zdestabilizować dynamikę.",
    "noise": "Skala szumu neuronalnego. Typowo 0.0-0.05; większa wartość zwiększa zmienność aktywacji i może maskować słabe efekty bodźców.",
    "gw_threshold": "Próg zapłonu global workspace. Typowo 0.4-0.8; niższy ułatwia globalną aktywację, wyższy wymaga silniejszej uwagi lub salience.",
    "gw_gain": "Stromość funkcji zapłonu global workspace. Typowo 5-20; większa wartość daje bardziej skokowe przejście między brakiem i obecnością zapłonu.",
    "learning_rate_semantic": "Tempo uczenia semantycznego. Typowo 0.0-0.02; większa wartość szybciej wzmacnia SEM przez HIP i GW.",
    "learning_rate_value": "Tempo uczenia wartościowania. Typowo 0.0-0.08; większa wartość szybciej zmienia VAL po błędzie predykcji nagrody.",
    "decay_semantic": "Zanik śladu semantycznego. Typowo 0.0-0.01; większa wartość szybciej wygasza SEM i ogranicza długotrwałe utrzymanie reprezentacji.",
    "enable_oscillators": "Włącza oscylatory Wilsona-Cowana. Typowo włączone; wyłączenie zeruje sygnały EEG i moc pasmową, ale zostawia dynamikę poznawczą.",
    "w_ee": "Samowzmacnianie populacji pobudzającej. Typowo 8-14; większa wartość wzmacnia amplitudę i może ułatwiać oscylacje.",
    "w_ei": "Hamowanie populacji pobudzającej przez I. Typowo 7-12; większa wartość mocniej tłumi E i może zmniejszać amplitudę EEG.",
    "w_ie": "Pobudzanie populacji hamującej przez E. Typowo 8-13; większa wartość wzmacnia sprzężenie E-I i wpływa na rytmiczność.",
    "w_ii": "Samooddziaływanie populacji hamującej. Typowo 0.5-2.0; większa wartość zmienia poziom hamowania i stabilność oscylatora.",
    "baseline_e": "Bazowy napęd populacji pobudzającej. Typowo -3.5 do -1.0; mniej ujemny podnosi aktywność E i zwiększa podatność na napęd poznawczy.",
    "baseline_i": "Bazowy napęd populacji hamującej. Typowo -4.0 do -1.5; mniej ujemny wzmacnia hamowanie i zmienia równowagę E-I.",
    "cognitive_drive_gain": "Wpływ aktywności poznawczej na oscylatory. Typowo 1-5; większa wartość silniej przekłada aktywacje modułów na EEG.",
    "coupling_gain": "Sprzężenie międzymodułowe oscylatorów. Typowo 0.0-1.0; większa wartość zwiększa synchronizację i propagację aktywności między modułami.",
    "oscillator_noise": "Szum oscylatorów Wilsona-Cowana. Typowo 0.0-0.05; większa wartość dodaje nieregularność do sygnałów EEG.",
    "phase_drive_gain": "Pomocniczy napęd fazy stabilizujący pasmo EEG. Typowo 0.0-0.3; większa wartość wzmacnia rytmiczność przypisanego pasma.",
}


class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        ttk.Label(
            self.tip,
            text=self.text,
            padding=(8, 5),
            relief="solid",
            borderwidth=1,
            background="#ffffe0",
            wraplength=420,
        ).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


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

            label = ttk.Label(self, text=name)
            label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            Tooltip(label, PARAMETER_DESCRIPTIONS.get(name, ""))

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
        self.geometry("1180x780")
        self.minsize(940, 660)

        self.brain_defaults = BrainParams()
        self.osc_defaults = WilsonCowanParams()

        self._build_layout()

    def _build_layout(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        config_tab = ttk.Frame(self.tabs)
        plots_tab = ttk.Frame(self.tabs)
        self.tabs.add(config_tab, text="Konfiguracja")
        self.tabs.add(plots_tab, text="Wykresy")

        root = ttk.Frame(config_tab, padding=12)
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
            text="Zmień parametry przed uruchomieniem symulacji. Po kliknięciu 'Uruchom' wykresy pojawią się w zakładce Wykresy.",
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

        t_label = ttk.Label(self.sim_frame, text="czas symulacji T [s]")
        t_label.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        Tooltip(t_label, PARAMETER_DESCRIPTIONS["T"])
        ttk.Entry(self.sim_frame, textvariable=self.T_var, width=14).grid(row=0, column=1, sticky="ew", pady=3)

        seed_label = ttk.Label(self.sim_frame, text="seed")
        seed_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        Tooltip(seed_label, PARAMETER_DESCRIPTIONS["seed"])
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

        self.plot_panel = PlotWindow(plots_tab)
        self.plot_panel.pack(fill="both", expand=True)

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

            self.plot_panel.clear()
            has_plots = False

            if self.plot_vars["activity"].get():
                self.plot_panel.add_plot(
                    "Aktywacje",
                    draw_activity,
                    time,
                    activity,
                    model.names,
                    model.idx,
                    figsize=(11, 7),
                )
                has_plots = True
            if self.plot_vars["diagnostics"].get():
                self.plot_panel.add_plot(
                    "Diagnostyka",
                    draw_diagnostics,
                    time,
                    diagnostics,
                    figsize=(11, 5),
                )
                has_plots = True
            if self.plot_vars["eeg"].get():
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
            if self.plot_vars["band_power"].get():
                self.plot_panel.add_plot(
                    "Moc pasm",
                    draw_band_power,
                    time,
                    oscillations,
                    figsize=(11, 8),
                )
                has_plots = True

            if has_plots:
                self.tabs.select(1)
            else:
                self.tabs.select(0)

            self.status_var.set("Symulacja zakończona.")

        except Exception as exc:
            self.status_var.set("Błąd konfiguracji.")
            messagebox.showerror("Błąd", str(exc))


def run_gui():
    app = BrainModelGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
