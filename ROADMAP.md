# ROADMAP — `neuro_sim`

## 1. Status dokumentu

**Stan na dzień:** 2026-06-05
**Zakres:** kierunek rozwoju aplikacji, kamienie milowe i zależności między strumieniami prac.
**Relacja do backlogu:** `BACKLOG.md` pozostaje operacyjną listą zadań, statusów i artefaktów. Ten dokument opisuje szerszą kolejność rozwoju oraz kryteria przejścia między etapami.

Roadmapa zakłada rozwój iteracyjny: ponieważ kluczowe artefakty MVP już istnieją, najbliższy akcent nie jest położony na samo wdrażanie kolejnych artefaktów MVP, lecz na walidację, sklejenie interpretacji dydaktycznej i dopięcie raportów porównawczych. Dopiero po tym należy rozszerzać warstwę biologiczną, kliniczną, platformową oraz hybrydy mikro-makro.

---

## 2. Wizja produktu

`neuro_sim` ma ewoluować z demonstratora procesów poznawczych do **wieloskalowej platformy symulacji mózgu** dla dydaktyki, eksploracji hipotez i porównań scenariuszy klinicznych.

Docelowy użytkownik powinien móc:

1. wybrać gotowy scenariusz poznawczy lub kliniczny,
2. uruchomić eksperyment z jednego pliku konfiguracji,
3. odtworzyć wynik dzięki jawnej konfiguracji, seedowi i wersjonowanym parametrom,
4. porównać przebiegi healthy/disorder/lesion dla tego samego bodźca,
5. otrzymać raport, który wyjaśnia „co, kiedy i dlaczego” wydarzyło się w modelu,
6. wykorzystać wyniki w ćwiczeniach dydaktycznych lub wstępnej analizie hipotez.

---

## 3. Główne założenia rozwoju

### 3.1. Założenia produktowe

- **Dydaktyka jako pierwszy przypadek użycia** — funkcje mają pomagać zrozumieć mechanizm, nie tylko generować przebieg numeryczny.
- **Scenariusze porównawcze** — wartość aplikacji rośnie, gdy ten sam bodziec można uruchomić dla profilu zdrowego, zaburzenia i uszkodzenia.
- **Raport zamiast surowych danych** — każdy eksperyment powinien kończyć się interpretowalnym raportem z osią czasu i słownikiem pojęć.
- **Roving oddball jako zadanie referencyjne** — `roving_oddball` jest rozwijany jako główny scenariusz dla predykcji, nowości, habituacji i readaptacji; artefakty MVP już istnieją w `brain_core/experiments/protocols.py`, `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml` i `configs/roving_oddball_lesion_hippocampus.yaml`, a walidacja części metryk pozostaje do domknięcia.

### 3.2. Założenia techniczne

- **KISS i minimalny zakres zmian** — rozwój ma wykorzystywać istniejące moduły `brain_core` i `brain_model`, bez niepotrzebnego mnożenia warstw.
- **Konfiguracja ponad hardcoding** — eksperyment ma być uruchamiany z YAML/JSON, a zmiany schematu muszą mieć walidację lub ścieżkę migracji.
- **Deterministyczność** — seed, konfiguracja, wersje parametrów i dane wejściowe muszą wystarczyć do odtworzenia przebiegu.
- **Separacja odpowiedzialności** — `brain_core` odpowiada za silnik, eksperymenty, anatomię i analizę; `brain_model` za model poznawczy, scenariusze, GUI i prezentację.
- **Testowalność** — każda zmiana logiki powinna mieć testy jednostkowe, integracyjne lub artefakt weryfikacji.

### 3.3. Założenia naukowo-modelowe

- **Model wieloskalowy, nie pełna symulacja komórkowa** — cały mózg jest reprezentowany przez neural mass/mean-field, a szczegółowe modele spiking są używane tylko dla wybranych obwodów.
- **Konektom i opóźnienia jako fundament sieciowy** — synchronizacja i dynamika międzymodułowa powinny wynikać z wag oraz opóźnień przewodzenia.
- **Neuromodulacja jako mechanizm interpretacyjny** — DA/5-HT/ACh/NA/GABA/glutaminian wpływają na pobudliwość, gating, plastyczność i stosunek E/I.
- **Walidacja jakościowa** — na tym etapie priorytetem są spójne, jakościowe efekty neuropsychologiczne, a nie kliniczna predykcja diagnostyczna.

---

## 4. Stan wyjściowy po przeglądzie 2026-06-05

Repozytorium posiada już fundamenty potrzebne do rozwoju roadmapy:

