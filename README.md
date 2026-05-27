# Cognitive Brain Model

Mezoskopowy model dynamiki procesów poznawczych w Pythonie.

Model nie symuluje pojedynczych neuronów. Reprezentuje aktywność modułów poznawczych oraz sprzężone oscylatory Wilsona-Cowana dla pasm EEG.

## Moduły poznawcze

- przetwarzanie wzrokowe i słuchowe,
- interocepcja,
- salience network,
- uwaga,
- pamięć robocza,
- pamięć semantyczna i epizodyczna,
- hipokampalne wiązanie epizodów,
- wartościowanie,
- planowanie działania,
- default mode network,
- global workspace.

## Oscylatory Wilsona-Cowana

Każdy moduł poznawczy ma osobny oscylator Wilsona-Cowana z populacją pobudzającą `E` i hamującą `I`.
Sygnał EEG jest aproksymowany jako:

```text
EEG_module(t) = E_module(t) - I_module(t)
```

Domyślne przypisanie pasm:

- `theta`: HIP, EPIS, PHON, VSWM,
- `alpha`: VIS, AUD, INT, DMN,
- `beta`: EXEC, ATT, SAL, MOT, LANG,
- `gamma`: SEM, VAL, GW.

Interpretacja:

- theta: hipokamp, bufor epizodyczny i pamięć robocza,
- alpha: hamowanie i bramkowanie sensoryczne,
- beta: kontrola wykonawcza i utrzymanie nastawienia zadaniowego,
- gamma: lokalne wiązanie cech i reprezentacji.

## Instalacja

```bash
pip install .

## Uruchomienie

```bash
python main.py
```

## Struktura

```text
neuro_sim/
├── main.py
├── brain_model/
│   ├── __init__.py
│   ├── params.py
│   ├── activations.py
│   ├── modules.py
│   ├── connectivity.py
│   ├── stimuli.py
│   ├── oscillators.py
│   ├── model.py
│   └── plotting.py
└── README.md
```


## Konfiguracje i silnik eksperymentów (brain_core)

Od tego etapu uruchamianie eksperymentów jest oparte o wspólny silnik `brain_core.simulation`, niezależny od GUI.

Najważniejsze elementy:

- `brain_core/simulation/engine.py` – API `run_experiment(config, progress_callback=...)`,
- `brain_core/simulation/config_schema.py` – schema + walidacja konfiguracji,
- `brain_core/simulation/config_loader.py` – loader YAML/JSON,
- `brain_core/simulation/run.py` – CLI (`python -m brain_core.simulation.run --config ...`),
- `configs/default.yaml` i `configs/cognitive_demo.yaml` – przykładowe konfiguracje.

Przykład uruchomienia z pliku konfiguracyjnego:

```bash
python -m brain_core.simulation.run --config configs/default.yaml
```

Alternatywnie po instalacji pakietu:

```bash
neuro-sim-run --config configs/cognitive_demo.yaml
```

### GUI i uruchamianie asynchroniczne

GUI uruchamia symulację asynchronicznie (w tle), dzięki czemu interfejs nie blokuje się podczas długich eksperymentów i na bieżąco aktualizuje pasek postępu.

Punkty wejścia GUI są zgodne i delegują do jednej implementacji:

- `main_gui.py`
- `run_gui.py`
- `brain_model.gui:run_gui`

## Wyniki symulacji

`model.simulate()` zwraca:

```python
time, activity, diagnostics, oscillations = model.simulate(T=45.0)
```

- `activity`: aktywacje modułów poznawczych,
- `diagnostics`: błąd predykcji, neuromodulacja, global workspace,
- `oscillations["eeg"]`: sygnały E-I dla modułów,
- `oscillations["band_power"]`: chwilowa moc theta/alpha/beta/gamma.

## GUI do konfiguracji parametrów

Dodano prosty moduł GUI oparty na `tkinter`. Pozwala zmienić parametry przed rozpoczęciem symulacji:

- czas symulacji `T`,
- `seed`,
- wszystkie pola `BrainParams`,
- wszystkie pola `WilsonCowanParams`,
- wybór wykresów do wygenerowania.

Uruchomienie GUI:

```bash
python main_gui.py
```

GUI nie wymaga dodatkowych bibliotek poza standardowym `tkinter`, `numpy` i `matplotlib`. W niektórych dystrybucjach Linuksa `tkinter` trzeba doinstalować oddzielnie, np. `sudo apt install python3-tk`.

### Komendy GUI do eksperymentów badawczych

W module GUI dostępne są teraz dwa tryby uruchamiania:

- `run` – pojedyncza symulacja dla wybranego `seed` i scenariusza,
- `batch` – seria symulacji dla wielu seedów/scenariuszy z uśrednianiem metryk i perturbacjami `sensitivity`.

Przykładowy workflow (w GUI, zakładka **Konfiguracja**):

1. Ustaw `komenda=run`, `T=60`, `seed=7`, `scenariusz=reward-learning` aby uruchomić przebieg referencyjny.
2. Przełącz `komenda=batch`.
3. Ustaw:
   - `batch seeds`: `7,11,19,23`
   - `batch scenariusze`: `reward-learning,threat-reversal`
   - `sensitivity parametry`: `noise,gw_threshold`
   - `sensitivity delta`: `0.1` (czyli ±10% dla wskazanych parametrów)
4. Uruchom symulację i obserwuj pasek postępu oraz podsumowanie metryk po zakończeniu.

Podsumowanie batch raportuje średnie wartości m.in.:

- `prediction_error`,
- `gw_ignition`,
- `confidence`,
- liczby zdarzeń decyzyjnych (`decision_events`).

Najważniejsze pliki:

```text
brain_model/gui.py   # okno konfiguracji parametrów
main_gui.py          # punkt wejścia GUI
```

Parametry oscylatorów Wilsona-Cowana można teraz przekazać także programistycznie:

```python
from brain_model.model import CognitiveBrainModel
from brain_model.params import BrainParams
from brain_model.oscillators import WilsonCowanParams

