# Architecture Decision Records (ADR)

Ten dokument wprowadza standard ADR w projekcie **neuro_sim** i zawiera pierwsze, bazowe decyzje architektoniczne.

## Cel

ADR (Architecture Decision Record) służy do:
- dokumentowania istotnych decyzji technicznych,
- utrzymania kontekstu „dlaczego” obok kodu,
- ułatwienia onboardingu i przeglądów zmian,
- ograniczania regresji decyzji (powrotu do dawnych problemów).

## Zakres stosowania ADR

Tworzymy ADR, gdy decyzja:
- wpływa na wiele modułów,
- zmienia sposób modelowania domeny lub strukturę projektu,
- dotyczy długoterminowych kompromisów (np. wydajność vs. czytelność),
- może być kwestionowana w przyszłości.

Przykłady:
- wybór architektury silnika symulacji,
- standard konfiguracji i walidacji,
- podejście do I/O, serializacji i raportowania,
- zasady modularności i granic odpowiedzialności.

## Format ADR

Każdy ADR powinien zawierać sekcje:

1. **Status** (proposed / accepted / superseded / deprecated)
2. **Kontekst**
3. **Decyzja**
4. **Konsekwencje**
5. **Alternatywy rozważane**
6. **Powiązane dokumenty / issue / PR**

## Konwencja nazewnictwa

Docelowo rekomendujemy przechowywanie ADR jako osobnych plików w `docs/adr/`:

- `0001-nazwa-decyzji.md`
- `0002-kolejna-decyzja.md`

W przypadku pojedynczego pliku zbiorczego (ten dokument), każda decyzja dostaje własny nagłówek `## ADR-XXXX`.

---

## ADR-0001: Podział na warstwy `brain_core` i `brain_model`

**Status:** accepted  
**Data:** 2026-05-26

### Kontekst
Projekt zawiera zarówno logikę niskopoziomową (silnik, integratory, scheduler, stan symulacji), jak i logikę domenową (moduły poznawcze, zachowania, scenariusze, raportowanie). Bez rozdziału warstw kod szybko staje się trudny w utrzymaniu.

### Decyzja
Utrzymujemy separację:
- `brain_core/` — warstwa infrastrukturalna i mechanika symulacji,
- `brain_model/` — warstwa domenowa modelu neuronalno-poznawczego.

Interakcja ma przebiegać przez jawne API, a nie przez wzajemne „przecieki” implementacyjne.

### Konsekwencje
**Pozytywne:**
- czytelny podział odpowiedzialności,
- łatwiejsze testowanie i wymiana elementów silnika,
- mniejsza podatność na sprzężenia zwrotne między domeną a infrastrukturą.

**Negatywne / koszty:**
- większa dyscyplina przy projektowaniu interfejsów,
- czasem dodatkowy kod mapujący dane między warstwami.

### Alternatywy rozważane
- Monolityczny moduł bez warstw: szybszy start, ale gorsza skalowalność i utrzymanie.
- Podział tylko funkcjonalny bez granicy core/model: prostsza nawigacja, ale wyższe ryzyko zależności cyklicznych.

### Powiązane
- `brain_core/simulation/`
- `brain_model/`

---

## ADR-0002: Konfiguracja oparta o pliki YAML + schemat

**Status:** accepted  
**Data:** 2026-05-26

### Kontekst
Symulacje muszą być łatwo odtwarzalne i porównywalne między uruchomieniami/scenariuszami. Parametry „zaszyte” w kodzie utrudniają reprodukcję wyników.

### Decyzja
Konfigurację trzymamy w `configs/*.yaml`, a jej interpretację i walidację opieramy o dedykowane moduły loadera/schematu.

### Konsekwencje
**Pozytywne:**
- powtarzalność eksperymentów,
- łatwe porównywanie wariantów,
- możliwość walidacji i szybkiego wykrywania błędów konfiguracji.

**Negatywne / koszty:**
- konieczność utrzymania zgodności schema ↔ konfiguracje,
- dodatkowa złożoność przy migracjach parametrów.