- `brain_core/simulation/` — konfiguracja, loader, uruchamianie eksperymentów, scheduler, integratory i deterministyczne źródła RNG,
- `brain_core/experiments/` — protokoły zadań, uszkodzenia i farmakologia,
- `brain_core/anatomy/` oraz `brain_core/networks/` — atlas, konektom, sieć strukturalna i opóźnienia,
- `brain_core/populations/` — Wilson-Cowan i pilotażowy adapter spiking,
- `brain_core/analysis/` oraz `brain_core/physiology/` — metryki sygnałowe, raporty, EEG/BOLD,
- `brain_model/` — model poznawczy, scenariusze, GUI, IO, raporty i wizualizacje,
- `configs/`, `data/`, `tests/` — przykładowe konfiguracje, dane atlasu/konektomu/walidacji oraz testy regresyjne.

Najważniejsze braki do domknięcia przed rozwojem funkcji zaawansowanych dotyczą teraz walidacji, spójnego połączenia istniejących artefaktów i interpretacji dydaktycznej, a nie samego tworzenia kolejnych artefaktów MVP:

1. jeden spójny schemat konfiguracji dla wszystkich eksperymentów,
2. pełny raport timeline trial-by-trial,
3. wersjonowany baseline `healthy_v1`,
4. walidacja i dydaktyczne sklejenie interpretacji `roving_oddball`,
5. pełniejsze raporty porównawcze healthy/disorder/lesion,
6. kompletność raportu trial-by-trial i jednolita dokumentacja interpretacji scenariuszy.

---


## 4A. Status funkcji i zakres MVP

Statusy w roadmapie używają wyłącznie wartości `done`, `partial` i `planned`.
Poniższa tabela oddziela działające MVP od zakresu docelowego, aby nie traktować
roadmapy jako obietnicy nowych funkcji na tym etapie.

| Funkcja | Status | MVP istnieje | Pozostały zakres |
| --- | --- | --- | --- |
| `roving_oddball` | `partial` | Artefakty MVP istnieją w `brain_core/experiments/protocols.py`, `configs/roving_oddball_healthy.yaml`, `configs/roving_oddball_disorder_gaba.yaml`, `configs/roving_oddball_lesion_hippocampus.yaml` i `docs/roving_oddball_guide.md`; obejmują aliasy, testy reprodukowalności i przewodnik dydaktyczny. | Walidacja metryk habituacji/readaptacji, porównanie profili healthy/disorder/lesion i raport amplitude-latency-mechanism. |
| Clinical profiles | `partial` | Profile w `configs/clinical_profiles/*.yaml`, integracja z konfiguracją oraz scenariuszami lesion/clinical; istnieją jakościowe progi różnic i podstawowe komentarze dydaktyczne. | Kalibracja progów, raport amplitude-latency-mechanism i walidacja względem benchmarków. |
| Timeline | `partial` | Oś `event_timeline` tworzona w `brain_core/simulation/events.py` i dołączana przez silnik oraz raporty. | Pełne grupowanie trial-by-trial, eksport raportu, linkowanie z wykresami i objaśnienia per profil. |
| Benchmark metadata | `partial` | Metadane benchmarków w `data/validation/benchmark_metadata.json` i walidacja w loaderze benchmarków. | Kryteria zgodności per benchmark, źródła literaturowe/empiryczne i raport wersyjny. |
| SNN demo | `partial` | Demo `snn_hippocampus_demo`, adapter sygnałów NM↔SNN, tryb `closed_loop`, dokument demo i testy pilotażowe. | Walidacja stabilności closed-loop, pomiar kosztu `report_only` vs `closed_loop`, pełniejsza synchronizacja kroków i backendy NEST/NEURON/Arbor. |
| GUI YAML presets | `partial` | Presety YAML dla `roving_oddball` i `snn_hippocampus_demo` są dostępne w konfiguracji GUI i sprawdzane statycznie testami. | Dopięcie interpretacji dydaktycznej w GUI, polskich etykiet i instrukcji wyboru scenariusza bez duplikowania logiki silnika. |
| Rejestr walidacji | `partial` | `docs/validation_registry.md`, metadane benchmarków i loader opisują podstawowe benchmarki edukacyjne. | Kryteria zgodności, źródła, poziomy walidacji i raport wersyjny pokazujący zakres jakościowo odtworzonych efektów. |

## 5. Strumienie strategiczne

### S1. Reprodukowalny pipeline eksperymentu

**Cel:** każdy eksperyment ma być uruchamialny z konfiguracji i odtwarzalny przy tym samym seedzie.

**Obejmuje:** schemat YAML/JSON, walidację, seed/RNG, wersjonowanie parametrów, zapisywanie metadanych uruchomienia.

### S2. Raport dydaktyczny i interpretowalność

