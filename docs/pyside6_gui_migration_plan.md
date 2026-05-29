# Plan migracji desktopowego GUI na PySide6

## Cel i zasada statusu

Celem migracji jest zastąpienie desktopowej ścieżki GUI opartej o `tkinter`
spójną implementacją PySide6/Qt, przy zachowaniu publicznego punktu wejścia
`brain_model.gui:run_gui` oraz skryptu `neuro-sim-gui`.

Ten dokument opisuje plan prac i kryteria ukończenia. Etapu nie należy opisywać
jako wykonanego w dokumentacji, PR ani komunikatach wydania, dopóki kod PySide6
nie obsłuży odpowiedniej funkcji w ścieżce uruchamianej przez
`brain_model.gui:run_gui`. W szczególności pełna migracja GUI może zostać
ogłoszona dopiero wtedy, gdy `brain_model.gui:run_gui` nie uruchamia już
implementacji `tkinter`.

## Założenia migracji

- Nowe elementy desktopowego GUI są tworzone w PySide6 i wzorcach Qt.
- Logika symulacji, konfiguracji i wykresów pozostaje oddzielona od widżetów.
- Teksty widoczne dla użytkownika pozostają po polsku, a nazwy techniczne w
  kodzie po angielsku.
- Format konfiguracji użytkownika pozostaje kompatybilny albo dostaje jawny
  komunikat migracyjny.
- Wykresy w desktopowym GUI korzystają z backendu Matplotlib dla Qt.
- Stara implementacja `tkinter` nie jest rozwijana o nowe funkcje; może pozostać
  wyłącznie jako kod przejściowy do czasu usunięcia zależności.

## Etapy migracji

### 1. Zależności i ADR

**Zakres**

- Potwierdzić decyzję architektoniczną o migracji do PySide6 w ADR.
- Uzgodnić minimalne wersje `PySide6`, Matplotlib i pozostałych zależności GUI.
- Zsynchronizować zależności runtime w `pyproject.toml`, `requirements.txt`,
  `environment.yml` oraz dokumentacji użytkowej.
- Opisać koszt większej zależności Qt i sposób uruchamiania w środowiskach bez
  serwera graficznego.

**Kryteria ukończenia**

- Istnieje ADR o statusie co najmniej `proposed`, zgodny z zasadami z
  `docs/architecture_decision_records.md`.
- Wszystkie pliki definicji środowiska wskazują tę samą minimalną wersję
  PySide6 albo jasno opisują powód różnicy.
- Dokumentacja uruchamiania GUI informuje, że desktopowe GUI wymaga PySide6.
- Test importu modułów Qt jest uwzględniony w zestawie kontroli jakości albo
  opisany jako kontrola ręczna w środowisku bez GUI.

### 2. Szkielet aplikacji PySide6

**Zakres**

- Utworzyć główne okno Qt z `QApplication`, `QMainWindow`, menu, paskiem stanu i
  kontenerem głównego widoku.
- Zachować kompatybilny punkt wejścia `brain_model.gui:run_gui` oraz skrypt
  `neuro-sim-gui`.
- Wydzielić moduły odpowiedzialne za aplikację, sekcje formularza, stan,
  konfigurację, workery, wykresy i style.
- Przygotować minimalny widok zastępczy, który pozwala uruchomić aplikację bez
  uruchamiania symulacji.

**Kryteria ukończenia**

- `brain_model.gui:run_gui` startuje aplikację PySide6 i nie tworzy okna
  `tkinter`.
- Aplikacja zamyka się bez pozostawiania aktywnych workerów ani wiszących
  procesów.
- Moduły Qt nie importują komponentów `tkinter` jako zależności runtime.
- Publiczne importy zachowują kompatybilność tam, gdzie jest to wymagane przez
  istniejące testy lub dokumentację.

### 3. Przeniesienie stanu

**Zakres**

- Przenieść stan formularza do dataclass niezależnej od widżetów Qt.
- Zachować jedno źródło prawdy dla scenariusza, czasu symulacji, opcji zapisu,
  parametrów modelu i wyboru wykresów.
- Ograniczyć synchronizację widżetów do jawnych metod odczytu i zapisu stanu.
- Zapewnić zgodność zapisu i odczytu konfiguracji z dotychczasowym formatem JSON
  albo udokumentować migrację.

**Kryteria ukończenia**

- Testy jednostkowe potwierdzają domyślne wartości stanu i serializację
  konfiguracji.
- Zmiana wartości w UI aktualizuje stan dopiero w przewidywalnym momencie, np.
  po zatwierdzeniu formularza albo zmianie kontrolki.
- Reset formularza przywraca komplet wartości domyślnych bez ręcznego czyszczenia
  pojedynczych widżetów poza warstwą synchronizacji.
- Nie istnieją równoległe, niespójne kopie tych samych parametrów w wielu
  obiektach widżetów.

### 4. Przeniesienie sekcji „Szybki start”

**Zakres**

