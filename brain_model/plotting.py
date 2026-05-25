from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


MODULE_DESCRIPTIONS = {
    "VIS": "Przetwarzanie wzrokowe.",
    "AUD": "Przetwarzanie słuchowe.",
    "INT": "Sygnały interoceptywne.",
    "SAL": "Sieć salience: istotność, zaskoczenie i zagrożenie.",
    "ATT": "Uwaga i wzmocnienie precyzji sygnałów.",
    "PHON": "Pętla fonologiczna pamięci roboczej.",
    "VSWM": "Wzrokowo-przestrzenna pamięć robocza.",
    "EXEC": "Kontrola wykonawcza i utrzymanie celu zadania.",
    "EPIS": "Bufor epizodyczny.",
    "SEM": "Pamięć semantyczna.",
    "HIP": "Hipokamp i integracja epizodyczna.",
    "VAL": "Wartościowanie i sygnał nagrody.",
    "MOT": "Przygotowanie odpowiedzi ruchowej.",
    "DMN": "Default mode network: aktywność spoczynkowa.",
    "GW": "Global workspace: globalne udostępnienie reprezentacji.",
}

DIAGNOSTIC_DESCRIPTIONS = {
    "błąd predykcji": "Różnica między bodźcem a predykcją sensoryczną.",
    "global workspace ignition": "Nieliniowy zapłon global workspace.",
    "błąd predykcji nagrody": "Różnica między nagrodą a aktualnym wartościowaniem.",
    "noradrenalina": "Pobudzenie zależne od niepewności, zaskoczenia i zagrożenia.",
    "acetylocholina": "Wzrost precyzji sygnałów związany z zadaniem i uwagą.",
}

BAND_DESCRIPTIONS = {
    "theta": "Pasmo theta: hipokamp, bufor epizodyczny i pamięć robocza.",
    "alpha": "Pasmo alfa: hamowanie i bramkowanie sensoryczne.",
    "beta": "Pasmo beta: kontrola wykonawcza i nastawienie zadaniowe.",
    "gamma": "Pasmo gamma: lokalne wiązanie cech i reprezentacji.",
}


def _describe(label):
    return MODULE_DESCRIPTIONS.get(label) or DIAGNOSTIC_DESCRIPTIONS.get(label) or BAND_DESCRIPTIONS.get(label) or label


def _attach_line_tooltips(fig, axes):
    annotation = axes[0].annotate(
        "",
        xy=(0, 0),
        xytext=(14, 14),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.3", "fc": "#ffffe0", "ec": "#777777", "alpha": 0.95},
        arrowprops={"arrowstyle": "->", "color": "#777777"},
    )
    annotation.set_visible(False)

    def on_move(event):
        if event.inaxes not in axes:
            if annotation.get_visible():
                annotation.set_visible(False)
                fig.canvas.draw_idle()
            return

        best = None
        for ax in axes:
            for line in ax.get_lines():
                contains, info = line.contains(event)
                if not contains:
                    continue
                ind = info.get("ind", [0])[0]
                x_data = line.get_xdata()
                y_data = line.get_ydata()
                if len(x_data) == 0:
                    continue
                best = (ax, line, x_data[ind], y_data[ind])
                break
            if best:
                break

        if not best:
            if annotation.get_visible():
                annotation.set_visible(False)
                fig.canvas.draw_idle()
            return

        _, line, x_value, y_value = best
        label = line.get_label()
        annotation.xy = (x_value, y_value)
        annotation.set_text(f"{label}\n{_describe(label)}\nt={x_value:.3g}, y={y_value:.3g}")
        annotation.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)


def _style_lines(ax):
    for line in ax.get_lines():
        line.set_picker(6)


