# Struktura programu `neuro_sim`

Ten dokument opisuje aktualny układ repozytorium na dzień 2026-06-02. Jest opisem stanu istniejącego, a nie docelowego szkicu architektury; plan najbliższych prac jest utrzymywany w `ROADMAP.md`.

## 1. Widok wysokiego poziomu

```text
neuro_sim/
├── main.py                         # szybkie uruchomienie symulacji poznawczej
├── main_gui.py                     # punkt wejścia GUI desktopowego
├── brain_model.py                  # starszy moduł kompatybilności modelu
├── brain_viewer.html               # samodzielny widok viewer
├── brain_viewer_compact.html       # kompaktowy wariant viewer
├── brain_sagittal_inline_regions.html
├── brain_model/                    # model poznawczy, GUI, raporty, IO
├── brain_core/                     # warstwa symulacji, anatomii, eksperymentów i analiz
├── brain_viewer/                   # mapowanie regionów i opis viewer
├── analysis/                       # zgodność wsteczna dla raportów
├── configs/                        # gotowe konfiguracje YAML/JSON
├── data/                           # atlasy, konektomy i dane walidacyjne
├── docs/                           # dokumentacja, ADR, grafiki i widoki statyczne
├── assets/                         # źródłowe zasoby SVG
├── scripts/                        # skrypty narzędziowe
├── tests/                          # testy jednostkowe i integracyjne
└── outputs/                        # przykładowe zapisane wyniki uruchomień
```

## 2. Punkty wejścia i uruchamianie

- `main.py` — uruchamia podstawową symulację i generowanie wyników z warstwy `brain_model`.
- `main_gui.py` — uruchamia GUI desktopowe delegujące do `brain_model.gui_runner` oraz modułów GUI.
- `python -m brain_core.simulation.run --config configs/default.yaml` — uruchamia eksperyment z pliku konfiguracyjnego przez niezależną od GUI warstwę `brain_core`.
- Skrypty instalowane przez `pyproject.toml`: `neuro-sim`, `neuro-sim-gui`, `neuro-sim-run`.


## 2A. Status funkcji w aktualnej strukturze

Statusy używane w tym dokumencie: `done`, `partial`, `planned`. Poniższe
pozycje opisują tylko stan dokumentowany w repozytorium, bez dodawania nowych
modułów.

| Funkcja | Status | MVP istnieje | Pozostały zakres strukturalny |
| --- | --- | --- | --- |
| `roving_oddball` | `partial` | `brain_core/experiments/protocols.py`, `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml`, `configs/roving_oddball_lesion_hippocampus.yaml`. | Artefakty MVP już istnieją; utrzymać rozwój w tych ścieżkach i istniejących raportach, bez nowej warstwy architektonicznej. |
| Clinical profiles | `partial` | `configs/clinical_profiles/*.yaml`, `brain_core/simulation/config_schema.py`, `brain_core/experiments/lesions.py`, `brain_model/scenarios/`. | Rozszerzać metadane i interpretacje w istniejącym katalogu profili oraz raportach porównawczych. |
| Timeline | `partial` | `brain_core/simulation/events.py`, `brain_core/simulation/engine.py`, `brain_core/analysis/reports.py`. | Rozbudować raport trial-by-trial w istniejących modułach raportowania i eksportu. |
| Benchmark metadata | `partial` | `data/validation/benchmark_metadata.json` i `brain_core/analysis/benchmark_loader.py`. | Uzupełniać kryteria zgodności i źródła w danych walidacyjnych oraz loaderze benchmarków. |
| SNN demo | `partial` | `configs/snn_hippocampus_demo.yaml`, `docs/snn_cosimulation_demo.md`, `brain_core/simulation/signal_adapter.py`, `brain_core/simulation/multiscale_engine.py`. | Pełniejsze sprzężenie i backendy utrzymywać w warstwie `brain_core/simulation` oraz `brain_core/populations`. |