**Cel:** użytkownik rozumie przebieg symulacji bez czytania kodu.

**Obejmuje:** log zdarzeń, oś czasu, słownik pojęć, raport Markdown/HTML, komentarze dla przejść standard/deviant i zmian profilu.

### S3. Warstwa biologiczno-sieciowa

**Cel:** przejście od samego modelu poznawczego do regionów, konektomu, opóźnień, populacji E/I i neuromodulacji.

**Obejmuje:** atlas, konektom, neural mass, opóźnienia, DA/5-HT/ACh/NA/GABA/glutaminian, EEG/BOLD.

### S4. Scenariusze i task battery

**Cel:** dostarczyć zestaw powtarzalnych zadań poznawczych oraz porównywalnych profili.

**Obejmuje:** `stroop`, `go_nogo`, `n_back`, `roving_oddball`, healthy/disorder/lesion, konfiguracje i raporty per task.

### S5. Jakość, dokumentacja i gotowość dydaktyczna

**Cel:** utrzymać projekt zrozumiały, testowalny i gotowy do użycia na zajęciach.

**Obejmuje:** testy, docstringi, type hints, ADR, instrukcje uruchamiania, słownik EN→PL, scenariusze lekcyjne.

### S6. Profesjonalna aplikacja dydaktyczna

**Cel:** przekształcić demonstrator naukowy w aplikację, którą prowadzący może
bezpiecznie wykorzystać na ćwiczeniach, laboratoriach i pokazach bez ręcznej
edycji kodu.

**Obejmuje:** katalog lekcji, tryb nauczyciela krok po kroku, pakiety
zajęciowe HTML/PDF, karty pracy studentów, rubryki oceny, dostępność,
spójne komunikaty po polsku oraz ostrzeżenia przed interpretacją diagnostyczną
profili clinical/lesion.

---

## 6. Roadmapa etapami

### Etap 0 — Porządkowanie stanu i kontraktów dokumentacyjnych

**Horyzont:** natychmiast / przed kolejnymi zmianami strukturalnymi
**Priorytet:** P0
**Status:** `partial`

**Cele:**

- Utrzymać `BACKLOG.md` jako listę prac z jasnym statusem i pozostałym zakresem.
- Utrzymać `docs/program_structure.md` jako opis rzeczywistej struktury repozytorium.
- Spiąć `ROADMAP.md`, `BACKLOG.md` i `README.md` w jeden spójny obraz rozwoju.

**Najbliższe działania:**

- aktualizować roadmapę przy zmianie kierunku produktu,
- aktualizować ADR przy zmianach granic odpowiedzialności modułów,
- dopisywać do backlogu artefakty implementacyjne po zakończeniu prac.

**Kryteria przejścia:**

- nowy kontrybutor rozumie z dokumentacji: co istnieje, co jest planowane i gdzie zacząć pracę,
- dokumenty nie opisują nieistniejących katalogów jako aktualnej struktury.

---

### Etap 1 — Fundament symulacyjno-edukacyjny

**Horyzont:** najbliższy etap wykonawczy
**Priorytet:** P0
**Status:** `partial`

**Cele:**

- Domknąć reprodukowalny pipeline: konfiguracja → symulacja → analiza → raport.
- Umożliwić uruchomienie baseline `healthy_v1` jako stabilnego punktu odniesienia.
- Zapewnić raport, który tłumaczy przebieg eksperymentu krok po kroku.

**Zakres:**

- ujednolicenie konfiguracji eksperymentów wokół istniejących `ExperimentConfig`, `config_loader` i `run.py`,
- jawne sekcje konfiguracji: `stimulus`, `brain_profile`, `connectome`, `rng_seed`, `analysis`,
- czytelne błędy walidacji konfiguracji,
- baseline `healthy_v1` z dokumentacją, metadanymi i progami regresji,
- event log oraz raport timeline generowany po symulacji,
- testy walidacji wejścia i regresji baseline.

**MVP istnieje:**

- `event_timeline` jest budowany w `brain_core/simulation/events.py` i dołączany do wyników symulacji.
- Raporty potrafią korzystać z podstawowych zdarzeń bodźców, odpowiedzi, patologii i zmian aktywności.

**Pozostały zakres:**

- ujednolicić timeline dla wszystkich typów symulacji,
- dodać pełny widok trial-by-trial, eksport HTML/PDF i powiązanie zdarzeń z wykresami.

**Artefakty docelowe:**

- specyfikacja konfiguracji,
- przykładowe konfiguracje baseline,
- raport `.md`/`.html` po uruchomieniu,
- testy walidacji i reprodukowalności seedów.

**Kryteria ukończenia:**

