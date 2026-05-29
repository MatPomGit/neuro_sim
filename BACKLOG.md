# BACKLOG — `neuro_sim`

Backlog jest uporządkowany według priorytetów (P0–P3) i gotowości wdrożeniowej.

- **P0** — krytyczne fundamenty produktu.
- **P1** — kluczowe rozszerzenia naukowe i dydaktyczne.
- **P2** — rozwój zaawansowany i jakościowy.
- **P3** — inicjatywy długoterminowe.

---

## Stan na dzień 2026-05-29

Backlog opisuje zarówno prace przyszłe, jak i obszary już częściowo zaimplementowane. Statusy oznaczają:
- `done` — zakres pozycji jest domknięty zgodnie z kryteriami akceptacji,
- `partial` — istnieją artefakty implementacyjne, ale pozostały elementy do ukończenia,
- `planned` — pozycja jest zaplanowana i nie ma jeszcze wystarczającej implementacji,
- `blocked` — realizacja wymaga wcześniejszego odblokowania zależności.

Najważniejsze istniejące fundamenty obejmują moduły eksperymentów, uszkodzeń i raportowania, m.in. `brain_core/experiments/protocols.py`, `brain_core/experiments/lesions.py` oraz `brain_core/analysis/reports.py`. Dla pozycji P0–P2 wskazano poniżej konkretne artefakty, aby oddzielić zakres już obecny w repozytorium od pozostałych prac.

### Najbliższe zaplanowane prace

Poniższa lista zbiera komplet najbliższych prac planowanych na bazie aktualnego stanu repozytorium. Kolejność odzwierciedla zależności: najpierw domknięcie fundamentów P0, potem elementy P1/P2 potrzebne do scenariuszy dydaktycznych i porównawczych.

1. **Domknięcie konfiguracji eksperymentów P0** — ujednolicić YAML/JSON wokół istniejących `ExperimentConfig`, `config_loader` i konfiguracji `configs/*.yaml`; dodać czytelne błędy walidacji oraz testy dla sekcji `stimulus`, `brain_profile`, `connectome`, `rng_seed`, `analysis`.
2. **Oś czasu i raport dydaktyczny P0** — rozwinąć raportowanie z `brain_core/analysis/reports.py` i `brain_model/report_export.py` o spójny log zdarzeń, pełną oś trial-by-trial i słownik pojęć dla użytkownika.
3. **Baseline `healthy_v1` P0** — sformalizować profil zdrowy jako wersjonowany artefakt, dodać dokumentację, referencyjne wykresy i progi regresji dla wyników baseline.
4. **Konektom z opóźnieniami P1** — potwierdzić co najmniej dwa eksperymenty oparte na `brain_core/anatomy/*`, `brain_core/networks/*` i danych `data/connectomes/*`; uzupełnić mapowanie poznawcze regionów.
5. **Stabilizacja neural mass P1** — zweryfikować scenariusze >50 regionów dla `brain_core/populations/wilson_cowan.py`, doprecyzować zakresy parametrów i sanity checks.
6. **Neuromodulacja P1** — domknąć spójne API profili DA/5-HT/ACh/NA/GABA/glutaminian oraz dodać raport pre/post pokazujący różnice czasowo-przestrzenne.
7. **Scenariusze healthy/disorder/lesion P1** — rozbudować katalog profili klinicznych i uszkodzeń, a następnie rozszerzyć automatyczny raport różnic o region, czas, funkcję poznawczą i komentarz dydaktyczny.
8. **Biblioteka tasków P2** — ujednolicić istniejące protokoły `stroop`, `go_nogo`, `n_back` i API w `brain_core/experiments/protocols.py`; przygotować wspólne szablony raportów per task.
9. **Roving oddball P2** — wdrożyć dedykowany generator sekwencji, konfiguracje healthy/disorder/lesion, metryki habituacji/novelty/readaptacji i testy reprodukowalności seedów.
10. **Raporty EEG/BOLD P2** — połączyć metryki z `brain_core/analysis/*` i `brain_core/physiology/*` w raportach z wykresami, interpretacją i porównaniem profili.
11. **Migracja desktopowego GUI na PySide6 P2** — domknąć przejście nowych
    przepływów desktopowych z `tkinter`/`TkAgg` na PySide6/Qt, zachowując
    kompatybilny punkt wejścia `brain_model.gui:run_gui` zgodnie z ADR-0016.
