# Struktura programu `neuro_sim`

Ten dokument opisuje aktualną strukturę repozytorium oraz rolę najważniejszych modułów.

## 1. Widok wysokiego poziomu

```text
neuro_sim/
├── main.py                        # uruchomienie szybkiej symulacji/raportów
├── main_gui.py                    # GUI (alias do uruchomienia okna)
├── run_gui.py                     # alternatywny punkt wejścia GUI
├── brain_model/                   # model poznawczy + wizualizacje + IO
├── brain_core/                    # silnik symulacyjny i konfiguracja eksperymentów
├── brain_viewer/                  # narzędzia mapowania regionów i widoki mózgu
├── configs/                       # gotowe konfiguracje YAML
├── docs/                          # dokumentacja i zasoby statyczne (SVG/HTML/PNG)
├── assets/                        # zasoby pomocnicze (np. SVG)
└── scripts/                       # skrypty narzędziowe
```

## 2. `brain_model/` — warstwa modelu poznawczego

Folder zawiera główną logikę modelu procesów poznawczych:

- `model.py` — klasa `CognitiveBrainModel`, przebieg symulacji i agregacja wyników,
- `params.py` — parametry modelu (`BrainParams`),
- `oscillators.py` — parametry i dynamika Wilson-Cowan,
- `modules.py`, `connectivity.py`, `plasticity.py`, `stimuli.py` — komponenty mechaniki modelu,
- `behavior.py`, `report.py`, `plotting.py` — analiza i prezentacja wyników,
- `gui.py` — logika interfejsu desktopowego.

To tutaj jest obecnie „fizyczna” implementacja dynamiki eksperymentu.

## 3. `brain_core/simulation/` — warstwa orkiestracji eksperymentów

Ta warstwa zapewnia niezależny od GUI silnik uruchamiania:

- `config_schema.py` — dataclass konfiguracji i walidacja,
- `config_loader.py` — wczytywanie YAML/JSON,
- `engine.py` — `run_experiment(config, progress_callback=...)`,
- `run.py` — CLI: `python -m brain_core.simulation.run --config ...`.

### 3.1. Nowe komponenty infrastrukturalne

Dodane elementy pod rozbudowę wieloskalową:

- `state.py` — `SimulationState`: centralny, mutowalny obiekt stanu (`regions`, `connections`, `neuromodulators`, `metrics`, `time`, `step`),
- `scheduler.py` — `SimulationScheduler` oraz fazy kroku:
  1. `stimuli`
  2. `neuronal_dynamics`
  3. `couplings`
  4. `physiology`
  5. `logging`
- `scheduler.py` — `CoSimulationHook`: punkt rozszerzeń pod moduły z różnymi krokami czasowymi,
- `integrators.py` — wspólny interfejs integratora + `EulerMaruyamaIntegrator` i `RK4Integrator`,
- `random_sources.py` — `RandomSources`: deterministyczne strumienie RNG per-moduł.

> Uwaga: `scheduler.py` i `multiscale_engine.py` współistnieją — pierwszy definiuje fazowy scheduler kroku, drugi prosty scheduler wieloskalowy (`base_dt` + zadania z własnym `dt`) dla współsymulacji NM↔SNN.

## 4. `brain_viewer/` i zasoby wizualne

- `brain_viewer/mapping.py` i `brain_viewer.md` — mapowania regionów oraz opis warstwy viewer,
- `docs/*.svg`, `docs/*.html`, `docs/*.png` — renderingi i interaktywne widoki przekrojów mózgu,
- `assets/svg/*.svg` — źródła grafiki używane przez viewer/dokumentację.

## 5. Konfiguracje, uruchamianie i przepływ danych

1. Użytkownik wybiera konfigurację (`configs/*.yaml`) lub GUI.
2. `brain_core.simulation.config_loader` wczytuje i waliduje dane.
3. `brain_core.simulation.engine.run_experiment` tworzy `CognitiveBrainModel` i uruchamia `simulate`.
4. Wyniki są zapisywane przez `brain_model.io` (jeśli `save_results=true`) i raportowane w GUI/CLI.

## 6. Rekomendowany kierunek rozwoju

Aby w pełni wykorzystać nowe API symulacyjne:

- przenieść kroki aktualizacji modelu do modułów zgodnych z `SimulationModule`,
- spiąć `SimulationScheduler` w głównej pętli symulacji,
- mapować metody z konfiguracji (`integrator.method`) na klasy integratorów,
- przypisać odseparowane strumienie z `RandomSources` do poszczególnych podsystemów.


## 3.2. Pilotażowy most neural-mass ↔ SNN

W `brain_core/populations/spiking_population.py` dodano startowy adapter `Brian2SpikingPopulationAdapter` oraz jawny kontrakt wymiany sygnałów:

- wejście NM→SNN: `excitatory_drive_hz`, `inhibitory_drive_hz`, `sync_dt`,
- wyjście SNN→NM: `firing_rate_hz`, `mean_membrane_potential_mv`, `sync_dt`.

Zakres pilotażu jest celowo ograniczony do 1–2 obwodów (hipokamp, DLPFC), aby utrzymać minimalny zakres zmian i prostą walidację.
