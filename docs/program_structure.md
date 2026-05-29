# Struktura programu `neuro_sim`

Ten dokument opisuje aktualny układ repozytorium na dzień 2026-05-29. Jest opisem stanu istniejącego, a nie docelowego szkicu architektury; plan najbliższych prac jest utrzymywany w `BACKLOG.md`.

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
- `engine.py` spina konfigurację z aktualnym modelem poznawczym.
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
- `spiking_population.py` zawiera pilotażowy kontrakt wymiany neural-mass ↔ SNN.
- `synapses/` grupuje neuromodulatory i stan synaptyczny.
- `physiology/` dostarcza aproksymacje EEG/BOLD i sprzężenia neuro-naczyniowego.

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

## 5. Dane, konfiguracje i artefakty statyczne

```text
configs/
├── default.yaml
├── cognitive_demo.yaml
├── go_nogo.yaml
├── n_back.yaml
├── stroop.yaml
├── multi_region_delay_demo.yaml
├── multi_region_delay_extended.yaml
└── brain_model_config_2026-05-28.json

data/
├── atlases/default_regions.csv
├── connectomes/weights.csv
├── connectomes/fiber_lengths.csv
└── validation/
    ├── behavior_target.csv
    ├── eeg_target.csv
    └── fmri_target.csv
```

Konfiguracje `configs/*.yaml` są podstawą uruchomień przez `brain_core.simulation.run`. Dane `data/*` są używane przez testy oraz moduły atlasu, konektomu i walidacji sygnałów.

## 6. Dokumentacja i zasoby viewer

```text
docs/
├── architecture_decision_records.md
├── adr/
├── developer_quality_checks.md
├── docstring_typing_*.md
├── english_polish_glossary.md
├── gui_defaults.json
├── index.html
├── program_structure.md
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

Testy obejmują obecnie m.in. konfigurację zadań, konektom, lesion, neuromodulację, metryki sygnałowe, adapter SNN i GUI. Najbliższy zakres rozwoju jakości jest opisany w `BACKLOG.md` oraz dokumentach `docs/typing_docstring_audit.md`, `docs/typing_docstring_progress.md` i `docs/docstring_typing_rollout_plan.md`.

## 8. Najbliższe konsekwencje dla struktury repozytorium

Najbliższe prace nie wymagają nowej warstwy architektonicznej. Oczekiwane zmiany strukturalne powinny pozostać minimalne:

1. dodać dedykowane artefakty `roving_oddball` w istniejącej warstwie `brain_core/experiments/` i `configs/`,
2. rozbudować raporty w istniejących modułach `brain_core/analysis/reports.py` i `brain_model/report_export.py`,
3. utrzymać scenariusze clinical/lesion w `brain_model/scenarios/` oraz `brain_core/experiments/lesions.py`,
4. aktualizować ADR tylko wtedy, gdy zmieni się granica odpowiedzialności modułów lub strategia konfiguracji/I/O.
