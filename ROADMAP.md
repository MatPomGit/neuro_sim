# ROADMAP — `neuro_sim`

## 1. Status dokumentu

**Stan na dzień:** 2026-05-29
**Zakres:** kierunek rozwoju aplikacji, kamienie milowe i zależności między strumieniami prac.
**Relacja do backlogu:** `BACKLOG.md` pozostaje operacyjną listą zadań, statusów i artefaktów. Ten dokument opisuje szerszą kolejność rozwoju oraz kryteria przejścia między etapami.

Roadmapa zakłada rozwój iteracyjny: najpierw domknięcie reprodukowalnego pipeline’u eksperymentów i raportów, następnie rozszerzenia biologiczne i kliniczne, a dopiero później warstwa platformowa oraz hybrydy mikro-makro.

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
- **Roving oddball jako zadanie referencyjne** — `roving_oddball` jest głównym scenariuszem walidującym predykcję, nowość, habituację i readaptację.

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

## 4. Stan wyjściowy na 2026-05-29

Repozytorium posiada już fundamenty potrzebne do rozwoju roadmapy:

- `brain_core/simulation/` — konfiguracja, loader, uruchamianie eksperymentów, scheduler, integratory i deterministyczne źródła RNG,
- `brain_core/experiments/` — protokoły zadań, uszkodzenia i farmakologia,
- `brain_core/anatomy/` oraz `brain_core/networks/` — atlas, konektom, sieć strukturalna i opóźnienia,
- `brain_core/populations/` — Wilson-Cowan i pilotażowy adapter spiking,
- `brain_core/analysis/` oraz `brain_core/physiology/` — metryki sygnałowe, raporty, EEG/BOLD,
- `brain_model/` — model poznawczy, scenariusze, GUI, IO, raporty i wizualizacje,
- `configs/`, `data/`, `tests/` — przykładowe konfiguracje, dane atlasu/konektomu/walidacji oraz testy regresyjne.

Najważniejsze braki do domknięcia przed rozwojem funkcji zaawansowanych:

1. jeden spójny schemat konfiguracji dla wszystkich eksperymentów,
2. pełny raport timeline trial-by-trial,
3. wersjonowany baseline `healthy_v1`,
4. dedykowany artefakt `roving_oddball`,
5. pełniejsze raporty porównawcze healthy/disorder/lesion,
6. jednolita dokumentacja uruchamiania i interpretacji scenariuszy.

---

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

---

## 6. Roadmapa etapami

### Etap 0 — Porządkowanie stanu i kontraktów dokumentacyjnych

**Horyzont:** natychmiast / przed kolejnymi zmianami strukturalnymi
**Priorytet:** P0
**Status:** częściowo zrealizowany

**Cele:**

- Utrzymać `BACKLOG.md` jako listę prac z jasnym statusem i pozostałym zakresem.
- Utrzymać `docs/program_structure.md` jako opis rzeczywistej struktury repozytorium.
- Spiąć `ROADMAP.md`, `BACKLOG.md`, `README.md` i `docs/todo.md` w jeden spójny obraz rozwoju.

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
**Status:** częściowo zrealizowany

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
**Status:** częściowo zrealizowany

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
**Status:** planowany dla dedykowanego `roving_oddball`

**Cele:**

- Ujednolicić bibliotekę zadań poznawczych.
- Wdrożyć `roving_oddball` jako zadanie referencyjne dla predykcji, nowości, habituacji i readaptacji.
- Zapewnić te same sekwencje bodźców dla profili healthy/disorder/lesion.

**Zakres:**

- wspólne API tasków dla `stroop`, `go_nogo`, `n_back` i `roving_oddball`,
- generator sekwencji standard/deviant z parametrami runów, jitterem i kontrolą seeda,
- metryki: novelty/surprise index, tempo habituacji, latencja readaptacji, różnice E/I i neuromodulacyjne,
- timeline trial-by-trial,
- konfiguracje `roving_oddball_healthy`, `roving_oddball_disorder_*`, `roving_oddball_lesion_*`,
- raport healthy vs disorder vs lesion.

**Artefakty docelowe:**

