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