## 3. `brain_model/` — model poznawczy, GUI i prezentacja wyników

```text
brain_model/
├── model.py, params.py, modules.py, activations.py
├── connectivity.py, oscillators.py, plasticity.py, stimuli.py
├── behavior.py, calibration.py, validation.py
├── report.py, report_export.py, plotting.py, io.py
├── gui.py, gui_app.py, gui_config.py, gui_forms.py
├── gui_layout.py, gui_runner.py, gui_state.py
└── scenarios/
    ├── library.py
    └── types.py
```

Najważniejsze odpowiedzialności:

- `model.py` i `params.py` przechowują główny model poznawczy oraz parametry uruchomienia.
- `calibration.py` udostępnia pomocniczy sweep parametrów; pełny przebieg, kontrakt danych i artefakty opisuje `docs/calibration_pipeline.md`.
- `oscillators.py`, `connectivity.py`, `plasticity.py` i `stimuli.py` obsługują dynamikę, bodźce i mechanikę modelu.
- `scenarios/` zawiera katalog scenariuszy oraz typy scenariuszy używane przez GUI i testy.
- `gui_*` rozdzielają stan, układ, formularze i uruchamianie GUI; GUI nie powinno przejmować logiki domenowej.
- `report.py`, `report_export.py`, `plotting.py` i `io.py` odpowiadają za prezentację oraz zapis wyników.

## 4. `brain_core/` — warstwa symulacji, domeny biologicznej i analiz

### 4.1. Symulacja i konfiguracja

```text
brain_core/simulation/
├── config_schema.py
├── config_loader.py
├── engine.py
├── run.py
├── state.py
├── scheduler.py
├── multiscale_engine.py
├── integrators.py
├── random_sources.py
└── signal_adapter.py
```

- `config_schema.py` definiuje `ExperimentConfig` i walidację sekcji `model`, `integrator`, `task`, `pathology`, `output`, `snn` oraz `analysis`.
- `config_loader.py` wczytuje YAML/JSON, a `run.py` udostępnia CLI eksperymentów.
- `engine.py` spina konfigurację z aktualnym modelem poznawczym i dołącza sekcję `snn_comparison` dla demonstracyjnego przebiegu neural-mass + lokalny obwód SNN.
- `signal_adapter.py` definiuje `SNNPopulationMapping` oraz `CouplingSignalAdapter`, czyli jawny kontrakt mapowania regionów i konwersji jednostek między neural-mass i SNN.
- `state.py`, `scheduler.py`, `multiscale_engine.py`, `integrators.py` i `random_sources.py` są fundamentem dalszej integracji wieloskalowej i deterministycznych uruchomień.

### 4.2. Anatomia, konektom i sieci

```text
brain_core/anatomy/
├── atlases.py
├── connectome.py
└── regions.py

brain_core/networks/
├── delays.py
└── structural_network.py
```

Ta część obsługuje atlas regionów, strukturalny konektom, macierze wag, długości włókien i opóźnienia przewodzenia. Dane wejściowe znajdują się w `data/atlases/` oraz `data/connectomes/`.

### 4.3. Eksperymenty, uszkodzenia i farmakologia

```text
brain_core/experiments/
├── protocols.py
├── lesions.py
└── pharmacology.py
```

- `protocols.py` jest punktem startowym dla biblioteki zadań poznawczych i generatorów sekwencji.
- `lesions.py` zawiera mechanizmy uszkodzeń ogniskowych/sieciowych.
- `pharmacology.py` integruje profile modulacji farmakologicznej z warstwą synaps.

### 4.4. Populacje, synapsy i fizjologia

```text
brain_core/populations/
├── wilson_cowan.py
└── spiking_population.py

brain_core/synapses/
├── acetylcholine.py, adrenaline.py, cortisol.py, dopamine.py
├── gaba_glutamate.py, noradrenaline.py, serotonin.py
├── plasticity.py
└── state.py

brain_core/physiology/
├── bold_hrf.py
├── eeg_forward_model.py
└── neurovascular_coupling.py
```

