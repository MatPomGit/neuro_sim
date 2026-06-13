# ADR-0034: Architektura docelowego backendu SNN opartego o `brian2.Network`

**Status:** proposed  
**Data:** 2026-06-13

## Kontekst

Obecny pilotaż SNN dla regionu `HIP` utrzymuje stabilny kontrakt neural-mass ↔
SNN, ale adapter `Brian2SpikingPopulationAdapter` jest deterministycznym
backendem zastępczym. Taki adapter dobrze testuje jednostki, mapowanie regionów,
`sync_dt`, raport `snn_comparison` oraz limity sprzężenia, lecz nie tworzy pełnej
sieci neuronów kolcowych.

Następny krok wymaga konkretnego planu przejścia do pełnego obiektu
`brian2.Network` bez naruszenia dotychczasowej replikowalności i bez mieszania
warstw `brain_core`, `brain_model`, GUI oraz raportowania. W dokumentacji Brian2
zalecane są dwa sposoby uruchamiania symulacji: jawny obiekt `Network` z metodą
`Network.run()` albo system „magic” z globalnym `run()`. Dla tego projektu
wybieramy jawny `Network`, ponieważ lepiej pasuje do testowalnego adaptera,
monitorów przechowywanych w strukturach oraz kontrolowanego schedulerowania.

Uwaga terminologiczna: w konfiguracji i dokumentacji projektu używamy nazwy
backendu `brian2`; docelowym obiektem biblioteki jest `brian2.Network`, nie
`brain2.Network`.

## Decyzja

Planujemy architekturę w czterech warstwach. Publiczny kontrakt I/O pozostaje
ten sam, żeby nie łamać aktualnych testów, raportów i konfiguracji pilotażu.

### 1. Kontrakt domenowy pozostaje niezależny od Brian2

Pozostają stabilne klasy danych:

- `NeuralMassToSNNInput` — wejście neural-mass → SNN:
  `excitatory_drive_hz`, `inhibitory_drive_hz`, `sync_dt`;
- `SNNToNeuralMassOutput` — wyjście SNN → neural-mass:
  `firing_rate_hz`, `mean_membrane_potential_mv`, `sync_dt`;
- `SNNPopulationMapping` i `CouplingSignalAdapter` — mapowanie nazw regionów,
  konwersja Hz → aktywność regionalna i ograniczenie amplitudy feedbacku.

Te obiekty pozostają w `brain_core`, bez importów GUI i bez bezpośredniego
wycieku typów Brian2 do raportu.

### 2. Nowy backend Brian2 jest adapterem za tym samym interfejsem

Docelowy moduł implementacyjny:

```text
brain_core/populations/
├── spiking_population.py          # kontrakty i deterministyczny backend zastępczy
├── brian2_network_factory.py      # budowa obiektu brian2.Network dla HIP
└── brian2_network_adapter.py      # adapter step(signal) -> SNNToNeuralMassOutput
```

Zakres odpowiedzialności:

- `spiking_population.py` utrzymuje kontrakty i lekki fallback używany w testach
  bez zależności od Brian2.
- `brian2_network_factory.py` tworzy obiekty Brian2: `Clock`, populacje E/I,
  wejścia rate-driven, synapsy, monitory i jawny `Network`.
- `brian2_network_adapter.py` przechowuje zbudowany `Network`, aktualizuje wejścia
  na początku każdego kroku synchronizacji, uruchamia `network.run(sync_dt)` i
  agreguje wyniki do `SNNToNeuralMassOutput`.

Adapter nie tworzy nowej sieci w każdym kroku. Sieć jest budowana raz na
uruchomienie eksperymentu, a kolejne wywołania `step()` kontynuują jej stan.
Reset stanu do testów regresyjnych musi odbywać się jawnie przez metodę adaptera
lub przez mechanizm `store`/`restore` Brian2, nigdy przez ukryte przeładowanie
modułu.

### 3. Minimalna sieć HIP w pierwszym etapie

Pierwsza pełna implementacja Brian2 obejmuje wyłącznie `HIP` i ma prosty model
LIF z populacją pobudzającą i hamującą:

```text
Neural-mass activity
      │
      ▼
CouplingSignalAdapter.rate_to_spike_drive(...)
      │ exc_drive_hz / inh_drive_hz
      ▼
Brian2NetworkAdapter.step(...)
      │
      ├─ Excitatory input source, rate aktualizowany co sync_dt
      ├─ Inhibitory input source, rate aktualizowany co sync_dt
      ├─ HIP_E: populacja LIF pobudzająca
      ├─ HIP_I: populacja LIF hamująca
      ├─ Synapses: E→E, E→I, I→E, I→I z wagami i opóźnieniami z konfiguracji
      ├─ SpikeMonitor dla HIP_E/HIP_I
      └─ StateMonitor dla potencjału błonowego, domyślnie opcjonalny lub próbkowany
      │
      ▼
SNNToNeuralMassOutput(firing_rate_hz, mean_membrane_potential_mv, sync_dt)
```

Parametry biologiczne i numeryczne muszą pochodzić z konfiguracji, nie z kodu:

```yaml
snn:
  enabled: true
  mode: closed_loop
  implementation: brian2_network
  sync_dt: 0.010
  brian2:
    device: runtime
    dt: 0.001
    profile: false
    store_initial_state: true
  circuits:
    - region: HIP
      backend: brian2
      neuron_model: lif_current_based
      excitatory_neurons: 640
      inhibitory_neurons: 160
      membrane_time_constant_ms: 20.0
      refractory_ms: 2.0
      reset_potential_mv: -65.0
      threshold_potential_mv: -50.0
      resting_potential_mv: -70.0
      synapses:
        ee_weight: 0.05
        ei_weight: 0.04
        ie_weight: -0.08
        ii_weight: -0.06
        delay_ms: 1.5
      recording:
        spike_monitor: true
        membrane_monitor_sample: 32
```

Pole `implementation` rozdziela znaczenie `backend: brian2` od faktycznej
implementacji. Wartości planowane:

- `deterministic_surrogate` — obecny backend zastępczy, domyślny dopóki Brian2
  nie jest zależnością uruchomieniową projektu;
- `brian2_network` — pełny adapter z obiektem `brian2.Network`, dostępny dopiero
  po dodaniu zależności, testów regresyjnych i jawnej walidacji konfiguracji.

### 4. Scheduler i raport pozostają właścicielami trybów porównania

`engine.py` i `MultiScaleEngine` nadal decydują, czy wynik SNN jest używany jako:

- `report_only_snn` — porównanie bez modyfikowania przebiegu neural-mass;
- `closed_loop_snn` — wejście zwrotne ograniczone przez `max_feedback_amplitude`.

Backend Brian2 nie decyduje o trybie eksperymentu. Backend odpowiada tylko za
krok lokalnej sieci SNN i metryki techniczne kroku. Raport pozostaje miejscem,
w którym agregujemy:

- `mode_metrics`,
- `mode_costs`,
- `max_feedback_amplitude_warning`,
- disclaimer metryk SNN,
- wersję backendu i parametry konfiguracji potrzebne do reprodukcji.

## Wymagania deterministyczności

1. Seed musi pochodzić z konfiguracji eksperymentu i być zapisany w artefaktach.
2. Adapter Brian2 ustawia seed Brian2 i NumPy jawnie podczas budowy sieci.
3. Wszystkie losowe połączenia synaptyczne, opóźnienia lub początkowe potencjały
   muszą być deterministyczne dla tego samego seeda.
4. `sync_dt / brian2.dt` musi być dodatnią liczbą całkowitą.
5. Domyślnym urządzeniem w pierwszym etapie jest `runtime`; `standalone` wymaga
   osobnej decyzji, ponieważ zmienia model budowania artefaktów i środowiska.
6. Monitory nie mogą zmieniać semantyki wyników; mogą być wyłączane lub
   próbkowane dla wydajności, ale musi to być zapisane w konfiguracji.

## Bramki przed implementacją pełnego `brian2.Network`

Implementacja `implementation: brian2_network` może zostać włączona dopiero po
spełnieniu poniższych warunków:

1. Zależność `brian2` jest dodana spójnie do `pyproject.toml`,
   `requirements.txt` / innych plików środowiska oraz dokumentacji użytkowej.
2. Walidator konfiguracji odrzuca brakujące lub niespójne parametry sieci HIP z
   czytelnym błędem.
3. Testy kontraktu porównują `deterministic_surrogate` i `brian2_network` pod
   względem kształtów, jednostek, skończoności i deterministyczności.
4. Test regresyjny HIP zapisuje stabilne oczekiwane zakresy dla firing rate,
   potencjału błonowego, metryk `report_only_snn` i metryk `closed_loop_snn`.
5. Raport zapisuje `implementation`, wersję Brian2, `brian2.dt`, seed oraz koszty
   symulacji.
6. Nowe regiony SNN pozostają zablokowane do czasu przejścia regresji HIP.

## Etapy wdrożenia

1. **Etap A — dokumentacja i kontrakt**: obecny ADR, opis docelowej architektury,
   brak nowych zależności i brak zmiany zachowania uruchomień.
2. **Etap B — konfiguracja eksperymentalna**: dodać opcjonalne pola
   `implementation` i `snn.brian2`, walidowane tylko dla `brian2_network`.
3. **Etap C — fabryka sieci HIP**: dodać `brian2_network_factory.py` i testy
   budowy sieci oznaczone jako pomijane, gdy Brian2 nie jest zainstalowany.
4. **Etap D — adapter kroku**: dodać `Brian2NetworkAdapter.step()` i testy
   deterministyczności dla krótkiego przebiegu HIP.
5. **Etap E — integracja z raportem**: dodać wersję Brian2, `implementation`,
   profiling i metryki kosztu rzeczywistego `Network.run()`.
6. **Etap F — decyzja o rozszerzeniu regionów**: dopiero po stabilnej regresji
   HIP przygotować osobny ADR dla kolejnego regionu lub wielu obwodów.

## Konsekwencje

**Pozytywne:**

- pełny Brian2 będzie ukryty za tym samym kontraktem co obecny backend,
- testy i raporty pozostaną porównywalne między fallbackiem i pełną siecią,
- jawny `Network` ograniczy ryzyko przypadkowego zbierania obiektów przez system
  „magic” Brian2,
- etapowanie zmniejszy ryzyko wprowadzenia niedeterministycznych regresji.

**Negatywne / koszty:**

- dojdzie nowa zależność naukowa i dodatkowy czas testów,
- konfiguracja SNN będzie dłuższa, bo parametry biologiczne muszą być jawne,
- `closed_loop_snn` z pełnym Brian2 będzie droższy obliczeniowo niż obecny
  backend zastępczy,
- testy regresyjne będą wymagały tolerancji numerycznych zależnych od wersji
  Brian2 i środowiska wykonawczego.

## Alternatywy rozważane

- **System „magic” Brian2 i globalne `run()`** — odrzucone, bo utrudnia
  kontrolę obiektów, monitorów i resetów w testach.
- **Budowanie nowego `Network` w każdym `step()`** — odrzucone, bo byłoby
  prostsze do implementacji, ale nie reprezentowałoby ciągłego stanu lokalnej
  sieci HIP i zawyżałoby koszt.
- **Natychmiastowe dodanie wielu regionów SNN** — odrzucone do czasu stabilnych
  testów regresyjnych HIP.
- **Zastąpienie kontraktu I/O typami Brian2** — odrzucone, bo przeniosłoby
  zależność Brian2 do warstw raportowania i konfiguracji.

## Powiązane

- `docs/snn_cosimulation_demo.md`
- `docs/architecture_decision_records.md`
- `brain_core/populations/spiking_population.py`
- `brain_core/simulation/signal_adapter.py`
- `brain_core/simulation/engine.py`
- `tests/test_spiking_population_adapter.py`
- Oficjalna dokumentacja Brian2: `https://brian2.readthedocs.io/en/stable/user/running.html`
- Oficjalna dokumentacja Brian2: `https://brian2.readthedocs.io/en/stable/user/models.html`