- dedykowany task `roving_oddball`,
- konfiguracje YAML dla wariantów profili,
- testy reprodukowalności sekwencji,
- notebook lub przewodnik dydaktyczny „Roving Oddball — od bodźca do interpretacji”.

**Kryteria ukończenia:**

- ten sam seed odtwarza identyczną sekwencję bodźców,
- raport pokazuje habituację w runie i reset odpowiedzi po zmianie standardu,
- co najmniej dwa profile zaburzeń i jeden profil lesion mają odróżnialne wzorce.

---

### Etap 4 — Biblioteka profili klinicznych i uszkodzeń

**Horyzont:** po Etapie 3
**Priorytet:** P1/P2
**Status:** częściowo zrealizowany

**Cele:**

- Dostarczyć porównania healthy vs disorder vs lesion jako podstawową wartość edukacyjną.
- Umożliwić uruchomienie identycznego bodźca na wielu profilach.

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

### Etap 5 — Warstwa EEG/BOLD i tryb nauczyciela

**Horyzont:** po ustabilizowaniu scenariuszy porównawczych
**Priorytet:** P2
**Status:** częściowo zrealizowany

**Cele:**

- Połączyć symulację z metrykami znanymi z praktyki badawczej.
- Uczynić aplikację gotową do użycia podczas zajęć.

**Zakres:**

- metryki spektralne EEG, synchronizacja, phase-locking,
- uproszczone mapowanie BOLD/HRF,
- raporty z wykresami i interpretacją,
- widoki „co obserwujesz teraz?” i „dlaczego to ważne?”,
- pytania kontrolne, scenariusze lekcyjne i polskie etykiety pojęć.

**Artefakty docelowe:**

- raporty EEG/BOLD per scenariusz,
- szablony lekcji laboratoryjnych,
- rozszerzony słownik pojęć EN→PL,
- widoki edukacyjne v1.

**Kryteria ukończenia:**

- student widzi metrykę, interpretację i kontekst biologiczny w jednym raporcie,
- nauczyciel może użyć gotowego scenariusza z pytaniami kontrolnymi,
- raporty są spójne dla tasków i profili porównawczych.

---

### Etap 6 — Hybrydy mikro-makro i platforma długoterminowa

**Horyzont:** długoterminowo
**Priorytet:** P3
**Status:** częściowo zrealizowany pilotażowo dla adaptera spiking, reszta planowana

**Cele:**

- Zintegrować wybrane obwody spiking z modelem makro.
- Rozwinąć personalizację i symulacje kohortowe.
- Zbudować bibliotekę benchmarków i hipotez literaturowych.

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
Etap 5: EEG/BOLD + tryb nauczyciela
    ↓
Etap 6: mikro-makro + kohorty + benchmarki
```

Najważniejsze zależności blokujące:

- `roving_oddball` wymaga stabilnego RNG, wspólnego API tasków i raportu trial-by-trial,
- profile clinical/lesion wymagają baseline `healthy_v1` oraz porównywalnych konfiguracji,
- tryb nauczyciela wymaga gotowych raportów i spójnej terminologii PL,
- hybrydy mikro-makro wymagają stabilnego kontraktu wymiany sygnałów i ograniczeń wydajnościowych.

---

## 8. Mierniki sukcesu

### Produktowe

- liczba gotowych scenariuszy uruchamianych z konfiguracji,
- liczba profili healthy/disorder/lesion z raportem porównawczym,
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

## 10. Zasady utrzymania roadmapy

1. Roadmapa opisuje **kierunek i zależności**, a nie zastępuje `BACKLOG.md`.
2. Po zakończeniu większego etapu należy zaktualizować:
   - statusy i artefakty w `BACKLOG.md`,
   - opis struktury w `docs/program_structure.md`, jeśli zmieniły się moduły,
   - ADR, jeśli zmieniły się granice odpowiedzialności, konfiguracja, I/O lub strategia losowości.
3. Każdy etap powinien kończyć się działającym scenariuszem, testem lub raportem, który można pokazać użytkownikowi.
4. Funkcje użytkowe, raporty i opisy scenariuszy pozostają po polsku; nazwy techniczne w kodzie i konfiguracji pozostają po angielsku.
