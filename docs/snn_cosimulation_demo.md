# Współsymulacja neural-mass + lokalny obwód SNN

Ten dokument opisuje demonstracyjny moduł współsymulacji neural-mass z lokalnym
obwodem SNN używany przez konfigurację `configs/snn_hippocampus_demo.yaml`.
Celem modułu jest pokazanie jawnego kontraktu wymiany sygnałów, walidowalnego
mapowania regionu `HIP` oraz raportu porównującego przebieg bazowy bez SNN,
wariant report-only SNN i wariant closed-loop SNN. Raport traktuje SNN jako
deterministyczne porównanie demonstracyjne, a nie jako pełny model biologiczny
hipokampa.

## Zakres i odpowiedzialności

Współsymulacja jest celowo ograniczona do jednego małego, testowalnego
przypadku pilotażowego: lokalnego obwodu demonstracyjnego hipokampa `HIP`. Nie
zastępuje pełnej sieci kolców całego mózgu ani pełnego modelu biologicznego
hipokampa.

Główne elementy:

- `brain_core/simulation/signal_adapter.py` — definiuje `SNNPopulationMapping`
  oraz `CouplingSignalAdapter`, czyli jawne mapowanie nazw regionów i konwersję
  sygnałów między neural-mass oraz SNN.
- `brain_core/populations/spiking_population.py` — zawiera kontrakty
  `NeuralMassToSNNInput`, `SNNToNeuralMassOutput` oraz startowy adapter
  `Brian2SpikingPopulationAdapter` dla pojedynczego obwodu `HIP` z
  deterministycznym backendem zastępczym.
- `brain_core/simulation/config_schema.py` — waliduje sekcję `snn`, w tym
  `sync_dt`, jednostki i spójność mapowania regionów.
- `brain_core/simulation/engine.py` — uruchamia demonstracyjne porównanie
  baseline, report-only SNN i closed-loop SNN oraz dołącza wynik jako
  `snn_comparison`. Pole `requested_mode` zapisuje tryb żądany w konfiguracji,
  a `computed_modes` wymienia warianty faktycznie policzone w raporcie.
- `brain_core/analysis/reports.py` — eksportuje `snn_comparison` do raportu
  Markdown oraz CSV.

## Co oznacza „deterministyczny backend zastępczy `brian2`”

Określenie „deterministyczny backend zastępczy `brian2`” jest nazwą
kontraktu pilotażowego, a nie deklaracją pełnej symulacji biologicznej Brian2.
W praktyce oznacza to, że:

- konfiguracja i raport używają wartości `backend: brian2`, aby utrzymać
  docelową nazwę integracji i stabilny kontrakt I/O;
- obecna implementacja nie buduje jeszcze pełnego obiektu `brian2.Network` ani
  nie symuluje realistycznej populacji neuronów kolcowych;
- adapter wykonuje jawny, deterministyczny transfer wejścia neural-mass do
  częstości wyładowań i potencjału błonowego, bez losowania i bez ukrytego
  stanu zależnego od środowiska;
- dla tej samej konfiguracji, seeda, sygnałów wejściowych i kolejności kroków
  wynik adaptera ma być identyczny, co pozwala testować mapowanie `HIP`,
  jednostki, limity amplitudy i format raportu;
- metryki SNN w raporcie są metrykami demonstracyjnymi kontraktu i stabilności,
  dlatego przy każdej metryce raport pokazuje krótki disclaimer.

Pełna biologiczna sieć Brian2 pozostaje osobnym etapem rozwoju. Do czasu
ustabilizowania testów regresyjnych `HIP` nie dodajemy kolejnych regionów SNN,
żeby nie rozszerzać zakresu walidacji przed potwierdzeniem zachowania pilota.
Konkretny plan warstw, konfiguracji, bramek testowych i przejścia do
`brian2.Network` opisuje
[`ADR-0034`](adr/0034-architektura-snn-brian2-network.md).

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
  max_feedback_amplitude: 0.15
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
- `max_feedback_amplitude` ogranicza bezwymiarowe wejście zwrotne
  `closed_loop_snn`; raport klasyfikuje wartość względem progów
  ostrzegawczych `0.20` (poziom informacyjny) i `0.30` (ostrzeżenie).
- `neural_mass_regions` zapisuje kolejność regionów neural-mass używaną przez
  `SNNPopulationMapping`.
- `circuits[].region` musi występować w `neural_mass_regions`; w bieżącym
  pilotażu dozwolony jest dokładnie jeden obwód i musi to być region `HIP`.
- `circuits[].backend` pozostaje pojedynczą wartością `brian2`; demo nie dodaje
  alternatywnych backendów.
- `coupling_gain` określa udział lokalnej aktywności SNN przy obliczaniu
  porównawczego przebiegu `report_only_snn`; w trybie `closed_loop` ten sam
  kontrakt służy do ograniczonego amplitudowo wejścia zwrotnego.

## Docelowa architektura `brian2.Network`