model = CognitiveBrainModel(
    params=BrainParams(dt=0.005, noise=0.01),
    oscillator_params=WilsonCowanParams(cognitive_drive_gain=3.2),
    seed=7,
)

time, activity, diagnostics, oscillations = model.simulate(T=45.0)
```


## Dokumentacja struktury programu

Szczegółowy opis aktualnej architektury repozytorium znajduje się w:

- `docs/program_structure.md`

Dokument zawiera również opis nowej infrastruktury symulacyjnej (`SimulationState`, `SimulationScheduler`, integratory i `RandomSources`) oraz wskazuje, które elementy są już gotowe, a które wymagają pełnej integracji z pętlą symulacji.


## Pilotaż NM ↔ SNN (Brian2 backend startowy)

Dodano minimalny most współsymulacji neural-mass ↔ spiking z jednym backendem startowym: `brian2`.

Najważniejsze elementy:

- `brain_core/populations/spiking_population.py`
  - `NeuralMassToSNNInput(excitatory_drive_hz, inhibitory_drive_hz, sync_dt)`
  - `SNNToNeuralMassOutput(firing_rate_hz, mean_membrane_potential_mv, sync_dt)`
  - `Brian2SpikingPopulationAdapter(region_names, dt=...)`
- `brain_core/simulation/multiscale_engine.py`
  - `TimeScaleTask(name, module, dt)`
  - `MultiScaleEngine(base_dt, tasks)`

Kontrakt synchronizacji:

- `sync_dt` określa krok wymiany NM↔SNN,
- adapter i scheduler walidują dodatnie `dt`,
- w pilotażu zakres ograniczono do 1–2 obwodów (hipokamp, DLPFC).

Krótki przykład użycia:

```python
import numpy as np
from brain_core.populations import Brian2SpikingPopulationAdapter, NeuralMassToSNNInput

adapter = Brian2SpikingPopulationAdapter(region_names=["hippocampus", "dlpfc"], dt=0.001)
signal = NeuralMassToSNNInput(
    excitatory_drive_hz=np.array([20.0, 16.0]),
    inhibitory_drive_hz=np.array([6.0, 5.0]),
    sync_dt=0.005,
)
out = adapter.step(signal)
```