- użytkownik uruchamia eksperyment z jednego pliku config,
- ten sam config i seed dają identyczny wynik w granicach tolerancji,
- raport pozwala odtworzyć przebieg bez zaglądania do kodu.

---

### Etap 2 — Model regionowy, konektom i neuromodulacja

**Horyzont:** po domknięciu Etapu 1
**Priorytet:** P1
**Status:** `partial`

**Cele:**

- Przejść z uproszczonej macierzy połączeń do modelu regionowego.
- Ustabilizować neural mass/mean-field per region.
- Uczynić neuromodulację widocznym i interpretowalnym mechanizmem.

**Zakres:**

- atlas regionów i typów funkcjonalnych,
- strukturalny konektom `C_ij` i opóźnienia `delay_ij`,
- stabilność symulacji dla scenariuszy >50 regionów,
- profile DA/5-HT/ACh/NA/GABA/glutaminian jako modyfikatory pobudliwości, gatingu, plastyczności i stosunku E/I,
- raport pre/post modulacji,
- sanity checks dla zakresów parametrów.

**Artefakty docelowe:**

- dane edukacyjnego atlasu i konektomu,
- konfiguracje wieloregionowe,
- raport porównujący przebieg bez modulacji i po modulacji,
- testy stabilności i neuromodulacji.

**Kryteria ukończenia:**

- co najmniej dwa eksperymenty działają na konektomie z opóźnieniami,
- wpływ modulacji jest widoczny w metrykach i raporcie,
- symulacje wieloregionowe pozostają stabilne numerycznie.

---

### Etap 3 — Task battery i roving oddball jako scenariusz referencyjny

**Horyzont:** równolegle z końcówką Etapu 2 / przed pełną biblioteką kliniczną
**Priorytet:** P1/P2
**Status:** częściowo zrealizowany (`partial`)

**Cele:**

- Ujednolicić bibliotekę zadań poznawczych.
- Rozwinąć istniejący `roving_oddball` jako zadanie referencyjne dla predykcji, nowości, habituacji i readaptacji.
- Zapewnić te same sekwencje bodźców dla profili healthy/disorder/lesion.

**Zrealizowane artefakty:**

- `RovingOddballTask` jako dedykowany protokół zadania referencyjnego w `brain_core/experiments/protocols.py`.
- Aliasy `get_task` dla wariantów nazwy `roving_oddball`.
- Konfiguracje scenariuszy healthy/disorder/lesion:
  - `configs/roving_oddball_healthy.yaml`,
  - `configs/roving_oddball_disorder_gaba.yaml`,
  - `configs/roving_oddball_lesion_hippocampus.yaml`.
- Testy reprodukowalności sekwencji oraz ładowania konfiguracji scenariuszy w `tests/test_task_protocols_and_engine.py`.

**Braki do domknięcia:**

- Przewodnik dydaktyczny „Roving Oddball — od bodźca do interpretacji”.
- Pełny raport porównawczy healthy/disorder/lesion.
- Walidacja metryk habituacji/readaptacji, w tym testy regresji dla zwalidowanych progów interpretacyjnych.

**Zakres docelowy i dalszy:**

- utrzymanie wspólnego API tasków dla `stroop`, `go_nogo`, `n_back` i `roving_oddball`,
- timeline trial-by-trial z interpretacją mechanizmu profilu klinicznego,
- raport healthy vs disorder vs lesion oparty na istniejących konfiguracjach,
- walidacja metryk: novelty/surprise index, tempo habituacji, latencja readaptacji, różnice E/I i neuromodulacyjne.

**Kryteria ukończenia:**

- ten sam seed odtwarza identyczną sekwencję bodźców,
- raport pokazuje habituację w runie i reset odpowiedzi po zmianie standardu,
- co najmniej dwa profile zaburzeń i jeden profil lesion mają odróżnialne wzorce.

---

### Etap 4 — Biblioteka profili klinicznych i uszkodzeń

**Horyzont:** po Etapie 3
**Priorytet:** P1/P2
**Status:** `partial`

**Cele:**

- Dostarczyć porównania healthy vs disorder vs lesion jako podstawową wartość edukacyjną.
- Umożliwić uruchomienie identycznego bodźca na wielu profilach.

**MVP istnieje:**

- Profile healthy/disorder/lesion są opisane w `configs/clinical_profiles/*.yaml`.
- Schemat konfiguracji i silnik obsługują profil kliniczny w uruchomieniu.
- Moduły lesion i scenariuszy umożliwiają podstawowe porównania.

**Pozostały zakres:**

- uzupełnić interpretacje dydaktyczne dla każdego profilu,
- zdefiniować progi jakościowe różnic i mechanizm raportowania,
- zweryfikować profile względem benchmarków oraz metryk roving oddball.

