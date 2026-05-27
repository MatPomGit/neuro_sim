# BACKLOG — `neuro_sim`

Backlog jest uporządkowany według priorytetów (P0–P3) i gotowości wdrożeniowej.

- **P0** — krytyczne fundamenty produktu.
- **P1** — kluczowe rozszerzenia naukowe i dydaktyczne.
- **P2** — rozwój zaawansowany i jakościowy.
- **P3** — inicjatywy długoterminowe.

---

## P0 — Fundamenty (najwyższy priorytet)

### 1. Standaryzacja konfiguracji eksperymentów
**Cel:** pełna reprodukowalność uruchomień.

**Zakres prac:**
- Ujednolicenie schematu YAML/JSON dla wszystkich eksperymentów.
- Jawne sekcje: `stimulus`, `brain_profile`, `connectome`, `rng_seed`, `analysis`.
- Walidator konfiguracji z czytelnymi błędami domenowymi.

**Deliverables:**
- Specyfikacja konfiguracji.
- Przykładowe konfiguracje baseline.
- Testy walidacji wejścia.

**Akceptacja:**
- Każda symulacja uruchamia się przez jeden plik config i daje identyczny wynik przy tym samym seed.

---

### 2. Rejestr zdarzeń i raport dydaktyczny „timeline”
**Cel:** student rozumie „co, kiedy i dlaczego” wydarzyło się w modelu.

**Zakres prac:**
- Event bus dla kluczowych zdarzeń (bodziec, zmiana aktywacji regionu, modulacja neurochemiczna).
- Generator raportu krokowego z osią czasu.
- Słownik pojęć (np. co oznacza wzrost theta, spadek gatingu itd.).

**Deliverables:**
- Format logu zdarzeń.
- Raport `.md`/`.html` generowany po każdej symulacji.

**Akceptacja:**
- Raport umożliwia odtworzenie przebiegu eksperymentu bez zaglądania do kodu.

---

### 3. Baseline „Healthy Brain v1”
**Cel:** stabilny punkt odniesienia do porównań klinicznych.

**Zakres prac:**
- Definicja domyślnego profilu zdrowego mózgu.
- Parametry startowe aktywności regionów i neuromodulatorów.
- Testy regresji baseline.

**Deliverables:**
- Profil healthy_v1 + dokumentacja.
- Zestaw referencyjnych wykresów.

**Akceptacja:**
- Wyniki baseline pozostają stabilne między wersjami (w granicach tolerancji).

---

## P1 — Kluczowe rozszerzenia

### 4. Moduł anatomii i konektomu regionów
**Cel:** przejście z uproszczonej macierzy połączeń do modelu regionowego.

**Zakres prac:**
- Reprezentacja atlasu regionów i typów funkcjonalnych.
- Macierze `C_ij` oraz `delay_ij`.
- Mapa obszarów poznawczych (uwaga, pamięć, kontrola wykonawcza).

**Deliverables:**
- API modułu `anatomy/connectome`.
- Dane przykładowe dla małego atlasu edukacyjnego.

**Akceptacja:**
- Co najmniej dwa eksperymenty działają na konektomie z opóźnieniami.

---

### 5. Neural mass / mean-field per region
**Cel:** skalowalna symulacja whole-brain.

**Zakres prac:**
- Implementacja populacji E/I + adaptacja.
- Integracja sprzężeń międzyregionowych.
- Kalibracja zakresów parametrów dla stabilności numerycznej.

**Deliverables:**
- Moduł dynamiki regionu.
- Testy stabilności i sanity checks.

**Akceptacja:**
- Symulacja >50 regionów bez niestabilności i z interpretowalnymi wskaźnikami.

---

### 6. Pierwsza biblioteka neuromodulacji
**Cel:** dydaktyczne i kliniczne modelowanie wpływu neurochemii.

**Zakres prac:**
- Efekty DA/5-HT/ACh/NA jako modyfikatory pobudliwości, plastyczności i gatingu.
- Parametryzacja zmian stężeń i receptorów.
- Wizualizacja „co zmieniła dana modulacja”.

**Deliverables:**
- Profile neuromodulacyjne i API ich zastosowania.
- Raport porównawczy pre/post modulacji.

**Akceptacja:**
- Użytkownik może włączyć modulację i zobaczyć różnice czasowo-przestrzenne.

---

### 7. Scenariusze porównawcze healthy vs disorder vs lesion
**Cel:** realizacja kluczowej wartości edukacyjnej i psychiatrycznej.

**Zakres prac:**
- Zestaw profili zaburzeń (np. deficyt dopaminy, dysregulacja GABA, serotonin imbalance).
- Scenariusze uszkodzeń mechanicznych (ogniskowe, sieciowe).
- Uruchamianie tego samego bodźca na wielu profilach.

**Deliverables:**
- Katalog profili klinicznych v1.
- Automatyczny raport różnic (region, czas, funkcja poznawcza).

**Akceptacja:**
- Co najmniej 3 profile kliniczne + 2 typy lesion, każdy z interpretacją dydaktyczną.

---

## P2 — Rozwój zaawansowany

### 8. Zestaw zadań poznawczych (task battery)
**Cel:** standaryzacja eksperymentów poznawczych.

