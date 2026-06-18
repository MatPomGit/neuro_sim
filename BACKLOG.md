# BACKLOG — `neuro_sim`

Backlog jest uporządkowany według priorytetów (P0–P3) i gotowości wdrożeniowej.

- **P0** — krytyczne fundamenty produktu.
- **P1** — kluczowe rozszerzenia naukowe i dydaktyczne.
- **P2** — rozwój zaawansowany i jakościowy.
- **P3** — inicjatywy długoterminowe.

---

## Stan na dzień 2026-06-05

Backlog opisuje zarówno prace przyszłe, jak i obszary już częściowo zaimplementowane. Statusy oznaczają:
- `done` — zakres pozycji jest domknięty zgodnie z kryteriami akceptacji,
- `partial` — istnieją artefakty implementacyjne, ale pozostały elementy do ukończenia,
- `planned` — pozycja jest zaplanowana i nie ma jeszcze wystarczającej implementacji.

Najważniejsze istniejące fundamenty obejmują moduły eksperymentów, uszkodzeń i raportowania, m.in. `brain_core/experiments/protocols.py`, `brain_core/experiments/lesions.py` oraz `brain_core/analysis/reports.py`. Dla pozycji P0–P2 wskazano poniżej konkretne artefakty, aby oddzielić zakres już obecny w repozytorium od pozostałych prac.

Na dzień 2026-06-18 status nie jest prognozą wdrożenia, tylko krótką oceną rzeczywistego stanu repozytorium na podstawie powyższych definicji.

### Najbliższe krytyczne ryzyka

- **Kalibracja progów clinical profiles** — istnieją progi jakościowe, ale wymagają
  sprawdzenia względem benchmarków i scenariuszy `roving_oddball`.
- **Interpretacja benchmarków** — metadane benchmarków są dostępne, lecz nadal
  trzeba dopisać jawne kryteria zgodności i ograniczenia interpretacyjne.
- **Koszt `closed_loop` SNN** — wariant działa jako MVP, ale wymaga pomiaru
  kosztu względem `report_only` dla tych samych zadań, seedów i czasów symulacji.
- **Kompletność raportu trial-by-trial** — raporty i timeline istnieją częściowo,
  ale pełne grupowanie zdarzeń per trial pozostaje krytycznym brakiem dydaktycznym.

### Mapa artefaktów P0–P2

| Priorytet | Zakres | Status dominujący | Główne istniejące artefakty |
| --- | --- | --- | --- |
| P0 | Konfiguracja, timeline i baseline zdrowego mózgu | `partial` | `brain_core/simulation/config_loader.py`, `brain_core/simulation/config_schema.py`, `brain_core/simulation/events.py`, `brain_core/simulation/engine.py`, `brain_core/analysis/reports.py`, `brain_model/report_export.py`, `brain_model/model.py` |
| P1 | Konektom, neural mass, neuromodulacja i scenariusze porównawcze | `partial` | `brain_core/anatomy/connectome.py`, `brain_core/networks/delays.py`, `brain_core/populations/wilson_cowan.py`, `brain_core/experiments/pharmacology.py`, `brain_core/experiments/lesions.py` |
| P2 | Task battery, roving oddball, EEG/BOLD i tryb nauczyciela | `partial` / `planned` | `brain_core/experiments/protocols.py`, `brain_core/analysis/spectral.py`, `brain_core/physiology/eeg_forward_model.py`, `brain_model/qt_app.py`, `brain_model/qt_plotting.py` |


### Statusy funkcji przekrojowych w obecnej wersji

| Funkcja | Status | MVP istnieje | Pozostały zakres |
| --- | --- | --- | --- |
| `roving_oddball` | `partial` | Artefakty MVP istnieją w `brain_core/experiments/protocols.py`, `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml`, `configs/roving_oddball_lesion_hippocampus.yaml` i `docs/roving_oddball_guide.md`; obejmują generator sekwencji, aliasy taska, testy reprodukowalności i przewodnik dydaktyczny. | Walidacja metryk habituacji/readaptacji, porównanie profili healthy/disorder/lesion oraz raport amplitude-latency-mechanism. |
| Clinical profiles | `partial` | Katalog `configs/clinical_profiles/*.yaml`, integracja z `brain_core/simulation/config_schema.py`, raportowanie w `brain_core/analysis/reports.py`, lesion i scenariusze porównawcze; obejmuje progi jakościowe różnic i podstawowe komentarze dydaktyczne. | Walidacja profili względem benchmarków, kalibracja progów oraz raport specyficzny dla `roving_oddball` amplitude-latency-mechanism. |
| Timeline | `partial` | `event_timeline` w `brain_core/simulation/events.py` jest integrowany z silnikiem w `brain_core/simulation/engine.py` oraz raportami, a jego działanie weryfikują testy w `tests/test_task_protocols_and_engine.py`. | Jednolity format dla wszystkich symulacji, widok trial-by-trial, filtrowanie zdarzeń, grupowanie per trial, eksport HTML/PDF, linkowanie zdarzeń z wykresami i objaśnienia per profil kliniczny. |
| Benchmark metadata | `partial` | `data/validation/benchmark_metadata.json` oraz walidacja metadanych w `brain_core/analysis/benchmark_loader.py`. | Jawne kryteria zgodności dla każdego benchmarku, źródła literaturowe/empiryczne i raport wersyjny. |
| SNN demo | `partial` | `closed_loop` jest istniejącym MVP: `configs/snn_hippocampus_demo.yaml`, `brain_core/simulation/engine.py`, `brain_core/simulation/signal_adapter.py`, `brain_core/simulation/multiscale_engine.py` i opis demo. | Walidacja stabilności closed-loop, porównanie kosztu `report_only` vs `closed_loop`, pełniejszy backend biologiczny oraz integracja NEST/NEURON/Arbor. |
| GUI YAML presets | `partial` | Presety YAML oraz sześć kart lekcji są dostępne w GUI, mają polskie opisy i są sprawdzane przez testy statyczne. | Rozszerzanie katalogu wraz z nowymi zwalidowanymi scenariuszami i utrzymanie zgodności opisów z artefaktami raportu. |
| Przepływ dydaktyczny | `done` | Sześć kart YAML definiuje profil, task, checklistę, oczekiwany raport i kryteria oceny; tryb nauczyciela prowadzi przez etapy, a eksport zapisuje raporty, kartę pracy, metadane i wykresy. | Dalsza walidacja użyteczności i rozwój katalogu są usprawnieniami, nie brakami kryteriów BL-EDU-01–03. |
| Rejestr walidacji | `partial` | `docs/validation_registry.md`, `data/validation/benchmark_metadata.json` i loader benchmarków opisują podstawowe benchmarki edukacyjne. | Kryteria zgodności, źródła, poziomy walidacji i raport wersyjny jakościowej zgodności. |

### Najbliższe konkretne zadania do zaplanowania

