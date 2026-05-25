from __future__ import annotations

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
    "serotonina": "Regulacja nastroju i obniżanie reaktywności na stresory.",
    "gaba": "Dominująca inhibicja stabilizująca pobudzenie sieci neuronowych.",
    "glutaminian": "Dominujący neuroprzekaźnik pobudzający wzmacniający transmisję korową.",
    "endorfiny": "Endogenna analgezja i tłumienie awersyjnego komponentu stresu.",
    "kortyzol": "Hormonalna odpowiedź stresowa osi HPA, rośnie przy zagrożeniu i niepewności.",
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
    annotations = {}
    for ax in axes:
        annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "#ffffe0", "ec": "#777777", "alpha": 0.95},
            arrowprops={"arrowstyle": "->", "color": "#777777"},
        )
        annotation.set_visible(False)
        annotations[ax] = annotation

    def hide_annotations():
        changed = False
        for annotation in annotations.values():
            if annotation.get_visible():
                annotation.set_visible(False)
                changed = True
        if changed:
            fig.canvas.draw_idle()

    def on_move(event):
        if event.inaxes not in axes:
            hide_annotations()
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
            hide_annotations()
            return

        ax, line, x_value, y_value = best
        label = line.get_label()
        for other_ax, other_annotation in annotations.items():
            if other_ax is not ax:
                other_annotation.set_visible(False)
        annotation = annotations[ax]
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
    return [ax]


def draw_diagnostics(ax, time, diagnostics):
    ax.plot(time, diagnostics["prediction_error"], label="błąd predykcji")
    ax.plot(time, diagnostics["gw_ignition"], label="global workspace ignition")
    ax.plot(time, diagnostics["dopamine_delta"], label="błąd predykcji nagrody")
    ax.plot(time, diagnostics["noradrenaline"], label="noradrenalina")
    ax.plot(time, diagnostics["acetylcholine"], label="acetylocholina")
    ax.plot(time, diagnostics["serotonin"], label="serotonina")
    ax.plot(time, diagnostics["gaba"], label="gaba")
    ax.plot(time, diagnostics["glutamate"], label="glutaminian")
    ax.plot(time, diagnostics["endorphins"], label="endorfiny")
    ax.plot(time, diagnostics["cortisol"], label="kortyzol")

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Wartość")
    ax.set_title("Zmienne obliczeniowe i neuromodulacyjne")
    ax.legend()
    _style_lines(ax)
    return [ax]




def draw_weight_trajectories(ax, time, diagnostics):
    history = diagnostics.get("weight_history", {})
    weights = history.get("weights", {})

    if not weights:
        ax.text(0.5, 0.5, "Brak adaptacji wag lub brak wybranych par modułów.", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Trajektorie wybranych wag W")
        ax.set_xlabel("Czas symulacji [s]")
        ax.set_ylabel("Waga")
        return [ax]

    for pair_name, values in sorted(weights.items()):
        ax.plot(time, values, label=pair_name)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Wartość wagi")
    ax.set_title("Trajektorie adaptowanych wag W")
    ax.legend(fontsize=8, ncol=2)
    _style_lines(ax)
    return [ax]


def draw_weight_deltas(ax, time, diagnostics):
    history = diagnostics.get("weight_history", {})
    deltas = history.get("deltas", {})

    if not deltas:
        ax.text(0.5, 0.5, "Brak zmian wag do wizualizacji.", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Zmiany wag ΔW")
        ax.set_xlabel("Czas symulacji [s]")
        ax.set_ylabel("ΔW / krok")
        return [ax]

    for pair_name, values in sorted(deltas.items()):
        ax.plot(time, values, label=pair_name)

    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("ΔW / krok")
    ax.set_title("Przyrosty adaptowanych wag")
    ax.legend(fontsize=8, ncol=2)
    _style_lines(ax)
    return [ax]
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
    return [ax]


def draw_band_power(ax, time, oscillations):
    band_power = oscillations["band_power"]
    fig = ax.figure
    ax.remove()
    axes = fig.subplots(4, 1, sharex=True)

    for band_ax, band in zip(axes, ["theta", "alpha", "beta", "gamma"]):
        band_ax.plot(time, band_power[band], label=band)
        band_ax.set_ylabel(band)
        band_ax.legend(loc="upper right")
        _style_lines(band_ax)

    axes[0].set_title("Symulowana dynamika pasm EEG")
    axes[-1].set_xlabel("Czas symulacji [s]")
    fig.supylabel("Uproszczona moc pasmowa")
    return list(axes)


def _show_standalone(draw_func, *args, figsize=(14, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    axes = draw_func(ax, *args) or [ax]
    fig.tight_layout()
    _attach_line_tooltips(fig, axes)
    plt.show()


def plot_activity(time, activity, names, idx):
    _show_standalone(draw_activity, time, activity, names, idx, figsize=(14, 8))


def plot_diagnostics(time, diagnostics):
    _show_standalone(draw_diagnostics, time, diagnostics, figsize=(14, 4))


def plot_eeg_modules(time, oscillations, names, idx):
    _show_standalone(draw_eeg_modules, time, oscillations, names, idx, figsize=(14, 6))


def plot_band_power(time, oscillations):
    _show_standalone(draw_band_power, time, oscillations, figsize=(14, 8))


class PlotWindow(ttk.Frame):
    """Tk frame that embeds all selected matplotlib plots."""

    def __init__(self, parent):
        super().__init__(parent)

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

    def clear(self):
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self._figures.clear()
        self._canvases.clear()

    def add_plot(self, tab_title, draw_func, *args, figsize=(10, 6)):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=tab_title)

        fig = Figure(figsize=figsize, dpi=100)
        ax = fig.add_subplot(111)
        axes = draw_func(ax, *args) or [ax]
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        _attach_line_tooltips(fig, axes)
        toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="top", fill="x")
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        canvas.draw()

        self._figures.append(fig)
        self._canvases.append(canvas)

    def fit_tabs_to_count(self):
        return
