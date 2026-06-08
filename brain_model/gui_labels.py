"""Etykiety i stałe tekstowe współdzielone przez GUI Tk i Qt.

Moduł nie importuje bibliotek GUI, aby aktywne widoki PySide6 mogły korzystać
z polskich etykiet bez ładowania legacy tkinter.
"""

# ruff: noqa: E501

from __future__ import annotations

import subprocess
from pathlib import Path

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

PARAMETER_LABELS = {
    "T": "czas symulacji [s]",
    "dt": "krok czasowy dt [s]",
    "seed": "ziarno losowości",
    "auto_dt": "automatyczny dobór dt",
    "noise": "szum neuronalny",
    "gw_threshold": "próg globalnej przestrzeni roboczej",
    "gw_gain": "wzmocnienie globalnej przestrzeni roboczej",
    "learning_rate_semantic": "tempo uczenia semantycznego",
    "learning_rate_value": "tempo uczenia wartościowania",
    "decay_semantic": "zanik śladu semantycznego",
    "enable_oscillators": "włącz oscylatory",
    "decision_threshold": "próg decyzji",
    "confidence_gain": "wzmocnienie pewności",
    "w_ee": "samowzmacnianie populacji E",
    "w_ei": "hamowanie E przez I",
    "w_ie": "pobudzanie I przez E",
    "w_ii": "samooddziaływanie populacji I",
    "baseline_e": "bazowy napęd populacji E",
    "baseline_i": "bazowy napęd populacji I",
    "cognitive_drive_gain": "wzmocnienie napędu poznawczego",
    "coupling_gain": "wzmocnienie sprzężenia oscylatorów",
    "oscillator_noise": "szum oscylatorów",
    "phase_drive_gain": "wzmocnienie napędu fazy",
    "scenario": "scenariusz",
    "save_results": "zapisz wyniki",
}

APP_BASE_VERSION = "0.3"


def build_app_version() -> str:
    """Zbuduj wersję aplikacji na podstawie liczby commitów w repozytorium."""
    root_dir = Path(__file__).resolve().parents[1]
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=root_dir,
            check=False,
            capture_output=True,
            text=True,
        )
        commit_count = result.stdout.strip()
        if result.returncode != 0 or not commit_count.isdecimal():
            return f"{APP_BASE_VERSION}.0"
        return f"{APP_BASE_VERSION}.{commit_count}"
    except (FileNotFoundError, subprocess.SubprocessError):
        return f"{APP_BASE_VERSION}.0"


APP_VERSION = build_app_version()
LAST_UPDATED = "2026-05-25"
APP_AUTHOR = "dr inż. Mateusz Pomianek"

RULE_FIELDS = ("semantic_rule", "value_rule", "connectivity_adaptation")
COMMAND_LABELS = {"run": "uruchom", "batch": "seria uruchomień"}
COMMAND_VALUES = {label: command for command, label in COMMAND_LABELS.items()}