**Zakres:**

- katalog profili klinicznych v1,
- co najmniej trzy profile disorder, np. deficyt dopaminy, dysregulacja GABA, zaburzenie serotoniny,
- co najmniej dwa typy lesion: ogniskowy i sieciowy,
- automatyczny raport różnic: region, czas, funkcja poznawcza, mechanizm,
- komentarze dydaktyczne dla każdego profilu.

**Artefakty docelowe:**

- katalog profili i lesion,
- konfiguracje porównawcze,
- dashboard lub raport porównawczy,
- testy scenariuszy porównawczych.

**Kryteria ukończenia:**

- użytkownik wybiera scenariusz i profile, a system uruchamia porównanie 1:1,
- raport wskazuje nie tylko różnicę, ale też proponowany mechanizm,
- profile są opisane po polsku i spójne terminologicznie ze słownikiem projektu.

---

### Etap 5 — Warstwa EEG/BOLD i profesjonalny tryb nauczyciela

**Horyzont:** po ustabilizowaniu scenariuszy porównawczych
**Priorytet:** P2
**Status:** `partial`

**Cele:**

- Połączyć symulację z metrykami znanymi z praktyki badawczej.
- Uczynić aplikację gotową do użycia podczas zajęć.
- Dostarczyć profesjonalny przepływ dydaktyczny: przygotowanie lekcji,
  prowadzenie ćwiczenia, omówienie wyników i eksport materiałów.

**Zakres:**

- metryki spektralne EEG, synchronizacja, phase-locking,
- uproszczone mapowanie BOLD/HRF,
- raporty z wykresami i interpretacją,
- widoki „co obserwujesz teraz?” i „dlaczego to ważne?”,
- pytania kontrolne, scenariusze lekcyjne i polskie etykiety pojęć,
- katalog lekcji z metadanymi: cel, czas, poziom trudności, profil, task,
  wymagane artefakty i oczekiwane obserwacje,
- kreator lub panel wyboru scenariusza, który uruchamia konfigurację bez
  ręcznego edytowania YAML przez studenta,
- pakiet zajęciowy eksportowany po uruchomieniu: raport HTML/PDF, karta pracy,
  skrót dla prowadzącego, seed, konfiguracja i wersja kodu,
- rubryka oceny odpowiedzi studenta oraz lista kontrolna prowadzącego,
- dostępność i profesjonalna użyteczność: kontrast, opisy wykresów, spójne
  komunikaty błędów, przewidywalna nawigacja i polska terminologia,
- jawne ograniczenia interpretacyjne dla profili clinical/lesion, aby aplikacja
  nie sugerowała zastosowań diagnostycznych.

**Artefakty docelowe:**

- raporty EEG/BOLD per scenariusz,
- szablony lekcji laboratoryjnych,
- rozszerzony słownik pojęć EN→PL,
- widoki edukacyjne v1,
- katalog profesjonalnych scenariuszy dydaktycznych v1,
- eksportowalne pakiety zajęciowe HTML/PDF,
- karta pracy studenta, skrót dla prowadzącego i rubryka oceny.

**Kryteria ukończenia:**

- student widzi metrykę, interpretację i kontekst biologiczny w jednym raporcie,
- nauczyciel może użyć gotowego scenariusza z pytaniami kontrolnymi,
- raporty są spójne dla tasków i profili porównawczych,
- prowadzący może przeprowadzić co najmniej trzy kompletne lekcje bez edycji
  kodu ani ręcznego składania materiałów,
- eksport lekcji zawiera konfigurację, seed, wersję kodu, wykresy, metryki,
  komentarze dydaktyczne i ograniczenia interpretacyjne.

---

### Etap 6 — Hybrydy mikro-makro i platforma długoterminowa

**Horyzont:** długoterminowo
**Priorytet:** P3
**Status:** `partial`

**Cele:**

- Zintegrować wybrane obwody spiking z modelem makro.
- Rozwinąć personalizację i symulacje kohortowe.
- Zbudować bibliotekę benchmarków i hipotez literaturowych.

**MVP istnieje:**

- `snn_hippocampus_demo` pokazuje pilotaż neural-mass + lokalny obwód SNN z trybem `closed_loop` oraz raportowym wariantem `report_only`.
- `data/validation/benchmark_metadata.json` opisuje syntetyczne i edukacyjne benchmarki EEG, fMRI oraz zachowania.

**Pozostały zakres:**

- zwalidować stabilność i koszt sprzężenia zwrotnego SNN wpływającego na trajektorię neural-mass,
- dodać kryteria zgodności i źródła dla benchmarków literaturowych/empirycznych,
- przygotować raport wersyjny „co model odtwarza, czego jeszcze nie”.