### Alternatywy rozważane
- Konfiguracja wyłącznie przez CLI: mniej plików, ale słabsza czytelność i wersjonowanie.
- Konfiguracja „hardcoded”: najprostsza lokalnie, nieakceptowalna dla badań porównawczych.

### Powiązane
- `configs/default.yaml`
- `brain_core/simulation/config_loader.py`
- `brain_core/simulation/config_schema.py`

---

## ADR-0003: Deterministyczność przez kontrolę źródeł losowości

**Status:** accepted  
**Data:** 2026-05-26

### Kontekst
W modelach symulacyjnych brak kontroli nad losowością utrudnia debugowanie, kalibrację i walidację wyników.

### Decyzja
Źródła losowe centralizujemy i inicjalizujemy w kontrolowany sposób (seed, strumienie RNG), tak aby możliwa była reprodukcja przebiegu symulacji.

### Konsekwencje
**Pozytywne:**
- powtarzalne eksperymenty,
- łatwiejsza diagnostyka odchyleń,
- możliwość porównań A/B.

**Negatywne / koszty:**
- konieczność świadomego przekazywania RNG między komponentami,
- ryzyko pozornej deterministyczności, jeśli część kodu omija wspólne źródła.

### Alternatywy rozważane
- Lokalny RNG „gdzie wygodnie”: mniejszy próg wejścia, ale chaos w reprodukcji.
- Brak deterministyczności: niedopuszczalne w kontekście badań/kalibracji.

### Powiązane
- `brain_core/simulation/random_sources.py`

---

## Procedura dodawania kolejnego ADR

1. Utwórz nowy rekord (`docs/adr/NNNN-*.md` lub sekcja `ADR-XXXX` w tym pliku).
2. Oznacz **Status: proposed**.
3. Podlinkuj ADR w PR i poproś o review architektoniczny.
4. Po akceptacji zmień status na **accepted**.
5. Jeśli decyzja została zastąpiona — oznacz jako **superseded** i dodaj link do nowego ADR.

## Krótki szablon (copy/paste)

```md
# ADR-XXXX: Tytuł decyzji

**Status:** proposed  
**Data:** RRRR-MM-DD

### Kontekst
...

### Decyzja
...

### Konsekwencje
...

### Alternatywy rozważane
...

### Powiązane
...
```


## ADR-0004: Model regionowy Wilson-Cowan z opóźnionym sprzężeniem strukturalnym

**Status:** accepted  
**Data:** 2026-05-26

### Kontekst
Potrzebny jest minimalny, ale jawny fundament pod symulacje multi-region: osobne stany pobudzające/hamujące (E/I) na region, macierz połączeń strukturalnych i opóźnienia przewodzenia w sprzężeniu międzyregionowym.

### Decyzja
Dodajemy trzy małe komponenty w `brain_core`:
- `populations/wilson_cowan.py`: regionowy model Wilson-Cowan z parametrami per region (`tau_E`, `tau_I`, `w_EE`, `w_EI`, `w_IE`, `w_II`, `gain`, `threshold`),
- `networks/structural_network.py`: macierzowe sprzężenie strukturalne,
- `networks/delays.py`: bufor historii i obliczenie `coupling_i(t) = Σ_j C_ij * activity_j(t-delay_ij)`.

Dodatkowo dodajemy demonstracyjny plik konfiguracji `configs/multi_region_delay_demo.yaml`.

### Konsekwencje
**Pozytywne:**
- czytelna separacja odpowiedzialności: dynamika regionu vs sieć połączeń vs opóźnienia,
- bezpośrednie wsparcie dla scenariuszy whole-brain o niskim koszcie obliczeniowym,
- łatwe testowanie komponentowe.

**Negatywne / koszty:**
- nowa konfiguracja demo nie jest jeszcze automatycznie podpięta pod `run_experiment`.

### Alternatywy rozważane
- Jedna klasa łącząca dynamikę, połączenia i opóźnienia: mniej plików, ale słabsza testowalność i większe mieszanie odpowiedzialności.
- Natychmiastowa pełna integracja z istniejącym `brain_model`: większy zakres zmian i ryzyko regresji poza aktualnym zadaniem.