- `wilson_cowan.py` zapewnia populacyjny model E/I.
- `spiking_population.py` zawiera pilotażowy kontrakt wymiany neural-mass ↔ SNN oraz startowy adapter lokalnej populacji SNN.
- `synapses/` grupuje neuromodulatory i stan synaptyczny.
- `physiology/` dostarcza aproksymacje EEG/BOLD i sprzężenia neuro-naczyniowego.
- Szczegółowe kontrakty danych między `anatomy`, `networks`, `populations`, `synapses` i `physiology` są utrzymywane w `docs/data_contracts.md`.

### 4.5. Analiza i raporty

```text
brain_core/analysis/
├── benchmark_loader.py
├── connectivity.py
├── information_flow.py
├── phase_locking.py
├── reports.py
├── signal_metrics.py
└── spectral.py
```

Warstwa analizy wylicza metryki spektralne, fazowe, łącznościowe i przepływu informacji. `signal_metrics.py` pełni rolę fasady kompatybilności, a `reports.py` agreguje metryki do raportów końcowych.

**MVP istnieje — timeline:** oś zdarzeń jest budowana w `brain_core/simulation/events.py`, dołączana przez `brain_core/simulation/engine.py` i konsumowana przez raporty.

**Pozostały zakres — timeline:** pełny raport trial-by-trial, eksport HTML/PDF i linkowanie zdarzeń z wykresami powinny pozostać w istniejących modułach analizy oraz `brain_model/report_export.py`.

## 5. Dane, konfiguracje i artefakty statyczne

```text
configs/
├── default.yaml
├── cognitive_demo.yaml
├── go_nogo.yaml
├── n_back.yaml
├── stroop.yaml
├── roving_oddball_healthy.yaml
├── roving_oddball_disorder_gaba.yaml
├── roving_oddball_lesion_hippocampus.yaml
├── clinical_profiles/
│   ├── healthy_v1.yaml
│   ├── dopamine_deficit.yaml
│   ├── gaba_dysregulation.yaml
│   ├── serotonin_imbalance.yaml
│   ├── hippocampal_lesion.yaml
│   └── dlpfc_weakening.yaml
├── multi_region_delay_demo.yaml
├── multi_region_delay_extended.yaml
├── snn_hippocampus_demo.yaml
└── brain_model_config_2026-05-28.json

data/
├── atlases/default_regions.csv
├── connectomes/weights.csv
├── connectomes/fiber_lengths.csv
└── validation/
    ├── benchmark_metadata.json
    ├── behavior_target.csv
    ├── eeg_target.csv
    └── fmri_target.csv
```

Konfiguracje `configs/*.yaml` są podstawą uruchomień przez `brain_core.simulation.run`.

**MVP istnieje — `roving_oddball`:** protokół zadania jest utrzymywany w `brain_core/experiments/protocols.py`, a trzy konfiguracje scenariuszy znajdują się w `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml` i `configs/roving_oddball_lesion_hippocampus.yaml`.

**MVP istnieje — clinical profiles:** katalog `configs/clinical_profiles/` zawiera profile healthy, disorder i lesion używane przez schemat konfiguracji, silnik i scenariusze porównawcze.

**MVP istnieje — benchmark metadata:** `data/validation/benchmark_metadata.json` opisuje metadane benchmarków EEG, fMRI i zachowania, a dane `data/validation/*_target.csv` są używane przez testy oraz moduły walidacji sygnałów.

**MVP istnieje — SNN demo:** `snn_hippocampus_demo.yaml` dokumentuje minimalny przypadek neural-mass + lokalny obwód SNN; pełny opis znajduje się w `docs/snn_cosimulation_demo.md`. Dane `data/*` są używane przez testy oraz moduły atlasu, konektomu i walidacji sygnałów.

## 6. Dokumentacja i zasoby viewer