**Zakres:**

- 1–2 obwody spiking, np. hipokamp lub DLPFC/PFC-BG,
- synchronizacja kroków czasowych neural mass ↔ SNN,
- personalizacja parametrów i symulacje kohortowe,
- raport statystyczny porównań,
- rejestr hipotez i benchmarków,
- zautomatyzowane testy zgodności jakościowej.

**Artefakty docelowe:**

- eksperyment wieloskalowy z raportem dydaktycznym,
- dokument ograniczeń wydajnościowych i interpretacyjnych,
- konfiguracje kohortowe,
- wersjonowany raport „co model odtwarza, czego jeszcze nie”.

**Kryteria ukończenia:**

- eksperyment mikro-makro jest powtarzalny i udokumentowany,
- personalizacja nie łamie deterministyczności,
- benchmarki mają jawne źródła i kryteria zgodności.

---

## 7. Zależności między etapami

```text
Etap 0: dokumentacja i kontrakty
    ↓
Etap 1: konfiguracja + baseline + raport timeline
    ↓
Etap 2: konektom + neural mass + neuromodulacja
    ↓
Etap 3: task battery + roving oddball
    ↓
Etap 4: healthy/disorder/lesion
    ↓
Etap 5: EEG/BOLD + profesjonalny tryb nauczyciela
    ↓
Etap 6: mikro-makro + kohorty + benchmarki
```

Najważniejsze zależności blokujące:

- `roving_oddball` ma już stabilny RNG i wspólne API tasków, a do domknięcia pozostają raport trial-by-trial oraz walidacja metryk habituacji/readaptacji,
- profile clinical/lesion wymagają baseline `healthy_v1` oraz porównywalnych konfiguracji,
- tryb nauczyciela wymaga gotowych raportów i spójnej terminologii PL,
- hybrydy mikro-makro wymagają stabilnego kontraktu wymiany sygnałów i ograniczeń wydajnościowych.

---

## 8. Mierniki sukcesu

### Produktowe

- liczba gotowych scenariuszy uruchamianych z konfiguracji,
- liczba profili healthy/disorder/lesion z raportem porównawczym,
- liczba kompletnych lekcji dostępnych bez edycji kodu,
- kompletność eksportu pakietu zajęciowego: raport, karta pracy, notatka dla
  prowadzącego, seed, konfiguracja i wersja kodu,
- czas potrzebny użytkownikowi do uruchomienia i zinterpretowania eksperymentu.

### Naukowo-dydaktyczne

- czytelność mechanizmu w raporcie: region, czas, neuromodulator, efekt poznawczy,
- zgodność jakościowa z oczekiwanymi efektami neuropsychologicznymi,
- liczba gotowych scenariuszy lekcyjnych.

### Inżynierskie

- reprodukowalność wyników dla tego samego configu i seeda,
- pokrycie testami walidacji konfiguracji, tasków, lesion, neuromodulacji i raportów,
- liczba braków docstringów/type hints wykrywana przez audyt,
- liczba zmian strukturalnych opisanych ADR.

---

## 9. Ryzyka i mitigacje

### Najbliższe krytyczne ryzyka

| Ryzyko | Dlaczego jest krytyczne teraz | Najbliższa mitigacja |
| --- | --- | --- |
| Kalibracja progów clinical profiles | progi wpływają na komentarze dydaktyczne i raporty porównawcze | porównać profile z benchmarkami i dodać testy regresji progów |
| Interpretacja benchmarków | metadane bez jawnych kryteriów mogą prowadzić do nadinterpretacji | dopisać kryteria zgodności, źródła i ograniczenia dla każdego benchmarku |
| Koszt `closed_loop` SNN | dodatkowa symulacja może ograniczyć użycie w GUI i scenariuszach lekcyjnych | zmierzyć `report_only` vs `closed_loop` na tym samym zadaniu, seedzie i czasie |
| Kompletność raportu trial-by-trial | bez pełnego widoku per trial użytkownik nie odtworzy mechanizmu wyniku | domknąć grupowanie zdarzeń, opis mechanizmu i linki do wykresów |

