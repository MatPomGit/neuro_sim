# ADR-0016: Migracja desktopowego GUI na PySide6

**Status:** proposed  
**Data:** 2026-05-29

## Kontekst

Obecne desktopowe GUI projektu powstało jako prosty interfejs oparty o
`tkinter`. Takie rozwiązanie było wystarczające dla podstawowego uruchamiania
symulacji, wypełniania formularzy i prezentowania wyników, ale zaczyna
ograniczać dalszy rozwój aplikacji desktopowej.

Najważniejsze ograniczenia obecnego podejścia to:

- zależność od `tkinter`, która utrudnia budowę bardziej rozbudowanych,
  współczesnych układów okien, paneli i kontrolek;
- wykorzystanie backendu Matplotlib `TkAgg`, co wiąże warstwę wykresów z
  toolkitami Tk i utrudnia spójne osadzanie wykresów w docelowym GUI Qt;
- trudniejsze tworzenie bardziej nowoczesnych interakcji, takich jak
  wielopanelowe widoki, responsywne aktualizowanie wyników, lepsza separacja
  wątku obliczeń od wątku UI oraz bardziej spójne akcje użytkownika.

Migracja powinna zachować dotychczasowy sposób uruchamiania GUI, aby nie
wprowadzać niepotrzebnej zmiany dla użytkowników i skryptów korzystających z
publicznego punktu wejścia.

## Decyzja

Docelowym toolkitem dla desktopowego GUI będzie `PySide6`. Nowe elementy GUI
należy rozwijać w modułach Qt zgodnych z istniejącym podziałem
odpowiedzialności w `brain_model/qt_*`, a wykresy osadzać przez backend
Matplotlib dla Qt.

Publiczny punkt wejścia `brain_model.gui:run_gui` pozostaje kompatybilny i
powinien nadal służyć jako stabilna funkcja uruchamiająca GUI. Wewnętrznie może
on delegować do implementacji PySide6, dzięki czemu użytkownicy zachowują
znany interfejs uruchomieniowy, a projekt może stopniowo wycofywać zależności
od Tk w nowych przepływach desktopowych.

## Konsekwencje

Pozytywne:

- desktopowe GUI zyskuje spójny kierunek rozwoju oparty o Qt i `PySide6`;
- zachowany zostaje kompatybilny punkt wejścia `brain_model.gui:run_gui`;
- wykresy mogą korzystać z backendu Qt zamiast `TkAgg`, co zmniejsza
  sprzężenie nowych widoków z `tkinter`;
- łatwiej będzie rozwijać bardziej nowoczesne interakcje i układy paneli.

Negatywne / koszty:

- `PySide6` staje się nową zależnością runtime dla desktopowego GUI;
- środowiska użytkowników i CI muszą instalować zależności Qt wymagane przez
  `PySide6`;
- testy statyczne GUI wymagają aktualizacji tak, aby obejmowały moduły Qt,
  importy PySide6 oraz kompatybilność punktu wejścia `brain_model.gui:run_gui`;
- istniejące elementy oparte o `tkinter` powinny być traktowane jako kod
  legacy/kompatybilności i nie powinny być rozwijane bez osobnej decyzji.

## Alternatywy rozważane

- Pozostanie przy `tkinter`: najniższy koszt krótkoterminowy i brak nowej
  zależności runtime, ale dalszy rozwój bardziej nowoczesnych interakcji oraz
  paneli wykresów pozostaje trudniejszy.
- `PyQt6`: technicznie bardzo zbliżone możliwości do `PySide6`, ale projekt
  wybiera `PySide6`, aby korzystać z oficjalnych bindingów Qt for Python i
  spójnie rozwijać jeden stos Qt.
- GUI webowe: ułatwia dystrybucję przez przeglądarkę i może być korzystne dla
  wybranych scenariuszy prezentacyjnych, ale zmienia model aplikacji oraz
  zwiększa zakres migracji względem lokalnego desktopowego GUI.
- Pełna aplikacja przeglądarkowa: daje największą niezależność od desktopowego
  toolkitu, ale wymagałaby osobnego frontendu, backendu aplikacyjnego i
  szerszej przebudowy sposobu uruchamiania oraz testowania.

## Powiązane dokumenty / issue / PR

- `docs/architecture_decision_records.md`
- `docs/adr/0016-migracja-gui-na-pyside6.md`
- `docs/adr/0017-panel-wykresow-qt.md`
- `brain_model/gui.py`
- `brain_model/qt_app.py`
- `brain_model/qt_plotting.py`