12. **Tryb nauczyciela P2** — dopisać widoki edukacyjne, pytania kontrolne i
    polskie etykiety pojęć zgodne z `docs/english_polish_glossary.md`.
13. **Jakość i dokumentacja przekrojowa** — utrzymać standard docstringów/type hints,
    aktualizować `docs/program_structure.md` oraz ADR przy zmianach
    strukturalnych i dopisać instrukcje uruchamiania dla scenariuszy.

## P0 — Fundamenty (najwyższy priorytet)

### 1. Standaryzacja konfiguracji eksperymentów
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/simulation/config_schema.py`, `brain_core/simulation/config_loader.py`, `brain_core/simulation/run.py`, `configs/default.yaml`, `configs/cognitive_demo.yaml`.

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

**Pozostały zakres:**
- Domknąć jednolity schemat dla wszystkich eksperymentów i formatów YAML/JSON.
- Uzupełnić czytelne błędy domenowe oraz testy walidacji dla pełnego zestawu sekcji.

---

### 2. Rejestr zdarzeń i raport dydaktyczny „timeline”
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/analysis/reports.py`, `analysis/reports.py`, `brain_model/report.py`, `brain_model/report_export.py`, `tests/test_observation_and_analysis.py`.

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

**Pozostały zakres:**
- Ujednolicić format logu zdarzeń dla wszystkich typów symulacji.
- Rozszerzyć raport o pełną oś czasu trial-by-trial i słownik pojęć.

---

### 3. Baseline „Healthy Brain v1”
**Status:** `partial`

**Artefakty implementacyjne:** `configs/default.yaml`, `configs/brain_model_config_2026-05-28.json`, `brain_model/params.py`, `brain_model/model.py`, `outputs/20260528_161218_baseline_gui/metadata.json`.

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

**Pozostały zakres:**
- Sformalizować profil `healthy_v1` jako wersjonowany artefakt z dokumentacją.
- Dodać referencyjne wykresy i progi regresji baseline.

---

## P1 — Kluczowe rozszerzenia

### 4. Moduł anatomii i konektomu regionów
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/anatomy/regions.py`, `brain_core/anatomy/atlases.py`, `brain_core/anatomy/connectome.py`, `brain_core/networks/structural_network.py`, `brain_core/networks/delays.py`, `data/atlases/default_regions.csv`, `data/connectomes/weights.csv`, `data/connectomes/fiber_lengths.csv`, `tests/test_atlas_connectome.py`.

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

**Pozostały zakres:**
- Potwierdzić dwa kompletne eksperymenty oparte o konektom z opóźnieniami.
- Uzupełnić mapowanie obszarów poznawczych i opis danych edukacyjnych.

---

### 5. Neural mass / mean-field per region
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/populations/wilson_cowan.py`, `brain_core/simulation/multiscale_engine.py`, `brain_core/simulation/integrators.py`, `tests/test_wilson_cowan_network.py`, `tests/test_multiscale_engine.py`.

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

**Pozostały zakres:**
- Zweryfikować stabilność dla scenariuszy >50 regionów.
- Doprecyzować zakresy parametrów i wskaźniki interpretacyjne.

---

### 6. Pierwsza biblioteka neuromodulacji
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/experiments/pharmacology.py`, `brain_core/synapses/dopamine.py`, `brain_core/synapses/serotonin.py`, `brain_core/synapses/acetylcholine.py`, `brain_core/synapses/noradrenaline.py`, `brain_core/synapses/gaba_glutamate.py`, `tests/test_neuromodulation.py`.

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

**Pozostały zakres:**
- Domknąć profile neuromodulacyjne DA/5-HT/ACh/NA jako spójne API.
- Uzupełnić raport porównawczy pre/post modulacji z warstwą dydaktyczną.

---

### 7. Scenariusze porównawcze healthy vs disorder vs lesion
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/experiments/lesions.py`, `brain_model/scenarios/library.py`, `brain_model/scenarios/types.py`, `tests/test_lesions.py`, `tests/test_task_protocols_and_engine.py`.

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

**Pozostały zakres:**
- Uzupełnić katalog profili klinicznych v1 i interpretacje dydaktyczne.
- Rozszerzyć automatyczny raport różnic o region, czas i funkcję poznawczą.

---

## P2 — Rozwój zaawansowany

