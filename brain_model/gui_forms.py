"""Formularze i pomocnicze kontrolki GUI modelu poznawczego."""

# ruff: noqa: E501

from __future__ import annotations

import tkinter as tk
from dataclasses import fields
from tkinter import ttk
from typing import Any, Dict, Iterable

PARAMETER_DESCRIPTIONS = {
    "T": "Czas trwania symulacji w sekundach. Typowo 10-120 s; większe wartości pokazują dłuższe trendy, ale wydłużają obliczenia.",
    "seed": "Ziarno generatora losowego. Typowo dowolna liczba całkowita; ta sama wartość daje powtarzalny przebieg szumu i oscylacji.",
    "scenario_details": "Opis, pole co się zmienia oraz przebieg wybranego scenariusza: fazy, zdarzenia i aktywne kanały bodźców.",
    "dt": "Krok czasowy symulacji. Typowo 0.001-0.01; mniejszy krok zwiększa dokładność i koszt, większy może wygładzić lub zdestabilizować dynamikę.",
    "auto_dt": "Automatycznie dobiera krok dt do czasu T, aby utrzymać rozsądną liczbę kroków i stabilność symulacji.",
    "noise": "Skala szumu neuronalnego. Typowo 0.0-0.05; większa wartość zwiększa zmienność aktywacji i może maskować słabe efekty bodźców.",
    "gw_threshold": "Próg zapłonu globalnej przestrzeni roboczej. Typowo 0.4-0.8; niższy ułatwia globalną aktywację, wyższy wymaga silniejszej uwagi lub sieci istotności.",
    "gw_gain": "Stromość funkcji zapłonu globalnej przestrzeni roboczej. Typowo 5-20; większa wartość daje bardziej skokowe przejście między brakiem i obecnością zapłonu.",
    "learning_rate_semantic": "Tempo uczenia semantycznego. Typowo 0.0-0.02; większa wartość szybciej wzmacnia SEM przez HIP i GW.",
    "learning_rate_value": "Tempo uczenia wartościowania. Typowo 0.0-0.08; większa wartość szybciej zmienia VAL po błędzie predykcji nagrody.",
    "decay_semantic": "Zanik śladu semantycznego. Typowo 0.0-0.01; większa wartość szybciej wygasza SEM i ogranicza długotrwałe utrzymanie reprezentacji.",
    "enable_oscillators": "Włącza oscylatory Wilsona-Cowana. Typowo włączone; wyłączenie zeruje sygnały EEG i moc pasmową, ale zostawia dynamikę poznawczą.",
    "decision_threshold": "Próg decyzji behawioralnej. Typowo 0.45-0.8; niższy daje szybsze i częstsze decyzje, wyższy wymaga silniejszego pobudzenia EXEC/VAL/MOT/GW.",
    "confidence_gain": "Wzmocnienie przeliczenia wyniku decyzji na pewność. Typowo 0.5-3.0; większa wartość szybciej nasyca pewność do wartości bliskich 0 lub 1.",
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
    "scenario": "Wybór gotowego scenariusza bodźców i kontekstu zadania. Każdy scenariusz uruchamia inne fazy, zdarzenia i profil sygnałów wejściowych.",
    "save_results": "Po zakończeniu symulacji zapisuje wyniki do katalogu outputs/ w formacie NPZ + JSON (z metadanymi eksperymentu).",
    "plot_activity": "Wykres aktywacji modułów poznawczych w czasie (np. ATT, EXEC, SEM, GW).",
    "plot_simulated_brain_activity": "Mapa cieplna aktywacji modułów mózgu w czasie (symulowana aktywność mózgu).",
    "plot_brain_region_projections": "Cztery rzuty mózgu na bazie szkieletu SVG z aktywacją regionów dla kolejnych kroków czasu.",
    "plot_region_activity_2d": "Wykres 2D (mapa cieplna): aktywacja poszczególnych regionów mózgu w funkcji czasu eksperymentu.",
    "plot_diagnostics": "Wykres zmiennych diagnostycznych i neuromodulacyjnych, m.in. błędu predykcji, zapłonu globalnej przestrzeni roboczej i neuroprzekaźników.",
    "plot_behavior": "Wykres strumienia zachowania: wynik decyzji, pewność oraz markery punktów decyzji.",
    "plot_eeg": "Wykres aproksymowanych sygnałów EEG (E-I) dla wybranych modułów modelu.",
    "plot_band_power": "Wykres chwilowej mocy pasm theta/alpha/beta/gamma wyliczanej z banku oscylatorów.",
    "plot_weight_trajectories": "Wykres trajektorii wybranych adaptowanych wag w macierzy W.",
    "plot_weight_deltas": "Wykres przyrostów ΔW/krok dla adaptowanych wag.",
    "plot_scenario_channels": "Wykres kanałów bodźców scenariusza w funkcji czasu.",
    "plot_scenario_timeline": "Oś czasu scenariusza: fazy i zdarzenia.",
}

APP_VERSION = "0.3.0"
LAST_UPDATED = "2026-05-25"
APP_AUTHOR = "dr inż. Mateusz Pomianek"

RULE_FIELDS = ("semantic_rule", "value_rule", "connectivity_adaptation")
COMMAND_LABELS = {"run": "uruchom", "batch": "seria uruchomień"}
COMMAND_VALUES = {label: command for command, label in COMMAND_LABELS.items()}


class Tooltip:
    """Prosta podpowiedź tekstowa wyświetlana po najechaniu na widżet."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        """Zarejestruj obsługę pokazania i ukrycia podpowiedzi."""
        self.widget: tk.Widget = widget
        self.text: str = text
        self.tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event: tk.Event | None = None) -> None:
        """Pokaż okno podpowiedzi obok widżetu."""
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

    def hide(self, event: tk.Event | None = None) -> None:
        """Ukryj aktywne okno podpowiedzi."""
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ParameterForm(ttk.LabelFrame):
    """Formularz parametrów budowany na podstawie pól dataclass."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        dataclass_type: type[Any],
        defaults: Any,
        include_fields: Iterable[str] | None = None,
    ) -> None:
        """Utwórz kontrolki edycji dla widocznych pól dataclass."""
        super().__init__(parent, text=title, padding=10)
        self.dataclass_type: type[Any] = dataclass_type
        self.defaults: Any = defaults
        self.vars: Dict[str, tk.Variable] = {}
        self.include_fields: set[str] | None = set(include_fields) if include_fields is not None else None

        form_fields = [
            f
            for f in fields(dataclass_type)
            if self.include_fields is None or f.name in self.include_fields
        ]
        for row, field in enumerate(form_fields):
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

    def values(self) -> Any:
        """Zwróć instancję dataclass z wartościami odczytanymi z formularza."""
        kwargs = {}
        for field in fields(self.dataclass_type):
            name = field.name
            if self.include_fields is not None and name not in self.include_fields:
                kwargs[name] = getattr(self.defaults, name)
                continue
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

    def reset(self) -> None:
        """Przywróć w formularzu wartości domyślne."""
        for field in fields(self.dataclass_type):
            if self.include_fields is not None and field.name not in self.include_fields:
                continue
            name = field.name
            value = getattr(self.defaults, name)
            self.vars[name].set(value if isinstance(value, bool) else str(value))