- Odtworzyć podstawowy przepływ uruchamiania symulacji: wybór scenariusza, czas
  symulacji, automatyczny dobór kroku czasowego, zapis wyników i uruchomienie.
- Zachować polskie etykiety, podpowiedzi i komunikaty błędów.
- Zapewnić czytelne walidowanie wartości liczbowych przed startem symulacji.
- Podłączyć przywracanie wartości domyślnych dla pól widocznych w szybkim
  starcie.

**Kryteria ukończenia**

- Użytkownik może skonfigurować i uruchomić podstawową symulację wyłącznie z
  sekcji „Szybki start”.
- Niepoprawny czas symulacji, krok czasowy lub brak wymaganej wartości wyświetla
  polski komunikat i nie uruchamia workera.
- Opcje szybkiego startu są zapisywane do konfiguracji i odtwarzane po wczytaniu
  pliku.
- Testy albo kontrola ręczna obejmują uruchomienie z domyślnymi wartościami.

### 5. Przeniesienie opcji zaawansowanych

**Zakres**

- Przenieść edycję parametrów modelu, reguł, oscylatorów i pozostałych opcji do
  dialogów lub paneli Qt.
- Zachować opisy parametrów i polskie etykiety użytkownika.
- Walidować typy wartości przed zapisaniem do stanu.
- Zapewnić anulowanie zmian bez modyfikowania zatwierdzonego stanu.

**Kryteria ukończenia**

- Każdy parametr dostępny wcześniej w opcjach zaawansowanych jest dostępny w
  odpowiedniku Qt albo ma udokumentowaną decyzję o usunięciu.
- Kliknięcie „Anuluj” nie zmienia stanu symulacji.
- Błędna wartość liczbowa blokuje zapis i wskazuje pole wymagające korekty.
- Testy walidują przynajmniej konwersję typów i brak zapisu po anulowaniu.

### 6. Przeniesienie panelu wykresów

**Zakres**

- Zastąpić osadzanie Matplotlib przez backend Tk odpowiednikiem Qt
  (`FigureCanvasQTAgg`, `NavigationToolbar2QT`).
- Utrzymać logikę rysowania wykresów poza warstwą widżetów.
- Zapewnić panel przewijany albo zakładkowy dla wielu figur.
- Uporządkować presety wykresów tak, aby użytkownik nie musiał zarządzać długą
  listą szczegółowych checkboxów w podstawowym przepływie.

**Kryteria ukończenia**

- Desktopowe GUI PySide6 nie importuje backendu Tk Matplotlib.
- Panel wykresów pokazuje wyniki symulacji po zakończeniu workera bez blokowania
  wątku UI.
- Presety wykresów działają deterministycznie i są zapisywane w konfiguracji.
- Szczegółowe opcje wykresów są dostępne tylko w trybie zaawansowanym albo w
  osobnym panelu, jeśli są nadal potrzebne.

### 7. Migracja workerów z `threading.Thread` na `QThread` albo `QRunnable`

**Zakres**

- Przenieść uruchamianie symulacji w tle na mechanizm Qt: `QThread` dla prostego
  workera z sygnałami albo `QRunnable`/`QThreadPool` dla wielu zadań.
- Komunikację z UI realizować przez sygnały Qt, bez bezpośredniej modyfikacji
  widżetów z wątku roboczego.
- Zapewnić obsługę sukcesu, błędu, postępu i zakończenia.
- Zablokować ponowne uruchomienie symulacji, gdy poprzednia nadal trwa.

**Kryteria ukończenia**

- Kod ścieżki PySide6 nie używa `threading.Thread` do uruchamiania symulacji z
  GUI.
- Worker przekazuje wynik, wyjątek i status zakończenia przez sygnały Qt.
- UI pozostaje responsywne podczas symulacji, a przycisk startu ma jednoznaczny
  stan zajętości.
- Testy albo kontrola ręczna obejmują przypadek sukcesu i przypadek błędu
  workera.

### 8. Aktualizacja testów

**Zakres**

- Zaktualizować testy importów, stanu, konfiguracji i presetów wykresów pod
  moduły PySide6.
- Dodać testy niewymagające wyświetlania okna tam, gdzie to możliwe.
- Oznaczyć testy wymagające środowiska graficznego jako zależne od możliwości
  środowiska CI.
- Usunąć lub przepisać testy, które sprawdzały szczegóły implementacji
  `tkinter`, jeśli nie opisują już publicznego zachowania.

**Kryteria ukończenia**

- `pytest` przechodzi w środowisku z zależnościami GUI albo testy GUI są jawnie
  pomijane z czytelnym powodem.
- Testy nie wymagają interakcji użytkownika.
- Istnieją testy dla zapisu/odczytu konfiguracji oraz domyślnych presetów
  wykresów.
- Testy nie utrwalają zależności od wewnętrznych nazw widżetów, jeśli wystarczy
  sprawdzić stan lub publiczną metodę.

### 9. Usunięcie zależności GUI od `tkinter`

**Zakres**