**Zakres prac:**
- Zadania uwagowe, pamięciowe, decyzyjne, emocjonalne.
- Parametryzacja trudności i rodzaju bodźca.
- Metryki behawioralne i neuronalne.
- Obowiązkowy pakiet referencyjny z roving oddball task.

**Deliverables:**
- Biblioteka tasków v1.
- Szablony raportów per task.

---

### 8A. Implementacja roving oddball task (priorytet P1/P2)
**Cel:** dostarczenie referencyjnego zadania do testów predykcji, nowości i adaptacji.

**Zakres prac:**
- Generator sekwencji bodźców z parametrami:
  - `n_runs`, `run_length_min/max`,
  - `stimulus_family`, `deviant_probability`,
  - `inter_stimulus_interval`, `jitter`.
- Konfiguracje eksperymentu:
  - `roving_oddball_healthy.yaml`,
  - `roving_oddball_disorder_*.yaml`,
  - `roving_oddball_lesion_*.yaml`.
- Implementacja metryk:
  - novelty/surprise index,
  - tempo habituacji,
  - latencja readaptacji po zmianie standardu,
  - różnice odpowiedzi E/I i neuromodulacyjnej.
- Warstwa dydaktyczna:
  - timeline trial-by-trial,
  - komentarz „co się dzieje w mózgu i dlaczego” przy przejściach standard/deviant.
- Warstwa porównawcza:
  - uruchamianie identycznej sekwencji dla healthy/disorder/lesion,
  - raport różnic amplituda-latencja-mechanizm.

**Deliverables:**
- Gotowy task `roving_oddball` z API scenariusza.
- 1 notebook dydaktyczny „Roving Oddball — od bodźca do interpretacji”.
- Raport porównawczy healthy vs disorder vs lesion.
- Testy regresji scenariusza i metryk.

**Akceptacja:**
- Ten sam seed i konfiguracja odtwarzają identyczną sekwencję bodźców.
- Raport pokazuje habituację w runie i reset odpowiedzi po zmianie standardu.
- Co najmniej 2 profile zaburzeń i 1 profil lesion mają opisane, odróżnialne wzorce.

---

### 9. Warstwa analityczna EEG/BOLD (aproksymacja)
**Cel:** połączenie symulacji z sygnałami znanymi z praktyki badawczej.

**Zakres prac:**
- Spektralne wskaźniki EEG (pasma, synchronizacja, phase-locking).
- Uproszczone mapowanie aktywności na BOLD/HRF.
- Porównania między profilami.

**Deliverables:**
- Moduły analizy sygnałowej v1.
- Raporty z wykresami i interpretacją.

---

### 10. Interfejs edukacyjny i „tryb nauczyciela”
**Cel:** zwiększenie dydaktyczności i użyteczności na zajęciach.

**Zakres prac:**
- Panele „co obserwujesz teraz?” i „dlaczego to ważne?”.
- Oznaczenia regionów/neuromodulatorów na osi czasu.
- Gotowe scenariusze lekcyjne z pytaniami kontrolnymi.

**Deliverables:**
- Widoki edukacyjne v1.
- Szablony lekcji laboratorjnych.

---

## P3 — Długoterminowe inicjatywy

### 11. Hybrydy mikro-makro (spiking submodels)
**Cel:** powiązanie mechanizmów mikro z zachowaniem makro.

**Zakres prac:**
- Integracja 1–2 obwodów spiking (np. hipokamp, PFC-BG).
- Synchronizacja kroków czasowych z warstwą neural mass.
- Porównanie jakościowe efektów.

---

### 12. Personalizacja i cohort simulation
**Cel:** scenariusze quasi-kliniczne i międzyosobnicze.

**Zakres prac:**
- Parametry indywidualne (np. wiek, podatność stresowa, bazowe poziomy modulacji).
- Symulacje kohortowe i rozkłady wyników.
- Raport statystyczny porównań.

---

### 13. Walidacja literaturowa i benchmarki
**Cel:** systematyczne mapowanie modelu na znane efekty naukowe.

**Zakres prac:**
- Rejestr hipotez i benchmarków.
- Zautomatyzowane testy zgodności jakościowej.
- Raport wersyjny „co model odtwarza, czego jeszcze nie”.

---

## Sekcja techniczna backlogu (cross-cutting)

### A. Jakość i testy
- Testy jednostkowe dynamiki, walidacji configów i generatorów raportów.
- Testy integracyjne pipeline eksperymentów.
- Testy regresji dla profili healthy i disorder.

### B. Dane i wersjonowanie parametrów
- Wersjonowane zbiory parametrów i konektomów.
- Metadane źródła danych i zakresu stosowalności.

### C. Dokumentacja i ADR
- ADR obowiązkowe dla zmian strukturalnych.
- Instrukcje „jak uruchomić i jak interpretować” dla każdego scenariusza.

---

## Definition of Ready / Definition of Done

### Definition of Ready (DoR)
Zadanie trafia do implementacji, gdy:
- ma jasno opisany cel poznawczy/edukacyjny,
- ma kryteria akceptacji i metryki,
- ma wskazane zależności danych/konfiguracji,
- ma plan testów.

### Definition of Done (DoD)
Zadanie uznaje się za ukończone, gdy:
- implementacja jest zgodna z zakresem,
- testy przechodzą,
- raport dydaktyczny jest aktualny,
- dokumentacja i (jeśli potrzeba) ADR zostały dodane,
- zmiana jest reprodukowalna z konfiguracji.