### 8. Zestaw zadań poznawczych (task battery)
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/experiments/protocols.py`, `brain_model/stimuli.py`, `configs/stroop.yaml`, `configs/go_nogo.yaml`, `configs/n_back.yaml`, `tests/test_task_protocols_and_engine.py`, `tests/test_task_stimulus_player.py`.

**Cel:** standaryzacja eksperymentów poznawczych.

**Zakres prac:**
- Zadania uwagowe, pamięciowe, decyzyjne, emocjonalne.
- Parametryzacja trudności i rodzaju bodźca.
- Metryki behawioralne i neuronalne.
- Obowiązkowy pakiet referencyjny z roving oddball task.

**Deliverables:**
- Biblioteka tasków v1.
- Szablony raportów per task.

**Pozostały zakres:**
- Ujednolicić bibliotekę tasków v1 oraz szablony raportów per task.
- Dodać obowiązkowy pakiet referencyjny z roving oddball task.

---

### 8A. Implementacja roving oddball task (priorytet P1/P2)
**Status:** `planned`

**Artefakty implementacyjne:** brak dedykowanego artefaktu `roving_oddball`; punktem startowym są `brain_core/experiments/protocols.py`, `brain_core/simulation/random_sources.py` i `tests/test_task_protocols_and_engine.py`.

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
  - wskaźnik nowości/zaskoczenia (novelty/surprise index),
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
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/analysis/spectral.py`, `brain_core/analysis/phase_locking.py`, `brain_core/analysis/signal_metrics.py`, `brain_core/physiology/eeg_forward_model.py`, `brain_core/physiology/bold_hrf.py`, `brain_core/physiology/neurovascular_coupling.py`, `tests/test_signal_metrics_modules.py`.

**Cel:** połączenie symulacji z sygnałami znanymi z praktyki badawczej.

**Zakres prac:**
- Spektralne wskaźniki EEG (pasma, synchronizacja, phase-locking).
- Uproszczone mapowanie aktywności na BOLD/HRF.
- Porównania między profilami.

**Deliverables:**
- Moduły analizy sygnałowej v1.
- Raporty z wykresami i interpretacją.

**Pozostały zakres:**
- Zintegrować raporty z wykresami i interpretacją dla EEG/BOLD.
- Rozszerzyć porównania między profilami.

---

### 10. Interfejs edukacyjny i „tryb nauczyciela”
**Status:** `partial`

**Artefakty implementacyjne:** `brain_model/gui.py`, `brain_model/gui_app.py`,
`brain_model/gui_layout.py`, `brain_model/gui_forms.py`, `brain_model/qt_app.py`,
`brain_model/qt_plotting.py`,
`docs/adr/0016-migracja-desktop-gui-na-pyside6.md`, `brain_viewer.html`,
`brain_viewer/brain_viewer.md`, `docs/index.html`.

**Cel:** zwiększenie dydaktyczności i użyteczności na zajęciach.

**Zakres prac:**
- Domknięcie migracji desktopowego GUI z `tkinter`/`TkAgg` na PySide6/Qt
  zgodnie z ADR-0016.
- Zachowanie kompatybilnego punktu wejścia `brain_model.gui:run_gui` dla
  użytkowników i skryptów.
- Aktualizacja testów statycznych GUI dla modułów PySide6 oraz backendu
  Matplotlib Qt.
- Panele „co obserwujesz teraz?” i „dlaczego to ważne?”.
- Oznaczenia regionów/neuromodulatorów na osi czasu.
- Gotowe scenariusze lekcyjne z pytaniami kontrolnymi.

**Deliverables:**
- Desktopowe GUI PySide6 v1 uruchamiane przez `brain_model.gui:run_gui`.
- Statyczne testy importów, punktu wejścia i panelu wykresów Qt.
- Widoki edukacyjne v1.
- Szablony lekcji laboratoryjnych.

**Pozostały zakres:**
- Domknąć migrację nowych przepływów desktopowych na PySide6 i nie rozwijać
  dalej ścieżki `tkinter` bez osobnej decyzji.
- Uzupełnić statyczne testy GUI o importy PySide6, punkt wejścia
  `brain_model.gui:run_gui` i backend wykresów Qt.
- Dodać tryb nauczyciela z pytaniami kontrolnymi i scenariuszami lekcyjnymi.
- Ujednolicić polskie etykiety pojęć z `docs/english_polish_glossary.md`.

---

## P3 — Długoterminowe inicjatywy

### 11. Hybrydy mikro-makro (spiking submodels)
**Status:** `partial`

