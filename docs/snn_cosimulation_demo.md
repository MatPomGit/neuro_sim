# Współsymulacja neural-mass + lokalny obwód SNN

Ten dokument opisuje demonstracyjny moduł współsymulacji neural-mass z lokalnym
obwodem SNN używany przez konfigurację `configs/snn_hippocampus_demo.yaml`.
Celem modułu jest pokazanie jawnego kontraktu wymiany sygnałów, walidowalnego
mapowania regionów oraz raportu porównującego przebieg bazowy bez SNN,
wariant report-only SNN i wariant closed-loop SNN.

## Zakres i odpowiedzialności

Współsymulacja jest celowo ograniczona do małego, testowalnego przypadku
pilotażowego. Nie zastępuje pełnej sieci kolców całego mózgu.

Główne elementy:

- `brain_core/simulation/signal_adapter.py` — definiuje `SNNPopulationMapping`
  oraz `CouplingSignalAdapter`, czyli jawne mapowanie nazw regionów i konwersję
  sygnałów między neural-mass oraz SNN.
- `brain_core/populations/spiking_population.py` — zawiera kontrakty
  `NeuralMassToSNNInput`, `SNNToNeuralMassOutput` oraz startowy adapter
  `Brian2SpikingPopulationAdapter` z deterministycznym backendem zastępczym.
- `brain_core/simulation/config_schema.py` — waliduje sekcję `snn`, w tym
  `sync_dt`, jednostki i spójność mapowania regionów.
- `brain_core/simulation/engine.py` — uruchamia demonstracyjne porównanie
  baseline, report-only SNN i closed-loop SNN oraz dołącza wynik jako
  `snn_comparison`. Pole `requested_mode` zapisuje tryb żądany w konfiguracji,
  a `computed_modes` wymienia warianty faktycznie policzone w raporcie.
- `brain_core/analysis/reports.py` — eksportuje `snn_comparison` do raportu
  Markdown oraz CSV.

## Konfiguracja demonstracyjna

Plik `configs/snn_hippocampus_demo.yaml` uruchamia jedno zadanie poznawcze
`n_back` na scenariuszu bodźcowym `task-switching` i dodaje lokalny obwód SNN
mapowany na region `HIP`.

Najważniejsze pola sekcji `snn`:

```yaml
snn:
  enabled: true
  sync_dt: 0.010
  input_rate_unit: Hz
  output_activity_unit: fraction
  neural_mass_regions:
    - VIS
    - AUD
    - INT
    - SAL
    - ATT
    - PHON
    - VSWM
    - EXEC
    - EPIS
    - SEM
    - HIP
    - VAL
    - MOT
    - DMN
    - LANG
    - GW
  circuits:
    - region: HIP
      backend: brian2
      neurons: 800
      coupling_gain: 0.20
```

Znaczenie pól:

- `enabled` włącza etap demonstracyjnego porównania SNN.
- `sync_dt` określa krok synchronizacji neural-mass ↔ SNN w sekundach. Musi być
  dodatnią całkowitą wielokrotnością `timestep`.
- `input_rate_unit` musi mieć wartość `Hz`, ponieważ wejście do SNN jest
  interpretowane jako częstość pobudzenia.
- `output_activity_unit` musi mieć wartość `fraction`, ponieważ wyjście SNN jest
  normalizowane do aktywności regionalnej z zakresu `[0, 1]`.
- `neural_mass_regions` zapisuje kolejność regionów neural-mass używaną przez
  `SNNPopulationMapping`.
- `circuits[].region` musi występować w `neural_mass_regions`; w demo jest to
  region `HIP`.
- `coupling_gain` określa udział lokalnej aktywności SNN przy obliczaniu
  porównawczego przebiegu `report_only_snn`; w trybie `closed_loop` ten sam
  kontrakt służy do ograniczonego amplitudowo wejścia zwrotnego.

## Kontrakt sygnałów i jednostek

Adapter wymiany sygnałów stosuje następujący kontrakt:

1. Neural-mass przekazuje do SNN wektory:
   - `excitatory_drive_hz`,
   - `inhibitory_drive_hz`,
   - `sync_dt`.