```text
docs/
├── architecture_decision_records.md
├── adr/
├── developer_quality_checks.md
├── docstring_typing_standard.md
├── english_polish_glossary.md
├── gui_defaults.json
├── index.html
├── program_structure.md
├── snn_cosimulation_demo.md
└── grafiki SVG/PNG/HTML przekrojów mózgu

brain_viewer/
├── brain_viewer.md
└── mapping.py

assets/svg/
└── brain_*_inline_regions.svg
```

- ADR dla zmian strukturalnych są utrzymywane w `docs/adr/` zgodnie z `docs/architecture_decision_records.md`.
- `docs/english_polish_glossary.md` jest źródłem polskich odpowiedników terminów technicznych w warstwie prezentacji.
- Grafiki w `docs/` i `assets/svg/` wspierają widoki mózgu oraz dokumentację edukacyjną.

## 7. Testy i jakość

```text
tests/
├── test_atlas_connectome.py
├── test_gui_layout_static.py
├── test_gui_state.py
├── test_lesions.py
├── test_multiscale_engine.py
├── test_neuromodulation.py
├── test_observation_and_analysis.py
├── test_plasticity_protocols.py
├── test_signal_metrics_modules.py
├── test_spiking_population_adapter.py
├── test_task_protocols_and_engine.py
├── test_task_stimulus_player.py
└── test_wilson_cowan_network.py
```

Testy obejmują obecnie m.in. konfigurację zadań, konektom, lesion, neuromodulację, metryki sygnałowe, adapter SNN i GUI. Bieżące wymagania jakościowe dla docstringów i adnotacji typów są opisane w `docs/docstring_typing_standard.md` oraz `docs/developer_quality_checks.md`, a przyszłe prace jakościowe pozostają śledzone w `ROADMAP.md`.

## 8. Najbliższe konsekwencje dla struktury repozytorium

Najbliższe prace nie wymagają nowej warstwy architektonicznej. Artefakty MVP `roving_oddball` już istnieją i powinny być utrzymywane w aktualnych lokalizacjach:

- `brain_core/experiments/protocols.py` — definicja protokołu i generator sekwencji zadania,
- `configs/roving_oddball_healthy.yaml` — konfiguracja profilu healthy,
- `configs/roving_oddball_disorder_gaba.yaml` — konfiguracja profilu disorder/GABA,
- `configs/roving_oddball_lesion_hippocampus.yaml` — konfiguracja profilu lesion/hippocampus.

Oczekiwane zmiany strukturalne powinny pozostać minimalne:

1. rozwijać istniejące artefakty MVP `roving_oddball` tylko w powyższych ścieżkach lub w już istniejących modułach raportowania,
2. rozbudować raporty w istniejących modułach `brain_core/analysis/reports.py` i `brain_model/report_export.py`,
3. utrzymać scenariusze clinical/lesion w `brain_model/scenarios/` oraz `brain_core/experiments/lesions.py`,
4. aktualizować ADR tylko wtedy, gdy zmieni się granica odpowiedzialności modułów lub strategia konfiguracji/I/O.

Następne kroki mają charakter dokumentacji użytkowej i doprecyzowania istniejących artefaktów MVP, a nie nowych warstw architektonicznych:

1. przygotować przewodnik dydaktyczny „Roving Oddball — od bodźca do interpretacji”,
2. dodać przykładowe uruchomienie scenariuszy healthy/disorder/lesion z istniejących konfiguracji,
3. opisać interpretację raportu, w tym `surprise_index`, `habituation_level` i `readaptation_latency`,
4. uzupełnić profile kliniczne o interpretacje dydaktyczne oraz progi różnic w istniejących konfiguracjach i raportach,
5. dopisać kryteria zgodności benchmarków w `data/validation/benchmark_metadata.json`,
6. rozwijać demo SNN bez przenoszenia kontraktu poza `brain_core/simulation` i `brain_core/populations`.