### Powiązane
- `brain_core/populations/wilson_cowan.py`
- `brain_core/networks/structural_network.py`
- `brain_core/networks/delays.py`
- `configs/multi_region_delay_demo.yaml`

---

## ADR-0005: Ujednolicenie typów neuromodulatorów między `brain_model` i `brain_core`

**Status:** proposed  
**Data:** 2026-05-26

### Kontekst
W `brain_model` neuromodulacja obejmuje m.in. `noradrenaline`, `acetylcholine`, `serotonin`, `gaba`, `glutamate`, `cortisol`. W pierwszej implementacji `brain_core/synapses` użyto częściowo innego zestawu nazw i pól, co utrudnia spójne mapowanie sygnałów między warstwami i scenariuszami farmakologicznymi.

### Decyzja
Rozszerzamy i normalizujemy stan neuromodulacji w `brain_core` tak, aby obejmował:
- `dopamine`,
- `noradrenaline`,
- `acetylcholine`,
- `serotonin`,
- `gaba`,
- `glutamate`,
- `cortisol`,
- `adrenaline`.

Dodatkowo dodajemy dedykowane moduły synaptyczne `noradrenaline.py`, `cortisol.py`, `adrenaline.py` oraz aktualizujemy interfejs farmakologiczny i mapowanie wpływu neuromodulacji w modelu regionowym Wilson-Cowan.

### Konsekwencje
**Pozytywne:**
- spójny słownik neuromodulatorów między warstwami projektu,
- łatwiejsze porównywanie scenariuszy i translacja diagnostyki,
- czytelniejsze rozszerzanie modeli o kolejne manipulacje farmakologiczne.

**Negatywne / koszty:**
- większy wektor stanu i więcej parametrów modulacji do kalibracji,
- konieczność aktualizacji testów i interfejsów używających poprzedniego zestawu pól.

### Alternatywy rozważane
- Utrzymanie lokalnych mapowań/adaptorów nazw bez zmiany stanu: mniejszy diff, ale rosnący dług techniczny.
- Redukcja do absolutnie wspólnego minimum (bez adrenaliny): prostsze, ale mniej elastyczne dla scenariuszy stresowych.

### Powiązane
- `brain_core/synapses/`
- `brain_core/populations/wilson_cowan.py`
- `brain_core/experiments/pharmacology.py`
- `brain_model/model.py`

---

## ADR-0006: Synaptyczna plastyczność neural-mass z dwiema skalami czasowymi

**Status:** proposed  
**Data:** 2026-05-26

### Kontekst
Potrzebne jest porównywalne uczenie między eksperymentami z jawną regułą aktualizacji wag, kontrolą stabilności (homeostaza, clamp) oraz rozdzieleniem szybkich i wolnych procesów plastyczności (forgetting/consolidation).

### Decyzja
Dodajemy moduł `brain_core/synapses/plasticity.py` zawierający:
- regułę neural-mass `dW_ij/dt = eta * pre_j * post_i * neuromod - lambda * W_ij`,
- szybki składnik aktualizacji (hebbowski + forgetting),
- wolny składnik aktualizacji (consolidation + homeostatic scaling),
- clamp wag `min_weight/max_weight`,
- tracker historii wag i metryk (`mean/std`, normy szybkich/wolnych aktualizacji).

Rozszerzamy też `brain_core/experiments` o prosty protokół fazowy train/test do standaryzacji przebiegów porównawczych.

### Konsekwencje
**Pozytywne:**
- jawna, testowalna i stabilizowana dynamika wag,
- gotowa telemetria do analizy porównawczej,
- spójny szablon eksperymentów train/test.

**Negatywne / koszty:**
- dodatkowe parametry wymagające kalibracji (`eta`, `lambda`, homeostasis, forgetting, consolidation),
- konieczność utrzymania zgodności integracji między modelem i protokołami.

### Alternatywy rozważane
- Jednoskalowa aktualizacja wag bez consolidation: prostsza, ale słabsze modelowanie trwałości śladu.
- Brak homeostazy i clamp: mniej kodu, ale wyższe ryzyko niestabilności.