def draw_activity(ax, time, activity, names, idx):
    selected = [
        "VIS", "AUD", "SAL", "ATT", "PHON", "VSWM",
        "EXEC", "EPIS", "SEM", "HIP", "VAL", "MOT", "DMN", "GW"
    ]

    for name in selected:
        ax.plot(time, activity[:, idx[name]], label=name)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Aktywacja modułu [0-1]")
    ax.set_title("Mezoskopowa dynamika procesów poznawczych")
    ax.legend(ncol=4, fontsize=9)
    _style_lines(ax)


def draw_diagnostics(ax, time, diagnostics):
    ax.plot(time, diagnostics["prediction_error"], label="błąd predykcji")
    ax.plot(time, diagnostics["gw_ignition"], label="global workspace ignition")
    ax.plot(time, diagnostics["dopamine_delta"], label="błąd predykcji nagrody")
    ax.plot(time, diagnostics["noradrenaline"], label="noradrenalina")
    ax.plot(time, diagnostics["acetylcholine"], label="acetylocholina")

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Wartość")
    ax.set_title("Zmienne obliczeniowe i neuromodulacyjne")
    ax.legend()
    _style_lines(ax)


def draw_eeg_modules(ax, time, oscillations, names, idx):
    selected = ["HIP", "VSWM", "VIS", "AUD", "EXEC", "ATT", "SEM", "GW"]
    eeg = oscillations["eeg"]

    for name in selected:
        ax.plot(time, eeg[:, idx[name]], label=name)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Sygnał EEG aproksymowany jako E-I")
    ax.set_title("Oscylatory Wilsona-Cowana dla wybranych modułów")
    ax.legend(ncol=4, fontsize=9)
    _style_lines(ax)


def draw_band_power(ax, time, oscillations):
    band_power = oscillations["band_power"]

    for band in ["theta", "alpha", "beta", "gamma"]:
        ax.plot(time, band_power[band], label=band)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Uproszczona moc pasmowa")
    ax.set_title("Symulowana dynamika pasm EEG")
    ax.legend()
    _style_lines(ax)


def _show_standalone(draw_func, *args, figsize=(14, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    draw_func(ax, *args)
    fig.tight_layout()
    _attach_line_tooltips(fig, [ax])
    plt.show()


def plot_activity(time, activity, names, idx):
    _show_standalone(draw_activity, time, activity, names, idx, figsize=(14, 8))


def plot_diagnostics(time, diagnostics):
    _show_standalone(draw_diagnostics, time, diagnostics, figsize=(14, 4))


def plot_eeg_modules(time, oscillations, names, idx):
    _show_standalone(draw_eeg_modules, time, oscillations, names, idx, figsize=(14, 6))


def plot_band_power(time, oscillations):
    _show_standalone(draw_band_power, time, oscillations, figsize=(14, 4))


class PlotWindow(tk.Toplevel):
    """Single Tk window that embeds all selected matplotlib plots."""

    def __init__(self, parent, title="Wykresy symulacji"):
        super().__init__(parent)
        self.title(title)
        self.geometry("1180x780")
        self.minsize(900, 620)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.status = ttk.Label(
            self,
            text="Pasek narzędzi Matplotlib: ikony lupy i przesuwania służą do przybliżania oraz nawigacji po wykresie.",
            anchor="w",
        )
        self.status.pack(fill="x", padx=8, pady=(0, 6))

        self._figures = []
        self._canvases = []

    def add_plot(self, tab_title, draw_func, *args, figsize=(10, 6)):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=tab_title)

        fig = Figure(figsize=figsize, dpi=100)
        ax = fig.add_subplot(111)
        draw_func(ax, *args)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        _attach_line_tooltips(fig, [ax])
        toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="top", fill="x")
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        canvas.draw()

        self._figures.append(fig)
        self._canvases.append(canvas)

    def fit_tabs_to_count(self):
        tab_count = len(self.notebook.tabs())
        if tab_count <= 1:
            return
        width = min(1320, max(980, 260 * tab_count))
        height = min(900, max(700, 170 * math.ceil(tab_count / 2)))
        self.geometry(f"{width}x{height}")