| ID | Priorytet | Zadanie | Powiązane ryzyko | Akceptacja |
| --- | --- | --- | --- | --- |
| BL-ROV-01 | P0 | Uruchomić `roving_oddball` dla healthy/disorder/lesion na wspólnym seedzie i porównać habituację, readaptację, amplitudę oraz latencję. | Interpretacja benchmarków, kompletność raportu trial-by-trial | Raport porównawczy zawiera tabelę metryk i jawny komentarz amplitude-latency-mechanism. |
| BL-CLIN-01 | P0 | Skalibrować progi clinical profiles względem benchmarków i dopisać tolerancje oraz kierunek oczekiwanej zmiany. | Kalibracja progów clinical profiles | Każdy próg ma źródło, tolerancję, zakres stosowalności i test regresji albo jawne uzasadnienie braku testu; każdy profil clinical ma `expected_direction`, `primary_metric`, `severity_level` i komentarz w raporcie porównawczym. |
| BL-TL-01 | P0 | Rozszerzyć timeline o grupowanie trial-by-trial i powiązania z wykresami. | Kompletność raportu trial-by-trial | Raport dla `roving_oddball` pokazuje numer triala, typ bodźca, odpowiedź, metryki i komentarz mechanizmu. |
| BL-SNN-01 | P1 | Zmierzyć koszt `report_only` vs `closed_loop` SNN dla tej samej konfiguracji, seeda i czasu symulacji. | Koszt `closed_loop` SNN | Raport zawiera czas wykonania, długości sygnałów, amplitudę feedbacku i rekomendację, czy wariant nadaje się do GUI. |
| BL-GUI-01 | P1 | **Zrealizowane (MVP):** dydaktyczne opisy presetów i kart lekcji są wczytywane z `configs/lessons/*.yaml`. | Interpretacja benchmarków, koszt `closed_loop` SNN | Utrzymywać polskie opisy celu, oczekiwanych obserwacji, ograniczeń i ścieżki konfiguracji bez duplikowania logiki silnika. |
| BL-EDU-01 | P1 | **Zrealizowane:** katalog obejmuje sześć lekcji z celem, czasem, poziomem, profilem, taskiem, oczekiwanym raportem, pytaniami i kryteriami oceny. | Gotowość aplikacji do zajęć | Kryteria akceptacji spełnione; nowe lekcje walidować według `docs/lesson_catalog_guidelines.md`. |
| BL-EDU-02 | P1 | **Zrealizowane:** tryb nauczyciela pokazuje checklistę, hipotezę, uruchomienie, obserwacje, raport, interpretację, ograniczenia, kryteria oceny i odnośnik do porównania. | Kompletność raportu trial-by-trial, interpretacja benchmarków | Kryteria akceptacji spełnione; pełniejsze linkowanie pojedynczych triali pozostaje w BL-TL-01. |
| BL-EDU-03 | P2 | **Zrealizowane:** pakiet zawiera raport HTML/PDF, konfigurację, seed, Git, środowisko, metryki, wykresy PNG, komentarze, pytania, plan, skrót i kartę pracy. | Replikowalność zajęć | Kryteria akceptacji spełnione; dalsze warianty materiałów mogą być rozwijane niezależnie. |
| BL-VAL-01 | P1 | Uzupełnić rejestr walidacji o kryteria zgodności, źródła i poziomy walidacji per benchmark. | Interpretacja benchmarków | Rejestr wskazuje efekty odtworzone jakościowo, częściowo odtworzone i pozostające poza zakresem. |

### Plan najbliższej iteracji

Poniższy plan porządkuje najbliższą iterację bez zmiany istniejących statusów
backlogu. Kolejność najpierw domyka fundament raportowania i porównań P0, a
następnie uzupełnia walidację, GUI oraz zakres dydaktyczny P1/P2.

#### 1. P0: `BL-TL-01` — trial-by-trial timeline dla `roving_oddball`

- **Cel:** rozszerzyć raport timeline tak, aby użytkownik widział przebieg
  `roving_oddball` per trial: numer triala, typ bodźca, odpowiedź, metryki i
  komentarz mechanizmu.
- **Zależności:** istniejący `event_timeline`, generator protokołu
  `roving_oddball`, raporty analityczne oraz eksport raportów; brak zależności
  od kalibracji progów klinicznych.
- **Główne pliki:** `brain_core/simulation/events.py`,
  `brain_core/simulation/engine.py`, `brain_core/analysis/reports.py`,
  `brain_model/report_export.py`, `tests/test_task_protocols_and_engine.py`,
  `tests/test_observation_and_analysis.py`.
- **Kryterium akceptacji:** raport dla `roving_oddball` grupuje zdarzenia per
  trial i pokazuje standard, deviant, nowy standard, odpowiedź, metryki oraz
  komentarz mechanizmu profilu w jednej osi czasu.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_task_protocols_and_engine.py
  tests/test_observation_and_analysis.py`.

#### 2. P0: `BL-ROV-01` — porównanie healthy/disorder/lesion na wspólnym seedzie

- **Cel:** uruchomić i opisać porównanie profili healthy, disorder i lesion dla
  `roving_oddball` na tym samym seedzie, z metrykami habituacji, readaptacji,
  amplitudy i latencji.
- **Zależności:** trial-by-trial timeline z `BL-TL-01`, konfiguracje
  `roving_oddball_*`, metryki analityczne oraz raport porównawczy.
- **Główne pliki:** `configs/roving_oddball_healthy.yaml`,
  `configs/roving_oddball_disorder_gaba.yaml`,
  `configs/roving_oddball_lesion_hippocampus.yaml`,
  `brain_core/experiments/protocols.py`, `brain_core/analysis/reports.py`,
  `docs/roving_oddball_guide.md`, `tests/test_task_protocols_and_engine.py`.
- **Kryterium akceptacji:** raport porównawczy zawiera tabelę metryk dla trzech
  profili, jawny wspólny seed i komentarz amplitude-latency-mechanism bez
  sugerowania interpretacji diagnostycznej.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_task_protocols_and_engine.py` oraz
  kontrolne uruchomienie scenariuszy `roving_oddball` na wspólnym seedzie.

#### 3. P0: `BL-CLIN-01` — kalibracja progów profili klinicznych względem benchmarków

- **Cel:** doprecyzować progi clinical profiles względem benchmarków, tolerancje,
  kierunek oczekiwanej zmiany i zakres stosowalności.
- **Zależności:** wyniki porównania `BL-ROV-01`, metadane benchmarków oraz
  rejestr walidacji; zależność logiczna od wspólnego sposobu raportowania
  metryk.
- **Główne pliki:** `configs/clinical_profiles/*.yaml`,
  `data/validation/benchmark_metadata.json`,
  `brain_core/analysis/benchmark_loader.py`, `brain_core/analysis/reports.py`,
  `brain_core/simulation/config_schema.py`, `tests/test_observation_and_analysis.py`.
- **Kryterium akceptacji:** każdy próg ma źródło, tolerancję, zakres
  stosowalności i test regresji albo jawne uzasadnienie braku testu; każdy profil
  clinical ma `expected_direction`, `primary_metric`, `severity_level` i komentarz
  w raporcie porównawczym.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_observation_and_analysis.py` oraz testy
  walidacji konfiguracji profili klinicznych.

#### 4. P1: `BL-VAL-01` — uzupełnienie rejestru walidacji o kryteria zgodności

- **Cel:** opisać kryteria zgodności, źródła i poziomy walidacji per benchmark,
  aby interpretacja wyników była jawna i wersjonowalna.
- **Zależności:** benchmark metadata, kalibracja progów z `BL-CLIN-01` oraz
  ograniczenia interpretacyjne scenariuszy `roving_oddball`.
- **Główne pliki:** `docs/validation_registry.md`,
  `data/validation/benchmark_metadata.json`,
  `brain_core/analysis/benchmark_loader.py`, `tests/test_observation_and_analysis.py`.
- **Kryterium akceptacji:** rejestr wskazuje efekty odtworzone jakościowo,
  częściowo odtworzone i pozostające poza zakresem, wraz z kryteriami zgodności
  oraz źródłami.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_observation_and_analysis.py` oraz
  kontrola spójności pól benchmark metadata z rejestrem walidacji.

#### 5. P1: `BL-GUI-01` — polskie opisy presetów YAML w GUI

- **Cel:** dodać polskie, dydaktyczne opisy presetów YAML dla `roving_oddball` i
  `snn_hippocampus_demo` bez duplikowania logiki silnika.
- **Zależności:** ustalone ograniczenia interpretacyjne z `BL-VAL-01`, słownik
  pojęć EN→PL oraz istniejąca lista presetów w GUI PySide6.
- **Główne pliki:** `brain_model/qt_app.py`, `brain_model/qt_sections.py`,
  `brain_model/qt_config.py`, `brain_model/qt_plotting.py`,
  `docs/english_polish_glossary.md`, `configs/roving_oddball_healthy.yaml`,
  `configs/snn_hippocampus_demo.yaml`, `tests/test_qt_config.py`,
  `tests/test_qt_sections.py`, `tests/test_gui_dependencies_static.py`.