### Powiązane
- `brain_core/synapses/plasticity.py`
- `brain_core/experiments/protocols.py`
- `tests/test_plasticity_protocols.py`

## ADR-0007: Kanał obserwacyjny EEG/BOLD i zestaw walidacji porównawczej

**Status:** proposed  
**Data:** 2026-05-26

### Kontekst
Model `brain_core` miał dynamikę neuronalną, ale brakowało prostego toru obserwacyjnego do mapowania aktywności na sygnały porównywalne z danymi EEG/fMRI oraz brakowało zunifikowanych metryk porównania do targetów eksperymentalnych.

### Decyzja
Dodajemy minimalny, deterministyczny tor obserwacyjny:
- `brain_core/physiology/eeg_forward_model.py`: liniowy model forward EEG z macierzą leadfield,
- `brain_core/physiology/neurovascular_coupling.py` + `brain_core/physiology/bold_hrf.py`: neurovascular drive i konwolucję HRF dla BOLD,
- `brain_core/analysis/signal_metrics.py`: moc pasm, PLV, macierz connectivity i raport porównawczy,
- `analysis/reports.py`: raport końcowy agregujący metryki EEG/fMRI/behawior,
- `data/validation/*.csv`: minimalne benchmarki referencyjne.

### Konsekwencje
**Pozytywne:**
- możliwa jest szybka walidacja jakości symulacji względem targetów,
- utrzymujemy prostotę (liniowy leadfield, konwolucja 1D/2D bez ciężkich zależności),
- przygotowujemy spójny format raportu końcowego.

**Negatywne / koszty:**
- model HRF jest uproszczony i nie zastępuje pełnego modelu hemodynamicznego,
- metryki connectivity opierają się na korelacji liniowej.

### Alternatywy rozważane
- Integracja z zewnętrznymi bibliotekami neuroimagingowymi: bogatsza funkcjonalność, ale większa złożoność i zależności.
- Brak dedykowanego toru obserwacyjnego: mniejszy zakres zmian, ale brak obiektywnej walidacji względem EEG/fMRI.

### Powiązane
- `brain_core/physiology/eeg_forward_model.py`
- `brain_core/physiology/neurovascular_coupling.py`
- `brain_core/physiology/bold_hrf.py`
- `brain_core/analysis/signal_metrics.py`
- `analysis/reports.py`
- `data/validation/eeg_target.csv`
- `data/validation/fmri_target.csv`
- `data/validation/behavior_target.csv`

---

## ADR-0008: Rozszerzenie EEG o warianty forward i solvery inverse

**Status:** proposed  
**Data:** 2026-05-26

### Kontekst
Pierwotny model EEG obejmował wyłącznie prostą projekcję leadfield bez referencjonowania i bez odtwarzania źródeł z przestrzeni sensorowej.

### Decyzja
Rozszerzamy `brain_core/physiology/eeg_forward_model.py` o:
- konfigurowalne forward modelowanie (`reference=none|average`, opcjonalny szum sensorowy),
- klasę `EEGInverseSolver` z solverami `minimum_norm` (ridge/MNE) i `weighted_minimum_norm` (depth-weighted MNE).

### Konsekwencje
**Pozytywne:**
- spójne API dla projekcji i rekonstrukcji źródeł,
- możliwość porównań symulacja↔EEG także w kierunku inverse,
- nadal brak ciężkich zależności zewnętrznych.

**Negatywne / koszty:**
- inverse jest uproszczone (brak pełnego modelu szumu i regularizacji przestrzennej typu LORETA),
- dobór `lam` i wag głębokości wymaga kalibracji.

### Alternatywy rozważane
- Użycie zewnętrznych toolboxów EEG (MNE/FieldTrip): większa dokładność i zakres metod, ale wyższy koszt integracji.
- Pozostanie przy samym forward: prostsze, ale bez obsługi inverse problem.

### Powiązane
- `brain_core/physiology/eeg_forward_model.py`
- `tests/test_observation_and_analysis.py`

## ADR-0009: Pilotażowa współsymulacja neural-mass ↔ SNN z backendem Brian2