- Usunąć importy `tkinter` z aktywnej ścieżki desktopowego GUI.
- Przenieść lub usunąć legacy moduły `gui_*`, jeśli nie są już potrzebne do
  kompatybilności.
- Usunąć backend Tk Matplotlib z panelu wykresów desktopowego GUI.
- Zaktualizować dokumentację i testy, aby wskazywały PySide6 jako jedyną
  docelową bibliotekę desktopowego GUI.

**Kryteria ukończenia**

- `brain_model.gui:run_gui` uruchamia wyłącznie ścieżkę PySide6.
- W aktywnych modułach desktopowego GUI nie ma importów `tkinter` ani
  `FigureCanvasTkAgg`.
- Dokumentacja użytkowa nie instruuje dodawania nowych funkcji GUI w `tkinter`.
- Jeżeli pozostają pliki legacy, są jasno oznaczone jako historyczne i nie są
  importowane przez punkt wejścia GUI.

## Zadania dokańczane z poprzedniej listy

### Ukrycie szczegółowych checkboxów wykresów

**Zakres**

- Zastąpić domyślnie widoczną listę wielu checkboxów prostymi presetami.
- Przenieść szczegółowy wybór wykresów do trybu zaawansowanego albo zwijanego
  panelu.

**Kryteria ukończenia**

- Podstawowy widok pokazuje preset lub krótki opis wybranych wykresów zamiast
  pełnej listy szczegółowych opcji.
- Zaawansowany użytkownik nadal może odtworzyć pełny wybór wykresów, jeśli ta
  funkcja pozostaje wymagana.
- Zapis konfiguracji zachowuje informację o faktycznie aktywnych wykresach.

### Przycisk sugerowanego czasu

**Zakres**

- Dodać akcję ustawiającą sugerowany czas symulacji dla wybranego scenariusza.
- Pokazać użytkownikowi, czy wartość pochodzi z presetu, scenariusza czy
  wartości domyślnej.

**Kryteria ukończenia**

- Kliknięcie przycisku ustawia pole czasu bez modyfikowania innych parametrów.
- Dla scenariusza bez sugestii użytkownik dostaje polski komunikat i zachowuje
  dotychczasową wartość.
- Test obejmuje co najmniej scenariusz z sugestią i scenariusz bez sugestii.

### Poprawa presetu „Podstawowe”

**Zakres**

- Zdefiniować preset „Podstawowe” jako minimalny zestaw wykresów potrzebny do
  szybkiej interpretacji wyniku.
- Oddzielić preset podstawowy od diagnostycznego i pełnego.

**Kryteria ukończenia**

- Preset „Podstawowe” nie włącza specjalistycznych wykresów diagnostycznych,
  jeśli nie są potrzebne w pierwszym uruchomieniu.
- Zmiana presetu aktualizuje stan i opis widoczny dla użytkownika.
- Test potwierdza listę wykresów aktywnych w presecie „Podstawowe”.

### Uproszczenie synchronizacji `GuiState`

**Zakres**

- Ograniczyć liczbę miejsc, w których widżety ręcznie kopiują wartości do
  `GuiState`.
- Zastosować małe, jawne funkcje mapujące stan na widżety i widżety na stan.
- Unikać dwukierunkowej synchronizacji wykonywanej automatycznie w wielu
  callbackach bez potrzeby.

**Kryteria ukończenia**

- Dla każdego pola wiadomo, która metoda odczytuje wartość z UI i która metoda
  zapisuje ją do UI.
- Reset, wczytanie konfiguracji i zmiana presetu korzystają z tych samych metod
  synchronizacji.
- Testy wykrywają rozjazd między stanem a konfiguracją po zapisie i odczycie.

### Pełna dokumentacja PySide6

**Zakres**

- Uzupełnić dokumentację użytkową uruchamiania desktopowego GUI w PySide6.
- Uzupełnić dokumentację developerską o strukturę modułów Qt, zasady dodawania
  nowych paneli i sposób testowania bez interakcji użytkownika.
- Opisać najczęstsze problemy środowiskowe, np. brak bibliotek systemowych Qt
  albo brak wyświetlacza w CI.

**Kryteria ukończenia**

- Dokumentacja użytkowa wskazuje komendę uruchomienia GUI oraz wymagane
  zależności.
- Dokumentacja developerska wskazuje, gdzie dodawać nowe sekcje, workery,
  wykresy i style Qt.
- Dokumentacja nie przedstawia `tkinter` jako docelowego sposobu rozwoju
  desktopowego GUI.

## Minimalna ścieżka weryfikacji przed zamknięciem migracji

Przed uznaniem migracji za zakończoną należy wykonać albo jawnie uzasadnić brak
możliwości wykonania następujących kontroli:

```bash
ruff check .
black .
pytest
python -c "from brain_model.gui import run_gui; print(run_gui)"
```

Dla zmian wpływających na widoczny interfejs należy dodatkowo wykonać ręczną
kontrolę uruchomienia aplikacji PySide6 w środowisku z obsługą GUI oraz zapisać
wynik w opisie PR.