2. Lokalny adapter SNN zwraca:
   - `firing_rate_hz`,
   - `mean_membrane_potential_mv`,
   - `sync_dt`.
3. `CouplingSignalAdapter` konwertuje `firing_rate_hz` do znormalizowanej
   aktywności regionalnej `fraction`, przycinanej do zakresu `[0, 1]`.

Mapowanie jest wyłącznie nazwane: region obwodu SNN nie jest dopasowywany po
indeksie z konfiguracji, dopóki `SNNPopulationMapping` nie potwierdzi, że nazwa
regionu istnieje w wektorze regionów neural-mass.

## Uruchomienie

Z katalogu repozytorium:

```bash
PYTHONPATH=. python -m brain_core.simulation.run --config configs/snn_hippocampus_demo.yaml
```

Przy `output.save_results: true` wyniki zostaną zapisane w katalogu `outputs/`
z etykietą `snn-hippocampus-demo`. Raport analizy zapisuje sekcję
`Porównanie przebiegu bez SNN i z lokalnym obwodem SNN`.

## Raport `snn_comparison`

Sekcja `snn_comparison` zawiera:

- status lokalnego obwodu SNN,
- listę mapowanych regionów SNN,
- `sync_dt_s`,
- jednostki wejścia i wyjścia,
- backend adaptera,
- `requested_mode`, czyli tryb żądany w konfiguracji,
- `computed_modes`, czyli warianty faktycznie policzone w raporcie,
- `comparison_note_pl`, czyli polską uwagę, że `closed_loop_snn` jest dodatkowym
  wariantem porównawczym, a nie nadpisaniem żądanego trybu,
- osobne metryki dla `baseline`, `report_only_snn` i `closed_loop_snn`, w tym
  długość sygnału oraz amplitudę feedbacku dla wariantu closed-loop,
- metryki różnic dla każdego mapowanego regionu:
  - `mean_without_snn`,
  - `mean_snn_local_activity`,
  - `mean_with_snn`,
  - `mean_abs_difference`,
  - `max_abs_difference`.

Wariant `report_only_snn` nie modyfikuje surowego przebiegu neural-mass
zapisywanego przez symulację. Wariant `closed_loop_snn` jest liczony jako
jawny dodatkowy wariant porównawczy także wtedy, gdy `snn.mode` ma wartość
`report_only`; dlatego raport rozdziela tryb żądany (`requested_mode`) od listy
wariantów faktycznie policzonych (`computed_modes`) i dodaje `comparison_note_pl`
z informacją, że `closed_loop_snn` jest dodatkowym wariantem porównawczym.

## Walidacja i testy

Spójność konfiguracji jest sprawdzana statycznie przez walidator konfiguracji:

- `sync_dt` musi być dodatnią wielokrotnością `timestep`,
- jednostki muszą odpowiadać kontraktowi `Hz` oraz `fraction`,
- regiony w `snn.circuits` muszą być niepuste i unikalne,
- region obwodu SNN musi istnieć w `snn.neural_mass_regions`.

Testy obejmujące ten moduł:

```bash
PYTHONPATH=. pytest tests/test_config_schema.py tests/test_spiking_population_adapter.py
```

Najważniejsze przypadki testowe sprawdzają konfigurację demo, indeks mapowania
`HIP`, jednostki, `sync_dt`, obecność sekcji raportu `snn_comparison` oraz
rozdzielenie trybu żądanego od wariantów faktycznie policzonych.

## Ograniczenia pilotażu

- Adapter `Brian2SpikingPopulationAdapter` nadal używa deterministycznego
  backendu zastępczego; pełna sieć Brian2/NEST jest osobnym krokiem rozwoju.
- Demo obejmuje jeden lokalny obwód hipokampa, aby zachować prostą walidację i
  czytelny raport.
- Closed-loop jest MVP demonstracyjnym dla HIP; przed użyciem badawczym wymaga
  dalszej walidacji stabilności, porównania kosztu `report_only` vs
  `closed_loop` oraz pełniejszego backendu biologicznego.