**Status:** proposed  
**Data:** 2026-05-27

### Kontekst
Projekt potrzebuje praktycznego punktu startowego do hybrydowej współsymulacji (neural-mass + SNN) bez rozszerzania od razu na cały mózg. Jednocześnie wymagane jest jawne API wymiany sygnałów oraz obsługa różnych kroków czasowych.

### Decyzja
Wprowadzamy minimalny, testowalny szkielet:
- `brain_core/populations/spiking_population.py` z adapterem `Brian2SpikingPopulationAdapter` jako backendem startowym,
- jawny kontrakt wymiany sygnałów:
  - wejście NM→SNN: `excitatory_drive_hz`, `inhibitory_drive_hz`, `sync_dt`,
  - wyjście SNN→NM: `firing_rate_hz`, `mean_membrane_potential_mv`, `sync_dt`,
- `brain_core/simulation/multiscale_engine.py` z prostym schedulerem wieloskalowym (`base_dt` + zadania z własnym `dt`),
- ograniczenie pilotażu do 1–2 obwodów (hipokamp, DLPFC) na poziomie konfiguracji eksperymentu i testów integracyjnych.

### Konsekwencje
**Pozytywne:**
- szybki i prosty start (KISS) pod dalszą integrację z pełnym modelem Brian2,
- jednoznaczny kontrakt danych między warstwami,
- deterministyczna walidacja działania harmonogramu wieloskalowego.

**Negatywne / koszty:**
- adapter startowy ma uproszczoną dynamikę (fallback) i nie zastępuje pełnej sieci kolców,
- konieczne późniejsze dopracowanie mapowania biologicznego i kalibracji.

### Alternatywy rozważane
- Od razu pełna integracja całego mózgu: większe ryzyko i koszt, trudniejszy debugging.
- Wybór innego backendu startowego (NEST): sensowny, ale cięższy wdrożeniowo w tym etapie.

### Powiązane
- `brain_core/populations/spiking_population.py`
- `brain_core/simulation/multiscale_engine.py`
- `tests/test_multiscale_engine.py`
- `tests/test_spiking_population_adapter.py`

---

## ADR-0007: Ujednolicony postprocessing analityczny i raport benchmarkowy

**Status:** proposed  
**Data:** 2026-05-27

### Kontekst
Silnik symulacji zwracał surowe artefakty (`activity`, `oscillations`, `behavior`), ale brakowało jednolitego etapu postprocessingu: obliczenia metryk, porównania z benchmarkami referencyjnymi oraz raportu końcowego w spójnych formatach.

### Decyzja
Dodajemy moduły `brain_core/analysis/reports.py` oraz `brain_core/analysis/benchmark_loader.py`, a w `brain_core/simulation/engine.py` nowy etap po symulacji:
1. ekstrakcja sygnałów EEG/fMRI/behavior,
2. obliczenie metryk analitycznych (moc pasm, ERP proxy, phase-locking, connectivity, metryki behawioralne),
3. porównanie do benchmarków z `data/validation/`,
4. publikacja raportu w strukturze JSON oraz (opcjonalnie przy zapisie wyników) eksport JSON/CSV/Markdown.

### Konsekwencje
**Pozytywne:**
- powtarzalny i jednolity pipeline oceny wyników,
- prostsza automatyczna walidacja oraz testy integracyjne,
- gotowe artefakty raportowe do dalszej analizy.

**Negatywne / koszty:**
- dodatkowy czas postprocessingu,
- konieczność utrzymywania zgodności formatu benchmarków i raportu.

### Alternatywy rozważane
- Pozostawienie raportowania poza silnikiem (w osobnym skrypcie): mniejsza ingerencja, ale brak jednolitego przepływu i większe ryzyko rozjazdu metryk.
- Raport tylko JSON: prostsze I/O, ale mniejsza użyteczność dla użytkowników preferujących CSV/Markdown.

### Powiązane
- `brain_core/analysis/reports.py`
- `brain_core/analysis/benchmark_loader.py`
- `brain_core/simulation/engine.py`
- `data/validation/*.csv`