| Ryzyko | Skutek | Mitigacja |
| --- | --- | --- |
| Zbyt szybkie dokładanie modeli biologicznych | niestabilność i trudność interpretacji | najpierw raport i baseline, potem rozszerzenia |
| Rozjazd GUI i silnika | duplikacja logiki, trudność testowania | konfiguracja jako kontrakt, GUI tylko generuje/uruchamia scenariusz |
| Brak deterministyczności | brak regresji i porównań | seed, wersjonowane parametry, kontrolowane RNG |
| Over-engineering | opóźnienie wartości edukacyjnej | małe etapy, KISS, minimalne API |
| Nieczytelne raporty | użytkownik nie rozumie wyniku | oś czasu, słownik pojęć, komentarz mechanizmu |
| Niestabilność neural mass | fałszywe wzorce wyników | sanity checks, zakresy parametrów, testy stabilności |
| Zbyt ambitna walidacja kliniczna | nadinterpretacja modelu | walidacja jakościowa i jasne ograniczenia |

---

## 10. Plan dalszego rozwoju i ulepszeń od 2026-06-26

Ten plan porządkuje dalszy rozwój programu po aktualnym stanie roadmapy. Nie
zastępuje backlogu operacyjnego; wskazuje kolejność decyzji produktowych,
technicznych i walidacyjnych, które powinny najpierw zwiększyć użyteczność
dydaktyczną, a dopiero później rozszerzać złożoność biologiczną modelu.

### 10.1. Priorytet A — stabilne jądro eksperymentu

**Cel:** użytkownik uruchamia eksperyment z jednego pliku konfiguracji, a wynik
można odtworzyć i porównać między profilami.

**Zakres prac:**

- domknąć walidację konfiguracji YAML/JSON dla wszystkich publicznych punktów
  wejścia, tak aby błędy były po polsku i wskazywały konkretną sekcję;
- utrwalić `healthy_v1` jako wersjonowany baseline regresyjny z metrykami,
  tolerancjami i opisem ograniczeń;
- rozszerzyć artefakty wyniku o jednoznaczny indeks uruchomienia: konfigurację,
  seed, commit Git, środowisko, metryki, log i ścieżki danych;
- utrzymać kompatybilność dotychczasowego słownika wynikowego tylko na granicy
  API, a wewnętrznie rozwijać jawny kontrakt `ExperimentResult`;
- dodać szybkie testy regresyjne dla deterministyczności seeda, stabilności
  kształtów tablic i walidacji konfiguracji.

**Kryteria ukończenia:**

- ta sama konfiguracja i seed dają powtarzalny wynik w przyjętej tolerancji;
- niepoprawna konfiguracja kończy się czytelnym błędem walidacji;
- każdy publiczny eksperyment zapisuje minimalny zestaw artefaktów
  reprodukowalności.

### 10.2. Priorytet B — interpretowalne raporty i analiza trial-by-trial

**Cel:** raport ma wyjaśniać mechanizm wyniku bez konieczności czytania kodu lub
surowych tablic.

**Zakres prac:**

- domknąć grupowanie osi czasu per trial dla `roving_oddball`;
- pokazywać w raporcie typ bodźca, odpowiedź, metryki amplitudy i latencji,
  habituację, readaptację oraz krótki komentarz mechanizmu;
- powiązać zdarzenia timeline z wykresami i eksportem HTML/PDF;
- dodać jawne ostrzeżenia, że profile clinical/lesion są dydaktyczne i nie są
  narzędziem diagnostycznym;
- utrzymywać słownictwo użytkowe zgodnie z `docs/english_polish_glossary.md`.

**Kryteria ukończenia:**

- raport `roving_oddball` pozwala prześledzić każdy trial od bodźca do
  interpretacji;
- eksport HTML/PDF zawiera konfigurację, seed, metryki, wykresy i ograniczenia;
- testy sprawdzają obecność kluczowych pól trial-by-trial i komentarzy
  dydaktycznych.

### 10.3. Priorytet C — porównania healthy/disorder/lesion i walidacja jakościowa

**Cel:** ten sam scenariusz można bezpiecznie porównać między profilami, a
raport pokazuje oczekiwany kierunek zmian i zakres zaufania.

**Zakres prac:**

- uruchomić porównania `roving_oddball` dla healthy, disorder i lesion na
  wspólnym seedzie oraz wspólnym zestawie metryk;
- skalibrować progi profili klinicznych względem rejestru walidacji i
  benchmarków jakościowych;
- dla każdego profilu opisać `primary_metric`, `expected_direction`,
  `severity_level`, tolerancje i ograniczenia stosowalności;
- wprowadzić raport porównawczy z tabelą różnic oraz komentarzem
  amplitude-latency-mechanism;
- oznaczyć efekty jako odtworzone jakościowo, częściowo odtworzone albo poza
  zakresem modelu.

**Kryteria ukończenia:**

- porównanie trzech profili działa z jednego zestawu konfiguracji;
- rejestr walidacji wskazuje źródło i kryterium zgodności dla każdej metryki;
- raport nie sugeruje zastosowań klinicznych poza edukacją i eksploracją
  hipotez.