Planowana implementacja pełnego backendu Brian2 nie zmienia publicznego
kontraktu `NeuralMassToSNNInput` / `SNNToNeuralMassOutput`. Nowe elementy mają
być dodawane za tym interfejsem: fabryka sieci HIP buduje jawny `brian2.Network`,
adapter przechowuje sieć przez cały przebieg eksperymentu i wykonuje
`Network.run(sync_dt)` na każdym kroku synchronizacji, a silnik symulacji nadal
decyduje, czy wynik jest użyty jako `report_only_snn` czy `closed_loop_snn`.
Szczegółowy podział modułów, plan konfiguracji `implementation: brian2_network`,
bramki deterministyczności i etapy wdrożenia są zapisane w
[`ADR-0034`](adr/0034-architektura-snn-brian2-network.md).

## Kontrakt sygnałów i jednostek

Adapter wymiany sygnałów stosuje następujący kontrakt:

1. Neural-mass przekazuje do SNN jednoelementowe wektory dla obwodu `HIP`:
   - `excitatory_drive_hz` — częstość pobudzenia ekscytującego w hercach [Hz],
   - `inhibitory_drive_hz` — częstość pobudzenia hamującego w hercach [Hz],
   - `sync_dt` — krok synchronizacji w sekundach [s].
2. Lokalny adapter SNN zwraca jednoelementowe wektory dla obwodu `HIP`:
   - `firing_rate_hz` — częstość wyładowań w hercach [Hz],
   - `mean_membrane_potential_mv` — średni potencjał błonowy w miliwoltach [mV],
   - `sync_dt` — ten sam krok synchronizacji w sekundach [s].
3. `CouplingSignalAdapter` konwertuje `firing_rate_hz` do znormalizowanej
   aktywności regionalnej `fraction`, przycinanej do zakresu `[0, 1]`.

Mapowanie jest wyłącznie nazwane: region obwodu SNN nie jest dopasowywany po
indeksie z konfiguracji, dopóki `SNNPopulationMapping` nie potwierdzi, że nazwa
regionu istnieje w wektorze regionów neural-mass. Próba skonfigurowania wielu
obwodów albo obwodu innego niż `HIP` jest odrzucana jako wyjście poza zakres
pilotażu.

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

- status demonstracyjnego obwodu SNN hipokampa,
- listę mapowanych regionów SNN,
- `sync_dt_s`,
- jednostki wejścia i wyjścia,
- backend adaptera,
- `requested_mode`, czyli tryb żądany w konfiguracji,
- `computed_modes`, czyli warianty faktycznie policzone w raporcie,
- `comparison_scope_pl`, czyli polską uwagę, że SNN jest porównaniem
  demonstracyjnym, a nie pełnym modelem biologicznym,
- `comparison_note_pl`, czyli polską uwagę, że `closed_loop_snn` jest dodatkowym
  wariantem porównawczym, a nie nadpisaniem żądanego trybu,
- `max_feedback_amplitude_warning`, czyli poziom `ok`, `notice` albo `warning`
  dla limitu amplitudy sprzężenia,
- `mode_costs`, czyli deterministyczne liczniki kosztu wariantów
  (`model_runs`, `simulated_steps`, `snn_updates`, `feedback_applications`)
  używane do porównania `report_only_snn` z `closed_loop_snn`,
- `metric_disclaimer_pl`, czyli krótki disclaimer dopisywany w raporcie
  Markdown przy każdej metryce SNN,
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
- `snn.circuits` może zawierać tylko jeden obwód demonstracyjny `HIP`,
- `snn.circuits[].backend` musi mieć wartość `brian2`,
- region obwodu SNN musi istnieć w `snn.neural_mass_regions`,
- regiony inne niż `HIP` są odrzucane do czasu stabilnych testów regresyjnych
  pilota `HIP`, nawet jeżeli istnieją w `snn.neural_mass_regions`.

Testy obejmujące ten moduł:

```bash
PYTHONPATH=. pytest tests/test_config_schema.py tests/test_spiking_population_adapter.py tests/test_multiscale_engine.py
```

Najważniejsze przypadki testowe sprawdzają konfigurację demo, indeks mapowania
`HIP`, jednostki, `sync_dt`, limity ostrzegawcze `max_feedback_amplitude`,
obecność sekcji raportu `snn_comparison`, koszt i metryki `report_only_snn` vs
`closed_loop_snn` oraz rozdzielenie trybu żądanego od wariantów faktycznie
policzonych.

## Ograniczenia pilotażu

- Adapter `Brian2SpikingPopulationAdapter` nadal używa deterministycznego
  backendu zastępczego `brian2`; pełna sieć biologiczna jest osobnym krokiem
  rozwoju.
- Demo obejmuje jeden lokalny obwód hipokampa `HIP`, aby zachować prostą
  walidację, deterministyczność i czytelny raport. Nie dodajemy nowych regionów
  SNN, dopóki `HIP` nie ma stabilnych testów regresyjnych.
- Closed-loop jest MVP demonstracyjnym dla HIP; przed użyciem badawczym wymaga
  dalszej walidacji stabilności, porównania kosztu `report_only` vs
  `closed_loop` oraz kalibracji biologicznej.
