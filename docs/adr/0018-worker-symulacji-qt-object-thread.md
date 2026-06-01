# ADR-0018: Worker symulacji jako QObject uruchamiany w QThread

**Status:** accepted  
**Data:** 2026-05-29

## Kontekst

Desktopowe GUI PySide6 uruchamia kosztowne obliczenia symulacji poza wątkiem
interfejsu, aby pasek postępu, status i okna komunikatów pozostawały responsywne.
Dotychczas worker dziedziczył bezpośrednio po `QThread`, co utrudniało jasne
oddzielenie obiektu roboczego od mechanizmu uruchomieniowego Qt i zachęcało do
mieszania odpowiedzialności.

## Decyzja

Worker symulacji w `brain_model/qt_runner.py` jest obiektem `QObject` z sygnałami
`progress(float)`, `done(object)`, `warning(str)` i `error(str)`. Główne okno
`brain_model/qt_app.py` tworzy osobny `QThread`, przenosi do niego workera przez
`moveToThread()` i aktualizuje pasek postępu oraz status wyłącznie w slotach
podłączonych do sygnałów Qt.

Zamykanie okna jest blokowane komunikatem użytkowym, gdy obliczenia nadal trwają.
Nie dodajemy przerwania w połowie symulacji, ponieważ obecny silnik obliczeń nie
ma jawnego, bezpiecznego tokenu anulowania i mogłoby to zostawić niespójne
artefakty wynikowe.

## Konsekwencje

Pozytywne:

- wątek GUI pozostaje jedynym miejscem aktualizacji widżetów,
- cykl życia obliczeń jest jawnie rozdzielony na worker `QObject` i `QThread`,
- zamknięcie aplikacji podczas obliczeń ma przewidywalne zachowanie.

Negatywne / koszty:

- użytkownik musi poczekać na zakończenie aktywnej symulacji przed zamknięciem
  okna,
- przyszłe anulowanie wymaga osobnej zmiany w silniku symulacji i propagacji
  kontrolowanego tokenu stopu.

## Alternatywy rozważane

- Pozostawienie dziedziczenia po `QThread`: odrzucone, bo miesza obiekt roboczy
  z mechanizmem uruchamiania i jest mniej czytelne w przepływie sygnałów Qt.
- Wymuszone zatrzymywanie wątku przy zamknięciu okna: odrzucone ze względu na
  ryzyko utraty spójności wyników oraz brak domenowego mechanizmu anulowania.
- `QThreadPool` i `QRunnable`: poprawne technicznie, ale mniej potrzebne przy
  pojedynczej aktywnej symulacji blokującej ponowne uruchomienie.

## Powiązane dokumenty / issue / PR

- `docs/adr/0016-migracja-desktop-gui-na-pyside6.md`
- `brain_model/qt_app.py`
- `brain_model/qt_runner.py`
- `BACKLOG.md` — P2 / 10 „Interfejs edukacyjny i tryb nauczyciela” oraz najbliższe prace / 11 „Migracja desktopowego GUI na PySide6 P2”