### 10.4. Priorytet D — ulepszenie desktopowego GUI i przepływu nauczyciela

**Cel:** prowadzący może przeprowadzić zajęcia bez edycji kodu, a GUI pozostaje
cienką warstwą nad konfiguracją i silnikiem.

**Zakres prac:**

- rozwinąć wybór presetów YAML w GUI PySide6 o polskie opisy celu, oczekiwanych
  obserwacji, ograniczeń i powiązanej lekcji;
- dodać widok porównania profili z tym samym seedem i jasnym wskazaniem
  różnic;
- rozbudować tryb nauczyciela o kroki: hipoteza, uruchomienie, obserwacja,
  interpretacja, ograniczenia i pytania kontrolne;
- zapewnić eksport pakietu zajęciowego: raport, karta pracy, konfiguracja,
  metadane uruchomienia i wykresy;
- nie dodawać nowych przepływów `tkinter`; nowe elementy desktopowe rozwijać
  wyłącznie w PySide6/Qt.

**Kryteria ukończenia:**

- użytkownik wybiera lekcję i uruchamia powiązany eksperyment bez ręcznej edycji
  YAML;
- GUI nie duplikuje logiki walidacji ani obliczeń z `brain_core`;
- statyczne testy zależności potwierdzają brak nowych przepływów `tkinter`.

### 10.5. Priorytet E — rozszerzenia biologiczne po ustabilizowaniu raportów

**Cel:** rozwijać model biologiczny tylko tam, gdzie raporty i walidacja potrafią
wyjaśnić wpływ nowej złożoności.

**Zakres prac:**

- dopracować konektom, opóźnienia przewodzenia i sanity checks stabilności
  neural mass;
- rozwijać neuromodulację jako jawne parametry profili, nie ukryte stałe w
  kodzie;
- mierzyć koszt współsymulacji SNN w trybach `report_only` i `closed_loop` na
  tych samych konfiguracjach;
- utrzymywać kontrakt wymiany sygnałów neural-mass ↔ SNN z jawnie opisanymi
  jednostkami i skalowaniem;
- rozszerzać EEG/BOLD dopiero po zdefiniowaniu kryteriów jakości i ograniczeń
  interpretacyjnych.

**Kryteria ukończenia:**

- nowe parametry biologiczne są konfigurowalne i testowane;
- raport pokazuje wpływ rozszerzenia na metryki i stabilność;
- koszt obliczeniowy wariantu SNN jest opisany przed udostępnieniem go w GUI.

### 10.6. Kolejność najbliższych iteracji

| Iteracja | Główny rezultat | Minimalna weryfikacja |
| --- | --- | --- |
| I1 | trial-by-trial timeline dla `roving_oddball` | testy raportu i protokołu zadania |
| I2 | porównanie healthy/disorder/lesion na wspólnym seedzie | uruchomienie trzech konfiguracji i tabela metryk |
| I3 | kalibracja progów profili i rejestru walidacji | testy benchmark metadata oraz kontrola raportu |
| I4 | GUI presetów i tryb nauczyciela oparty o lekcje | testy Qt, statyczna kontrola zależności GUI |
| I5 | pomiar kosztu SNN `report_only` vs `closed_loop` | raport czasu wykonania i stabilności sygnałów |

### 10.7. Zasady ograniczające zakres

- Nie dodawać nowego modelu biologicznego, jeśli nie ma planu raportowania,
  walidacji i testów regresyjnych.
- Nie rozszerzać GUI przez kopiowanie logiki silnika; GUI ma przygotowywać
  konfigurację, uruchamiać eksperyment i prezentować wynik.
- Nie nadawać profilom clinical znaczenia diagnostycznego; komunikaty dla
  użytkownika muszą jasno mówić o charakterze dydaktycznym i eksploracyjnym.
- Nie zmieniać schematu konfiguracji bez walidacji, przykładu migracji albo
  czytelnego błędu dla starszych plików.

---

## 11. Zasady utrzymania roadmapy

1. Roadmapa opisuje **kierunek i zależności**, a nie zastępuje `BACKLOG.md`.
2. Po zakończeniu większego etapu należy zaktualizować:
   - statusy i artefakty w `BACKLOG.md`,
   - opis struktury w `docs/program_structure.md`, jeśli zmieniły się moduły,
   - ADR, jeśli zmieniły się granice odpowiedzialności, konfiguracja, I/O lub strategia losowości.
3. Każdy etap powinien kończyć się działającym scenariuszem, testem lub raportem, który można pokazać użytkownikowi.
4. Funkcje użytkowe, raporty i opisy scenariuszy pozostają po polsku; nazwy techniczne w kodzie i konfiguracji pozostają po angielsku.