**Cel:** powiązanie mechanizmów mikro z zachowaniem makro.

**Zakres prac:**
- Integracja 1–2 obwodów spiking (np. hipokamp, PFC-BG).
- Synchronizacja kroków czasowych z warstwą neural mass.
- Porównanie jakościowe efektów.

**Pozostały zakres:**
- Zintegrować konkretne obwody spiking z warstwą neural mass.
- Udokumentować synchronizację kroków czasowych i porównanie jakościowe efektów.

---

### 12. Personalizacja i cohort simulation
**Status:** `planned`

**Cel:** scenariusze quasi-kliniczne i międzyosobnicze.

**Zakres prac:**
- Parametry indywidualne (np. wiek, podatność stresowa, bazowe poziomy modulacji).
- Symulacje kohortowe i rozkłady wyników.
- Raport statystyczny porównań.

---

### 13. Walidacja literaturowa i benchmarki
**Status:** `partial`

**Cel:** systematyczne mapowanie modelu na znane efekty naukowe.

**Zakres prac:**
- Rejestr hipotez i benchmarków.
- Zautomatyzowane testy zgodności jakościowej.
- Raport wersyjny „co model odtwarza, czego jeszcze nie”.

**Pozostały zakres:**
- Rozbudować rejestr hipotez i benchmarków o jawne źródła oraz kryteria zgodności.
- Zautomatyzować raport wersyjny zgodności jakościowej.

---

## Sekcja techniczna backlogu (cross-cutting)

### A. Jakość i testy
**Status:** `partial`

- Testy jednostkowe dynamiki, walidacji configów i generatorów raportów.
- Testy integracyjne pipeline eksperymentów.
- Testy regresji dla profili healthy i disorder.

**Pozostały zakres:**
- Uzupełnić pokrycie testami regresji dla profili `healthy` i `disorder`.
- Ujednolicić testy integracyjne pipeline eksperymentów.

### B. Dane i wersjonowanie parametrów
**Status:** `partial`

- Wersjonowane zbiory parametrów i konektomów.
- Metadane źródła danych i zakresu stosowalności.

**Pozostały zakres:**
- Dodać spójne metadane źródeł i zakresów stosowalności dla wszystkich zestawów danych.
- Uporządkować wersjonowanie parametrów używanych w scenariuszach.

### C. Dokumentacja i ADR
**Status:** `partial`

- ADR obowiązkowe dla zmian strukturalnych.
- Instrukcje „jak uruchomić i jak interpretować” dla każdego scenariusza.

**Pozostały zakres:**
- Uzupełnić instrukcje uruchamiania i interpretacji dla każdego scenariusza.
- Pilnować ADR przy kolejnych zmianach strukturalnych.

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

---

## Zadanie jakościowe (uzupełniające)

### Q1. Utrzymanie standardu docstringów i type hints w całym repozytorium
**Status:** `done`

**Cel:** utrzymanie standardu dokumentacji i typowania dla wszystkich modułów Python.

**Kontekst (weryfikacja 2026-05-29):**
- Lokalny skan AST repozytorium zwrócił **0** braków docstringów.
- Lokalny skan AST repozytorium zwrócił **0** braków pełnych adnotacji typów.
- Historyczne dokumenty rollout/audit/progress zostały usunięte, ponieważ dublowały
  zamknięty zakres i nie zawierały już decyzji potrzebnych do dalszego rozwoju.

**Zakres utrzymaniowy:**
- Utrzymać docstringi dla wszystkich funkcji, klas i metod publicznych/prywatnych.
- Utrzymać type hints dla argumentów i typów zwracanych.
- Unikać nadmiarowego `Any` tam, gdzie możliwe jest wskazanie typu domenowego.
- Rozwijać kontrolę CI (lint/type check), jeśli projekt zacznie egzekwować jakość
  poza lokalnymi kontrolami opisanymi w `docs/developer_quality_checks.md`.

**Deliverables:**
- Aktualny standard w `docs/docstring_typing_standard.md`.
- Instrukcja kontroli jakości w `docs/developer_quality_checks.md`.

**Akceptacja:**
- Skan AST repozytorium zwraca brak braków docstringów i type hints.

**Pozostały zakres:**
- Brak znanych luk docstringów i adnotacji typów na dzień 2026-05-29.
- Opcjonalnie dodać kontrolę CI egzekwującą minimalny poziom pokrycia.