- **Kryterium akceptacji:** użytkownik widzi polski opis celu, oczekiwanego
  efektu, ograniczeń i link do konfiguracji dla każdego presetu.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_qt_config.py tests/test_qt_sections.py
  tests/test_gui_dependencies_static.py` oraz statyczna kontrola braku nowych
  przepływów `tkinter`.

#### 6. P1: `BL-EDU-01` i `BL-EDU-02` — katalog lekcji oraz tryb nauczyciela

- **Cel:** przygotować katalog lekcji i prowadzenie użytkownika przez hipotezę,
  uruchomienie, obserwację metryk oraz interpretację ograniczeń.
- **Zależności:** przed pełną implementacją trybu nauczyciela muszą być
  spełnione `BL-TL-01` (raport trial-by-trial dla `roving_oddball`),
  `BL-ROV-01` (porównanie healthy/disorder/lesion na wspólnym seedzie),
  `BL-CLIN-01` (skalibrowane progi clinical profiles) i `BL-VAL-01`
  (rejestr walidacji z kryteriami zgodności); dodatkowo wymagane są polskie
  opisy presetów YAML.
- **Główne pliki:** `brain_model/qt_app.py`, `brain_model/qt_results.py`,
  `brain_model/qt_sections.py`, `brain_model/qt_state.py`,
  `brain_model/qt_config.py`,
  `docs/english_polish_glossary.md`, `docs/roving_oddball_guide.md`,
  `configs/*.yaml`, `tests/test_qt_sections.py`, `tests/test_gui_state.py`,
  `tests/test_qt_profile_comparison_static.py`.
- **Kryterium akceptacji:** co najmniej 3 scenariusze mają kartę lekcji,
  konfigurację YAML, oczekiwane obserwacje, pytania kontrolne i kryteria oceny;
  widok nauczyciela pokazuje checklistę, komentarze per etap, ostrzeżenie przed
  interpretacją diagnostyczną i link do raportu porównawczego; widoki i eksport
  przedstawiają metryki wyłącznie jako dydaktyczną interpretację modelu, nie
  jako diagnozę kliniczną; nowe panele wynikowe korzystają ze wspólnego tekstu
  ograniczenia z `EDUCATIONAL_LIMITATION_TEXT_PL`, bez lokalnych wariantów.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_qt_sections.py tests/test_gui_state.py
  tests/test_gui_layout_static.py` oraz kontrola zgodności pojęć z glosariuszem.

#### 7. P2: `BL-EDU-03` — eksport pakietu dydaktycznego

- **Cel:** umożliwić eksport kompletnego pakietu zajęciowego: raportu HTML/PDF,
  skrótu dla prowadzącego, karty pracy studenta i metadanych konfiguracji.
- **Zależności:** katalog lekcji i tryb nauczyciela z `BL-EDU-01`/`BL-EDU-02`,
  a przed pełną implementacją trybu nauczyciela także `BL-TL-01`, `BL-ROV-01`,
  `BL-CLIN-01` i `BL-VAL-01`; wymagane są raport porównawczy, timeline
  trial-by-trial oraz mechanizm eksportu raportów.
- **Główne pliki:** `brain_model/report_export.py`, `brain_core/analysis/reports.py`,
  `brain_model/qt_sections.py`, `brain_model/qt_app.py`,
  `docs/roving_oddball_guide.md`, `tests/test_observation_and_analysis.py`,
  `tests/test_qt_sections.py`.
- **Kryterium akceptacji:** eksport zawiera konfigurację, seed, wersję kodu,
  metryki, wykresy, komentarze dydaktyczne i pytania kontrolne bez ręcznego
  kopiowania z GUI; eksport nie przedstawia metryk jako diagnozy klinicznej,
  tylko jako dydaktyczną interpretację modelu.
- **Minimalny zestaw testów lub kontroli statycznych:** `ruff check .`,
  `black --check .`, `pytest tests/test_observation_and_analysis.py
  tests/test_qt_sections.py` oraz kontrola kompletności metadanych eksportu.

### Zrealizowane milestone’y

Poniższe pozycje opisują funkcje ukończone lub częściowo ukończone na
poziomie MVP. Nie oznacza to pełnej realizacji architektury docelowej z
długoterminowej sekcji biologicznej backlogu; każda pozycja ma jawne pole **Pozostałe ograniczenia**, aby
odróżnić działający artefakt od kompletnego zakresu badawczego.

| Milestone | Status | Główne pliki | Testy | Pozostałe ograniczenia |
| --- | --- | --- | --- | --- |
| Taski poznawcze `stroop`, `go_nogo`, `n_back`, `roving_oddball` | `partial` | [`brain_core/experiments/protocols.py`](brain_core/experiments/protocols.py), [`brain_model/stimuli.py`](brain_model/stimuli.py), [`configs/stroop.yaml`](configs/stroop.yaml), [`configs/go_nogo.yaml`](configs/go_nogo.yaml), [`configs/n_back.yaml`](configs/n_back.yaml), [`configs/roving_oddball_healthy.yaml`](configs/roving_oddball_healthy.yaml), [`configs/roving_oddball_disorder_gaba.yaml`](configs/roving_oddball_disorder_gaba.yaml), [`configs/roving_oddball_lesion_hippocampus.yaml`](configs/roving_oddball_lesion_hippocampus.yaml) | [`tests/test_task_protocols_and_engine.py`](tests/test_task_protocols_and_engine.py), [`tests/test_task_stimulus_player.py`](tests/test_task_stimulus_player.py) | Dostępne są podstawowe protokoły, konfiguracje demonstracyjne i przewodnik dydaktyczny `roving_oddball`; dalszy zakres obejmuje walidację metryk habituacji/readaptacji, porównanie profili healthy/disorder/lesion oraz raport amplitude-latency-mechanism. |
| Moduł uszkodzeń `lesions.py` | `partial` | [`brain_core/experiments/lesions.py`](brain_core/experiments/lesions.py), [`brain_model/scenarios/library.py`](brain_model/scenarios/library.py), [`brain_model/scenarios/types.py`](brain_model/scenarios/types.py) | [`tests/test_lesions.py`](tests/test_lesions.py), [`tests/test_task_protocols_and_engine.py`](tests/test_task_protocols_and_engine.py) | Obecny zakres wspiera scenariusze ogniskowe/sieciowe i integrację z taskami, ale katalog profili klinicznych, interpretacje dydaktyczne oraz raport różnic region-czas-funkcja pozostają niepełne. |
| Raport benchmarkowy | `partial` | [`brain_core/analysis/reports.py`](brain_core/analysis/reports.py), [`brain_core/analysis/benchmark_loader.py`](brain_core/analysis/benchmark_loader.py), [`brain_core/simulation/engine.py`](brain_core/simulation/engine.py), [`data/validation/eeg_target.csv`](data/validation/eeg_target.csv), [`data/validation/fmri_target.csv`](data/validation/fmri_target.csv), [`data/validation/behavior_target.csv`](data/validation/behavior_target.csv) | [`tests/test_observation_and_analysis.py`](tests/test_observation_and_analysis.py), [`tests/test_signal_metrics_modules.py`](tests/test_signal_metrics_modules.py) | Raport potrafi agregować metryki i porównania referencyjne, ale nie zastępuje pełnego raportu dydaktycznego z kompletną osią trial-by-trial, wykresami i interpretacją profili z długoterminowej sekcji biologicznej backlogu. |
| Metryki analityczne EEG/BOLD/zachowanie | `partial` | [`brain_core/analysis/signal_metrics.py`](brain_core/analysis/signal_metrics.py), [`brain_core/analysis/spectral.py`](brain_core/analysis/spectral.py), [`brain_core/analysis/phase_locking.py`](brain_core/analysis/phase_locking.py), [`brain_core/analysis/connectivity.py`](brain_core/analysis/connectivity.py), [`brain_core/analysis/information_flow.py`](brain_core/analysis/information_flow.py), [`brain_core/physiology/eeg_forward_model.py`](brain_core/physiology/eeg_forward_model.py), [`brain_core/physiology/bold_hrf.py`](brain_core/physiology/bold_hrf.py), [`brain_core/physiology/neurovascular_coupling.py`](brain_core/physiology/neurovascular_coupling.py) | [`tests/test_signal_metrics_modules.py`](tests/test_signal_metrics_modules.py), [`tests/test_observation_and_analysis.py`](tests/test_observation_and_analysis.py) | Dostępne są metryki sygnałowe i fasada kompatybilności, ale integracja z raportami EEG/BOLD, wykresami, progami jakości i porównaniami wielu profili nadal wymaga domknięcia. |
| SNN signal adapter i kontrakt NM↔SNN | `partial` | [`brain_core/simulation/signal_adapter.py`](brain_core/simulation/signal_adapter.py), [`brain_core/populations/spiking_population.py`](brain_core/populations/spiking_population.py), [`brain_core/simulation/multiscale_engine.py`](brain_core/simulation/multiscale_engine.py) | [`tests/test_spiking_population_adapter.py`](tests/test_spiking_population_adapter.py), [`tests/test_multiscale_engine.py`](tests/test_multiscale_engine.py) | Adapter definiuje kontrakt sygnałów i pilotażową wymianę neural-mass ↔ SNN, ale backend jest startową aproksymacją; pełne obwody SNN, większe sieci i backendy typu NEST/NEURON pozostają zakresem docelowym. |
| GUI state | `partial` | [`brain_model/gui_state.py`](brain_model/gui_state.py), [`brain_model/gui_layout.py`](brain_model/gui_layout.py), [`brain_model/qt_state.py`](brain_model/qt_state.py), [`brain_model/qt_app.py`](brain_model/qt_app.py), [`brain_model/qt_sections.py`](brain_model/qt_sections.py), [`brain_model/qt_config.py`](brain_model/qt_config.py) | [`tests/test_gui_state.py`](tests/test_gui_state.py), [`tests/test_gui_layout_static.py`](tests/test_gui_layout_static.py), [`tests/test_qt_config.py`](tests/test_qt_config.py), [`tests/test_qt_sections.py`](tests/test_qt_sections.py), [`tests/test_gui_dependencies_static.py`](tests/test_gui_dependencies_static.py) | Stan GUI jest wydzielony i testowany statycznie dla głównych przepływów, ale migracja wszystkich nowych przepływów na PySide6, tryb nauczyciela i pełna zgodność etykiet z glosariuszem pozostają częściowe. |

### Najbliższe zaplanowane prace

Poniższa lista zbiera komplet najbliższych prac planowanych na bazie aktualnego stanu repozytorium. Kolejność odzwierciedla zależności: najpierw domknięcie fundamentów P0, potem elementy P1/P2 potrzebne do scenariuszy dydaktycznych i porównawczych.

1. **Domknięcie konfiguracji eksperymentów P0** — Status: `partial`. ujednolicić YAML/JSON wokół istniejących `ExperimentConfig`, `config_loader` i konfiguracji `configs/*.yaml`; dodać czytelne błędy walidacji oraz testy dla sekcji `stimulus`, `brain_profile`, `connectome`, `rng_seed`, `analysis`.
2. **Oś czasu i raport dydaktyczny P0** — Status: `partial`. rozwinąć raportowanie z `brain_core/analysis/reports.py` i `brain_model/report_export.py` o spójny log zdarzeń, pełną oś trial-by-trial i słownik pojęć dla użytkownika.
3. **Baseline `healthy_v1` P0** — Status: `partial`. sformalizować profil zdrowy jako wersjonowany artefakt, dodać dokumentację, referencyjne wykresy i progi regresji dla wyników baseline.
4. **Konektom z opóźnieniami P1** — Status: `partial`. potwierdzić co najmniej dwa eksperymenty oparte na `brain_core/anatomy/*`, `brain_core/networks/*` i danych `data/connectomes/*`; uzupełnić mapowanie poznawcze regionów.
5. **Stabilizacja neural mass P1** — Status: `partial`. zweryfikować scenariusze >50 regionów dla `brain_core/populations/wilson_cowan.py`, doprecyzować zakresy parametrów i sanity checks.
6. **Neuromodulacja P1** — Status: `partial`. domknąć spójne API profili DA/5-HT/ACh/NA/GABA/glutaminian oraz dodać raport pre/post pokazujący różnice czasowo-przestrzenne.
7. **Scenariusze healthy/disorder/lesion P1** — Status: `partial`. istniejący katalog profili klinicznych i uszkodzeń zawiera progi jakościowe różnic oraz podstawowe komentarze dydaktyczne; priorytetem pozostaje walidacja profili względem benchmarków, kalibracja progów i raport specyficzny dla `roving_oddball` amplitude-latency-mechanism.
8. **Biblioteka tasków P2** — Status: `partial`. ujednolicić istniejące protokoły `stroop`, `go_nogo`, `n_back` i API w `brain_core/experiments/protocols.py`; przygotować wspólne szablony raportów per task.
9. **Roving oddball P2** — Status: `partial`. istniejący pakiet MVP obejmuje generator sekwencji, konfiguracje healthy/disorder/lesion, testy reprodukowalności i przewodnik dydaktyczny; priorytetem pozostaje walidacja metryk habituacji/readaptacji, porównanie profili healthy/disorder/lesion oraz raport amplitude-latency-mechanism.
10. **Raporty EEG/BOLD P2** — Status: `partial`. połączyć metryki z `brain_core/analysis/*` i `brain_core/physiology/*` w raportach z wykresami, interpretacją i porównaniem profili.
11. **Migracja desktopowego GUI na PySide6 P2** — Status: `partial`. domknąć przejście nowych
    przepływów desktopowych z `tkinter`/`TkAgg` na PySide6/Qt, zachowując
    kompatybilny punkt wejścia `brain_model.gui:run_gui` zgodnie z ADR-0016.
12. **Tryb nauczyciela P2** — Status: `done`. Widoki edukacyjne zawierają
    checklistę, pytania, oczekiwany raport, kryteria oceny, odnośnik do
    porównania oraz wspólne ograniczenie interpretacyjne.
13. **Profesjonalizacja aplikacji dydaktycznej P1/P2** — Status: `done`.
    Katalog sześciu lekcji i eksport pakietu z raportami, kartą pracy,
    metadanymi oraz osobnymi wykresami spełniają kryteria BL-EDU-01–03.
14. **Jakość i dokumentacja przekrojowa** — Status: `partial`. utrzymać standard docstringów/type hints,
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

**Artefakty implementacyjne:** `brain_core/simulation/events.py`, `brain_core/simulation/engine.py`, `brain_core/analysis/reports.py`, `brain_model/report.py`, `brain_model/report_export.py`, `tests/test_observation_and_analysis.py`, `tests/test_task_protocols_and_engine.py`.

**Cel:** student rozumie „co, kiedy i dlaczego” wydarzyło się w modelu.

**MVP istnieje:**
- MVP `event_timeline` istnieje w `brain_core/simulation/events.py` i jest
  integrowane z silnikiem symulacji w `brain_core/simulation/engine.py`;
  podstawowe testy timeline są ujęte w `tests/test_task_protocols_and_engine.py`.

**Zakres prac:**
- Event bus dla kluczowych zdarzeń (bodziec, zmiana aktywacji regionu, modulacja neurochemiczna).
- Generator raportu krokowego z osią czasu.
- Słownik pojęć (np. co oznacza wzrost theta, spadek gatingu itd.).

**Deliverables:**
- Format logu zdarzeń.
- Raport `.md`/`.html` generowany po każdej symulacji.

**Akceptacja:**
- Raport umożliwia odtworzenie przebiegu eksperymentu bez zaglądania do kodu.
- Raport dla `roving_oddball` pokazuje standard, deviant, nowy standard,
  odpowiedź i mechanizm profilu klinicznego w jednej osi czasu.

**Pozostały zakres:**
- Ujednolicić format logu zdarzeń dla wszystkich typów symulacji.
- Rozszerzyć raport timeline o filtrowanie zdarzeń, grupowanie per trial,
  eksport HTML/PDF, linkowanie zdarzeń z wykresami oraz objaśnienia per profil
  kliniczny.

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

**Artefakty implementacyjne:** `configs/clinical_profiles/*.yaml`, `brain_core/simulation/config_schema.py`, `brain_core/analysis/reports.py`, `brain_core/simulation/engine.py`, `brain_core/experiments/lesions.py`, `brain_model/scenarios/library.py`, `brain_model/scenarios/types.py`, `tests/test_lesions.py`, `tests/test_task_protocols_and_engine.py`.

**Artefakty MVP profili klinicznych:**
- `configs/clinical_profiles/*.yaml` — wersjonowane profile kliniczne.
- `brain_core/simulation/config_schema.py` — schemat i integracja profilu klinicznego w konfiguracji.
- `brain_core/analysis/reports.py` — komentarze dydaktyczne i raport porównawczy.

**Cel:** realizacja kluczowej wartości edukacyjnej i psychiatrycznej.

**MVP istnieje:**
- Katalog `configs/clinical_profiles/*.yaml` zawiera profile healthy, disorder i lesion.
- `brain_core/simulation/config_schema.py` i `brain_core/simulation/engine.py` obsługują profil kliniczny w konfiguracji.
- `brain_core/experiments/lesions.py` oraz `brain_model/scenarios/` wspierają scenariusze porównawcze na poziomie MVP.
- `brain_core/analysis/reports.py` wspiera podstawowe komentarze dydaktyczne w raporcie porównawczym.
- Profile zawierają progi jakościowe różnic potrzebne do interpretacji wyników porównawczych.
- Podstawowe komentarze dydaktyczne i progi jakościowe różnic są traktowane jako istniejący zakres MVP, a nie jako pozostała praca.

**Zakres prac:**
- Utrzymać istniejące profile zaburzeń i lesion jako wersjonowane artefakty MVP.
- Uruchamiać ten sam bodziec na wielu profilach bez zmiany konfiguracji bazowej poza jawnie wskazanym profilem.
- Rozwijać raport porównawczy wyłącznie o brakujące elementy walidacyjne i task-specific.

**Deliverables / artefakty:**
- `configs/clinical_profiles/*.yaml` — katalog profili klinicznych v1.
- `brain_core/simulation/config_schema.py` — schemat pól profilu clinical w konfiguracji.
- `brain_core/analysis/reports.py` — automatyczny raport różnic, komentarze dydaktyczne i porównanie region-czas-funkcja.

**Istniejące profile:**
- `healthy_v1`
- `dopamine_deficit`
- `gaba_dysregulation`
- `serotonin_imbalance`
- `hippocampal_lesion`
- `dlpfc_weakening`

**Akceptacja:**
- Co najmniej 3 profile kliniczne + 2 typy lesion, każdy z interpretacją dydaktyczną.
- Każdy profil clinical ma `expected_direction`, `primary_metric`, `severity_level` i komentarz w raporcie porównawczym.

**Pozostały zakres:**
- Zweryfikować profile względem benchmarków.
- Skalibrować progi jakościowe różnic względem wyników referencyjnych.
- Dodać raport specyficzny dla `roving_oddball` amplitude-latency-mechanism.

---

## P2 — Rozwój zaawansowany

### 8. Zestaw zadań poznawczych (task battery)
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/experiments/protocols.py`, `brain_model/stimuli.py`, `configs/stroop.yaml`, `configs/go_nogo.yaml`, `configs/n_back.yaml`, `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml`, `configs/roving_oddball_lesion_hippocampus.yaml`, `tests/test_task_protocols_and_engine.py`, `tests/test_task_stimulus_player.py`.

**Cel:** standaryzacja eksperymentów poznawczych.

**Zakres prac:**
- Zadania uwagowe, pamięciowe, decyzyjne, emocjonalne.
- Parametryzacja trudności i rodzaju bodźca.
- Metryki behawioralne i neuronalne.
- Dalsza walidacja istniejących artefaktów MVP `roving_oddball`: metryki habituacji/readaptacji, porównanie profili healthy/disorder/lesion oraz raport amplitude-latency-mechanism.

**Deliverables:**
- Biblioteka tasków v1.
- Szablony raportów per task.

**Pozostały zakres:**
- Ujednolicić bibliotekę tasków v1 oraz szablony raportów per task.
- Uzupełnić istniejący pakiet `roving_oddball` o walidację metryk habituacji/readaptacji, porównanie profili healthy/disorder/lesion oraz raport amplitude-latency-mechanism.

---

### 8A. Rozwój i dokumentacja roving oddball task (priorytet P1/P2)
**Status:** `partial`

**Artefakty implementacyjne:** `brain_core/experiments/protocols.py`, `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml`, `configs/roving_oddball_lesion_hippocampus.yaml`, `docs/roving_oddball_guide.md`, `tests/test_task_protocols_and_engine.py`.

**Cel:** utrzymanie istniejącego zadania referencyjnego do testów predykcji, nowości i adaptacji oraz domknięcie walidacji porównań profili.

**MVP istnieje:**
- Generator sekwencji bodźców z parametrami:
  - `n_runs`, `run_length_min/max`,
  - `stimulus_family`, `deviant_probability`,
  - `inter_stimulus_interval`, `jitter`.
- Aliasy taska dla `roving_oddball`.
- Konfiguracje eksperymentu:
  - `configs/roving_oddball_healthy.yaml`,
  - `configs/roving_oddball_disorder_gaba.yaml`,
  - `configs/roving_oddball_lesion_hippocampus.yaml`.
- Podstawowe metryki:
  - `surprise_index`,
  - `habituation_level`,
  - `readaptation_latency`.
- Testy reprodukowalności sekwencji i ładowania konfiguracji scenariuszy.
- Przewodnik dydaktyczny `docs/roving_oddball_guide.md`: „Roving Oddball — od bodźca do interpretacji”.

**Pozostały zakres:**
- Walidacja metryk habituacji/readaptacji.
- Porównanie profili healthy/disorder/lesion.
- Raport amplitude-latency-mechanism.

**Deliverables do uzupełnienia:**
- Testy regresji zwalidowanych metryk habituacji/readaptacji.
- Raport z porównania profili healthy/disorder/lesion.
- Raport amplitude-latency-mechanism.

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
- Katalog lekcji dla prowadzącego: cel, czas trwania, poziom trudności,
  wymagane konfiguracje, oczekiwane obserwacje i pytania kontrolne.
- Prowadzenie krok po kroku: hipoteza → konfiguracja → uruchomienie → metryki
  → interpretacja → ograniczenia modelu.
- Eksport pakietu zajęciowego: raport HTML/PDF, karta pracy studenta, skrót dla
  prowadzącego, konfiguracja, seed i metadane uruchomienia.
- Mechanizmy bezpieczeństwa dydaktycznego: komunikaty, że profile clinical są
  modelami edukacyjnymi i nie stanowią predykcji diagnostycznej.
- Podstawy profesjonalnej dostępności i użyteczności: spójna nawigacja,
  czytelne stany błędów, kontrast, opisy wykresów i powtarzalne układy ekranów.

**Deliverables:**
- Desktopowe GUI PySide6 v1 uruchamiane przez `brain_model.gui:run_gui`.
- Statyczne testy importów, punktu wejścia i panelu wykresów Qt.
- Widoki edukacyjne v1.
- Szablony lekcji laboratoryjnych.
- Katalog scenariuszy dydaktycznych v1 dla `healthy_v1`, `roving_oddball`,
  `gaba_dysregulation`, `dopamine_deficit` i scenariusza lesion.
- Eksportowalny pakiet zajęciowy z raportem, kartą pracy i metadanymi
  reprodukowalności.
- Lista kontrolna prowadzącego oraz rubryka oceny odpowiedzi studenta.

**Akceptacja profesjonalnej aplikacji dydaktycznej:**
- Prowadzący może uruchomić gotową lekcję bez edycji kodu i otrzymuje pełny
  pakiet materiałów do zajęć.
- Student widzi w jednym miejscu bodziec, metrykę, wykres, komentarz mechanizmu
  i ograniczenia interpretacyjne.
- Eksport lekcji zawiera konfigurację, seed, wersję kodu, metryki i komentarze
  wystarczające do powtórzenia demonstracji.
- GUI nie powiela logiki walidacji silnika; błędy konfiguracji są pokazane po
  polsku i wskazują konkretne pole lub sekcję.

**Pozostały zakres:**
- Domknąć migrację nowych przepływów desktopowych na PySide6 i nie rozwijać
  dalej ścieżki `tkinter` bez osobnej decyzji.
- Uzupełnić statyczne testy GUI o importy PySide6, punkt wejścia
  `brain_model.gui:run_gui` i backend wykresów Qt.
- Dodać tryb nauczyciela z pytaniami kontrolnymi i scenariuszami lekcyjnymi.
- Zbudować katalog lekcji, eksport pakietów zajęciowych i rubrykę oceny.
- Ujednolicić polskie etykiety pojęć z `docs/english_polish_glossary.md`.

---

## P3 — Długoterminowe inicjatywy

### 11. Hybrydy mikro-makro (spiking submodels)
**Status:** `partial`

**Cel:** powiązanie mechanizmów mikro z zachowaniem makro.

**MVP istnieje:** istnieje pilotaż `snn_hippocampus_demo` z jednym
obwodem HIP; tryb `closed_loop` jest działającym MVP obok wariantu
`report_only`. Raport `snn_comparison` dokumentuje kontrakt wymiany sygnałów,
tryb żądany oraz faktycznie policzone warianty porównawcze.

**Artefakty implementacyjne:**
- [`configs/snn_hippocampus_demo.yaml`](configs/snn_hippocampus_demo.yaml)
- [`docs/snn_cosimulation_demo.md`](docs/snn_cosimulation_demo.md)
- [`brain_core/simulation/engine.py`](brain_core/simulation/engine.py)
- [`brain_core/simulation/signal_adapter.py`](brain_core/simulation/signal_adapter.py)
- [`brain_core/simulation/multiscale_engine.py`](brain_core/simulation/multiscale_engine.py)
- [`brain_core/analysis/reports.py`](brain_core/analysis/reports.py)

**Zakres prac:**
- Walidacja stabilności wariantu `closed_loop` w dłuższych i bardziej
  zróżnicowanych scenariuszach.
- Porównanie kosztu obliczeniowego `report_only` vs `closed_loop`.
- Pełniejszy backend biologiczny oraz integracja NEST/NEURON/Arbor.

**Akceptacja:**
- Raport pokazuje osobno baseline, report-only SNN i closed-loop SNN wraz z
  długościami sygnałów i amplitudą feedbacku.

**Pozostały zakres:**
- Zweryfikować stabilność `closed_loop` w dłuższych scenariuszach i przy
  różnych profilach klinicznych.
- Porównać koszt obliczeniowy `report_only` vs `closed_loop` na tym samym
  zadaniu, ziarnie i czasie symulacji.
- Rozwinąć pełniejszy backend biologiczny oraz integrację NEST, NEURON/PyNE i
  Arbor dla większych modeli.

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

**MVP istnieje:**
- `data/validation/benchmark_metadata.json` opisuje źródło, zakres, ograniczenia i poziom walidacji dla benchmarków EEG, fMRI i zachowania.
- `brain_core/analysis/benchmark_loader.py` waliduje kompletność metadanych i ładuje je razem z danymi referencyjnymi.

**Zakres prac:**
- Rejestr hipotez i benchmarków z poziomami walidacji: `synthetic`, `educational`, `literature-inspired`, `empirical`.
- Zautomatyzowane testy zgodności jakościowej.
- Raport wersyjny „co model odtwarza, czego jeszcze nie”.

**Pozostały zakres:**
- Rozbudować rejestr hipotez i benchmarków o jawne źródła oraz kryteria zgodności.
- Każdy benchmark musi mieć metadane, kryterium zgodności i informację, czy jest
  edukacyjny, literaturowy czy empiryczny.
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

### D. GUI: modularizacja, stan i walidacja formularzy
**Status:** `planned`

**Powiązane ADR:** ADR-0012, ADR-0013.

**Cel:** domknięcie długu technicznego desktopowego GUI po modularizacji oraz
ujednolicenie jawnego stanu formularzy i walidacji danych wejściowych.

**Zakres prac:**
- Przejrzeć granice odpowiedzialności modułów `brain_model/gui_app.py`,
  `brain_model/gui_forms.py`, `brain_model/gui_layout.py`,
  `brain_model/gui_config.py`, `brain_model/gui_runner.py` oraz
  `brain_model/gui_state.py` zgodnie z ADR-0012 i ADR-0013.
- Utrzymać `GuiState` jako źródło zatwierdzonych wartości formularzy oraz
  ograniczyć wpływ okien dialogowych do jawnych akcji zapisu.
- Ujednolicić walidację pól skalarnych i parametrów zaawansowanych tak, aby
  komunikaty błędów były zrozumiałe dla użytkownika i nie wymagały analizy
  tracebacków.
- Dopisać testy regresji dla zapisu, odczytu, resetu i anulowania formularzy.

**Akceptacja:**
- Anulowanie lub zamknięcie formularzy nie wprowadza niejawnych zmian
  zatwierdzonego stanu GUI.
- Niepoprawne wartości formularzy dają czytelne, polskie komunikaty błędów
  wskazujące pole oraz oczekiwany zakres albo format.
- Punkt wejścia `brain_model.gui:run_gui` pozostaje kompatybilny z istniejącymi
  importami, skryptami i dokumentacją użytkową.
- Testy potwierdzają spójność `GuiState`, konfiguracji JSON i uruchamiania
  symulacji po poprawnych zmianach formularzy.

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

---

## Zintegrowany plan biologiczny i wieloskalowy

Ta sekcja konsoliduje długoterminowy zakres biologiczny i wieloskalowy, aby jeden
plik backlogu był źródłem prawdy dla zadań, etapów i ograniczeń rozwoju.
Najbliższe zadania operacyjne pozostają w sekcji **Najbliższe konkretne zadania
do zaplanowania**, natomiast poniższe punkty opisują kierunek docelowy i nie
muszą odpowiadać jeden-do-jednego bieżącej strukturze plików.

## 1. Docelowa idea systemu

Docelowy program powinien mieć trzy warstwy:

```text
warstwa biologiczna
    neurony, synapsy, populacje neuronalne, astrocyty, neuromodulatory

warstwa sieciowa
    obszary mózgu, konektom, opóźnienia przewodzenia, oscylacje, synchronizacja

warstwa poznawcza
    uwaga, pamięć robocza, salience, kontrola wykonawcza, język, emocje, decyzje
```

Obecny program znajduje się głównie w trzeciej warstwie, z początkiem warstwy sieciowej przez oscylatory Wilsona-Cowana. Kolejnym etapem jest „podłożenie” pod każdy moduł poznawczy biologicznego mechanizmu: populacji pobudzających i hamujących, receptorów, neuroprzekaźników, plastyczności i sprzężeń międzyobszarowych.

## 2. Proponowana architektura docelowa

```text
brain_simulator/
├── apps/
│   ├── desktop_gui/
│   ├── web_gui/
│   └── notebooks/
│
├── brain_core/
│   ├── anatomy/
│   │   ├── regions.py
│   │   ├── connectome.py
│   │   ├── cortical_layers.py
│   │   └── atlases.py
│   │
│   ├── neurons/
│   │   ├── izhikevich.py
│   │   ├── adaptive_exponential.py
│   │   ├── hodgkin_huxley.py
│   │   └── cell_types.py
│   │
│   ├── synapses/
│   │   ├── ampa.py
│   │   ├── nmda.py
│   │   ├── gaba.py
│   │   ├── dopamine.py
│   │   ├── serotonin.py
│   │   ├── acetylcholine.py
│   │   └── plasticity.py
│   │
│   ├── populations/
│   │   ├── neural_mass.py
│   │   ├── wilson_cowan.py
│   │   ├── jansen_rit.py
│   │   ├── mean_field.py
│   │   └── spiking_population.py
│   │
│   ├── networks/
│   │   ├── structural_network.py
│   │   ├── functional_network.py
│   │   ├── delays.py
│   │   └── coupling.py
│   │
│   ├── cognition/
│   │   ├── attention.py
│   │   ├── working_memory.py
│   │   ├── episodic_memory.py
│   │   ├── semantic_memory.py
│   │   ├── executive_control.py
│   │   ├── salience.py
│   │   ├── language.py
│   │   ├── valuation.py
│   │   └── global_workspace.py
│   │
│   ├── physiology/
│   │   ├── eeg_forward_model.py
│   │   ├── bold_hrf.py
│   │   ├── metabolism.py
│   │   ├── neurovascular_coupling.py
│   │   └── homeostasis.py
│   │
│   ├── simulation/
│   │   ├── integrators.py
│   │   ├── scheduler.py
│   │   ├── multiscale_engine.py
│   │   ├── random_sources.py
│   │   └── state.py
│   │
│   ├── experiments/
│   │   ├── stimuli.py
│   │   ├── cognitive_tasks.py
│   │   ├── lesions.py
│   │   ├── pharmacology.py
│   │   └── protocols.py
│   │
│   └── analysis/
│       ├── eeg.py
│       ├── spectral.py
│       ├── connectivity.py
│       ├── information_flow.py
│       ├── phase_locking.py
│       └── reports.py
│
├── data/
│   ├── atlases/
│   ├── connectomes/
│   ├── parameters/
│   └── validation/
│
├── configs/
│   ├── default.yaml
│   ├── cognitive_demo.yaml
│   ├── eeg_demo.yaml
│   ├── lesion_demo.yaml
│   └── pharmacology_demo.yaml
│
└── tests/
```

Kluczowa zasada: kod modelu nie powinien być zaszyty w GUI. GUI powinno tylko generować konfigurację, np. YAML/JSON, a silnik symulacji powinien działać niezależnie.

## 3. Poziomy modelowania

### Poziom A: obecny model poznawczy

To zostaje jako warstwa wysokopoziomowa. Moduły typu `ATT`, `EXEC`, `HIP`, `SEM`, `DMN`, `GW` nadal istnieją, ale nie są już tylko abstrakcyjnymi zmiennymi. Każdy moduł dostaje biologiczne „ciało”.

Przykład:

```text
HIP =
    CA1
    CA3
    DG
    subiculum
    populacje pyramidalne
    interneurony GABA
    oscylacje theta
    plastyczność epizodyczna
```

```text
EXEC =
    DLPFC
    ACC
    basal ganglia loop
    populacje pobudzające/hamujące
    rytm beta
    kontrola bramkowania pamięci roboczej
```

### Poziom B: neural mass / mean field

To najbardziej praktyczny poziom dla całego mózgu. Każdy region atlasu mózgowego, np. 68, 100, 200 albo 400 regionów, jest opisany niewielkim układem równań różniczkowych. Takie podejście jest powszechne w modelowaniu whole-brain, bo jeden region można reprezentować małą liczbą zmiennych zamiast milionami neuronów. ([PLOS][2])

Minimalnie:

```text
E_r(t)  aktywność populacji pobudzającej regionu r
I_r(t)  aktywność populacji hamującej regionu r
A_r(t)  adaptacja / zmęczenie
N_r(t)  neuromodulacja
```

Równania:

```text
dE_r/dt = (-E_r + S(w_EE E_r - w_EI I_r + input_r + coupling_r)) / τ_E
dI_r/dt = (-I_r + S(w_IE E_r - w_II I_r)) / τ_I
```

### Poziom C: sieci kolczaste, czyli spiking neural networks

Dla wybranych obszarów, np. hipokampa, kory przedczołowej, wzgórza lub ciała migdałowatego, można zastosować modele neuronów kolczastych. Tutaj warto użyć Brian2, NEST, NEURON, Arbor albo NetPyNE. Brian2 jest elastycznym symulatorem sieci kolczastych w Pythonie, a NetPyNE pozwala budować wieloskalowe modele w NEURON z separacją parametrów od implementacji. ([brian2.readthedocs.io][3])

Praktyczna zasada:

```text
cały mózg        neural mass / mean field
wybrane obwody   spiking neural network
wybrane neurony  compartmental / Hodgkin-Huxley
```

### Poziom D: modele komórkowe

To najwyższy koszt obliczeniowy. Stosować tylko lokalnie, np. do demonstracji kanałów jonowych, receptorów NMDA, wpływu GABA albo dopaminy.

Modele:

```text
Hodgkin-Huxley
Morris-Lecar
Adaptive Exponential Integrate-and-Fire
Izhikevich
multi-compartment NEURON
```

## 4. Moduł anatomii i konektomu

Obecna macierz `W` powinna zostać zastąpiona przez strukturalny konektom.

Dane wejściowe:

```text
atlas mózgu
lista regionów
macierz połączeń strukturalnych
długości włókien
opóźnienia przewodzenia
typ regionu: sensoryczny, asocjacyjny, limbiczny, motoryczny
```

Model połączeń:

```text
coupling_i(t) = Σ_j C_ij · activity_j(t - delay_ij)
```

To jest istotne, bo mózg nie jest siecią natychmiastową. Opóźnienia przewodzenia są warunkiem powstawania synchronizacji, desynchronizacji, rytmów i fal aktywności.

## 5. Moduł neurochemii

Pełniejsza symulacja musi mieć neuromodulatory jako osobne pola dynamiczne, a nie pojedyncze zmienne diagnostyczne.

Proponowane systemy:

```text
dopamina        nagroda, błąd predykcji, motywacja, bramkowanie jąder podstawy
noradrenalina   czujność, stres, niepewność, wzrost gain
serotonina      stabilizacja nastroju, impulsywność, awersja, cierpliwość
acetylocholina  uwaga, uczenie sensoryczne, precyzja predykcji
GABA            hamowanie lokalne
glutaminian     pobudzenie, transmisja AMPA/NMDA
```

Każdy neuromodulator powinien wpływać na parametry regionów:

```text
gain sigmoidy
próg aktywacji
plastyczność synaptyczna
stosunek E/I
szum neuronalny
stałą czasową
```

Przykład:

```text
wysoka acetylocholina → większa precyzja sygnałów sensorycznych
wysoka noradrenalina  → większy gain, silniejsza reakcja salience
wysoka dopamina       → silniejsze uczenie wartościowania
wysoki GABA           → hamowanie, spadek pobudliwości
```

## 6. Moduł plastyczności

Bez plastyczności program będzie tylko symulatorem aktywacji. Biologiczna symulacja wymaga zmiany połączeń w czasie.

Potrzebne mechanizmy:

```text
Hebbian learning
STDP
homeostatic plasticity
synaptic scaling
reinforcement-modulated plasticity
metaplasticity
consolidation
forgetting
```

Dla poziomu neural mass wystarczy reguła:

```text
dW_ij/dt = η · pre_j · post_i · neuromodulator - λW_ij
```

Dla sieci kolczastych można stosować STDP:

```text
Δw = A+ exp(-Δt/τ+) gdy pre przed post
Δw = -A- exp(Δt/τ-) gdy post przed pre
```

## 7. Moduł EEG, LFP i fMRI/BOLD

Obecny sygnał `E-I` jest dobrym szkicem. Docelowo trzeba rozdzielić:

```text
spikes       aktywność neuronów kolczastych
LFP          lokalny potencjał polowy
EEG/MEG      projekcja aktywności źródeł korowych na elektrody
BOLD/fMRI    wolna odpowiedź hemodynamiczna
```

Minimalny model EEG:

```text
source_r(t) = gain_r · pyramidal_activity_r(t)
EEG_e(t) = Σ_r leadfield[e,r] · source_r(t)
```

Minimalny model BOLD:

```text
neural_activity → neurovascular coupling → HRF convolution → BOLD
```

Dzięki temu program może generować dane porównywalne z EEG/fMRI, a nie tylko abstrakcyjne wykresy aktywacji.

## 8. Moduł zadań poznawczych

Obecny scenariusz bodźców należy zamienić na protokoły eksperymentalne.

Przykłady:

```text
Stroop task
Go/No-Go
N-back
oddball auditory
visual search
fear conditioning
reward learning
semantic priming
working memory delay task
```

Każde zadanie powinno mieć:

```text
bodźce
czas prezentacji
reguły odpowiedzi
oczekiwane reakcje
miary behawioralne
mapowanie na moduły mózgowe
```

Wyniki:

```text
czas reakcji
trafność
błąd predykcji
siła uwagi
obciążenie pamięci roboczej
aktywność EEG
moc pasm
synchronizacja między regionami
```

## 9. Moduł uszkodzeń i zaburzeń

Bardzo wartościowy naukowo byłby moduł manipulacji patologicznych.

Typy manipulacji:

```text
lesion          usunięcie lub osłabienie regionu
disconnection   osłabienie połączeń
noise increase  wzrost szumu
E/I imbalance   zaburzenie równowagi pobudzenie-hamowanie
dopamine shift  zmiana dopaminy
GABA reduction  spadek hamowania
atrophy         spadek pojemności regionu
delay increase  spowolnienie przewodzenia
```

Przykłady symulacyjne:

```text
uszkodzenie hipokampa → deficyt kodowania epizodycznego
osłabienie DLPFC → gorsza kontrola wykonawcza
nadreaktywny salience network → błędna detekcja istotności
obniżony GABA → nadmierna synchronizacja / podatność napadowa
```

## 10. Silnik symulacyjny

Docelowy silnik powinien obsługiwać wiele solverów.

```text
Euler-Maruyama      szybki, prosty, dla SDE
Runge-Kutta RK4     dokładniejszy dla ODE
Dopri5 / RK45       adaptacyjny krok czasowy
event-based         dla sieci kolczastych
co-simulation       różne kroki czasowe dla różnych skal
GPU backend         JAX / PyTorch / CuPy
```

Najważniejszy problem to różne skale czasowe:

```text
kanały jonowe       mikrosekundy-milisekundy
spikes              milisekundy
oscylacje EEG       milisekundy-sekundy
BOLD/fMRI           sekundy
uczenie             sekundy-godziny
konsolidacja        godziny-dni
```

Dlatego potrzebny jest scheduler wieloskalowy.

## 11. Architektura obliczeniowa

Docelowo:

```text
Python core
NumPy/SciPy dla wersji bazowej
JAX albo PyTorch dla przyspieszenia GPU
Brian2/NEST/NEURON/Arbor jako backendy opcjonalne
HDF5/Zarr do zapisu dużych wyników
YAML/JSON do konfiguracji eksperymentów
Plotly/Dash albo web GUI do interfejsu
```

Wersja GitHub Pages z Pyodide może nadal istnieć, ale tylko jako wersja demonstracyjna. Pełna biologiczna symulacja powinna działać lokalnie albo na serwerze/HPC. Pyodide nie jest właściwym środowiskiem dla ciężkich modeli wieloskalowych.

## 12. Etapy rozbudowy

### Etap 1: uporządkowanie obecnego modelu

**Status:** `partial`

Cel: stabilna baza.

Dodać:

```text
konfiguracje YAML
zapis wyników do CSV/HDF5
testy jednostkowe
walidację parametrów
moduł eksperymentów
rozdzielenie GUI od silnika
```

### Etap 2: pełne modele populacyjne

**Status:** `partial`

Cel: biologicznie interpretowalne moduły.

Dodać:

```text
Wilson-Cowan dla każdego regionu
Jansen-Rit dla sygnałów EEG
opóźnienia przewodzenia
osobne populacje E/I
oscylacje theta/alpha/beta/gamma
sprzężenie między regionami
```

### Etap 3: konektom i atlas

**Status:** `partial`

Cel: przejście z 16 modułów poznawczych na regiony anatomiczne.

Dodać:

```text
atlas Desikan-Killiany albo Schaefer
macierz konektomu
mapowanie regionów na funkcje poznawcze
projekcję regionów na moduły poznawcze
```

Przykład:

```text
ATT  = FEF + IPS + pulvinar
EXEC = DLPFC + ACC + basal ganglia
EPIS = hippocampus + parahippocampal cortex
SAL  = anterior insula + dACC + amygdala
DMN  = mPFC + PCC + angular gyrus
```

### Etap 4: neuromodulacja

**Status:** `partial`

Cel: biologiczne sterowanie parametrami.

Dodać:

```text
dopamina
noradrenalina
serotonina
acetylocholina
GABA/glutaminian
farmakologiczne manipulacje parametrów
```

### Etap 5: plastyczność i uczenie

**Status:** `partial`

Cel: model ma się zmieniać w wyniku doświadczenia.

Dodać:

```text
Hebbian learning
STDP
reinforcement learning
consolidation
forgetting
homeostatic regulation
```

### Etap 6: backend SNN dla wybranych obwodów

Cel: lokalnie szczegółowa symulacja biologiczna.

**Status:** `partial`

Zrealizowano:

```text
[x] Brian2 jako backend startowy (adapter: brain_core/populations/spiking_population.py)
[x] Kontrakt NM↔SNN (wejścia/wyjścia + sync_dt)
[x] Ograniczenie pilotażu do 1-2 obwodów (hipokamp, DLPFC)
[x] Scheduler wieloskalowy (brain_core/simulation/multiscale_engine.py)
[x] Test wydajności/stabilności smoke dla współsymulacji
```

Do dalszej realizacji:

```text
[ ] NEST dla dużych SNN
[ ] NEURON/NetPyNE dla modeli biokomórkowych
[ ] Arbor dla symulacji wielkoskalowych/HPC
```

### Etap 7: walidacja

**Status:** `partial`

Cel: model nie tylko generuje wykresy, ale daje porównywalne dane.

Porównać z:

```text
EEG: moc pasm, ERP, phase locking
fMRI: BOLD, functional connectivity
behawior: czas reakcji, trafność, błędy
neuropsychologia: profile deficytów po uszkodzeniach
```

## 13. Proponowany docelowy przepływ działania

```text
1. Użytkownik wybiera eksperyment poznawczy.
2. System ładuje konfigurację mózgu.
3. System generuje bodźce.
4. Silnik symuluje dynamikę neuronalną i poznawczą.
5. Moduł fizjologii generuje EEG/BOLD.
6. Moduł zachowania generuje odpowiedzi.
7. Moduł analizy oblicza metryki.
8. GUI pokazuje wykresy, sieci, raport i eksport danych.
```

## 14. Najważniejsza decyzja projektowa

Nie próbowałbym od razu budować „pełnego mózgu” na poziomie neuronów. To byłoby obliczeniowo i metodologicznie niekontrolowane. Najlepsza architektura to:

```text
whole brain = neural mass / mean field
selected circuits = spiking neural networks
selected cells = biophysical compartment models
cognition = symbolic/functional control layer
```

To daje kompromis: biologiczna interpretowalność, wykonalność obliczeniowa i możliwość demonstracji procesów psychologii poznawczej oraz neuropsychologii.

[1]: https://ebrains.eu/data-tools-services/modelling-simulation/whole-brain-simulation?utm_source=chatgpt.com "Whole Brain Simulation"
[2]: https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012647&utm_source=chatgpt.com "Insights from next generation neural mass modelling ..."
[3]: https://brian2.readthedocs.io/?utm_source=chatgpt.com "Brian 2 documentation — Brian 2 2.10.1 documentation"
