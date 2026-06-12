# ADR-0027: Etykiety GUI bez zależności od tkinter

**Status:** accepted  
**Data:** 2026-06-07

## Status implementacji

Implementacja jest docelowa: współdzielone polskie etykiety znajdują się w
`brain_model/gui_labels.py`, aktywne moduły Qt nie importują `gui_forms.py`, a
test statyczny pilnuje braku zależności nowych przepływów Qt od `tkinter`.

## Kontekst

Desktopowe GUI PySide6 korzysta z tych samych polskich etykiet, opisów parametrów i stałych konfiguracyjnych co starsza warstwa formularzy tkinter. Gdy stałe pozostają w `brain_model/gui_forms.py`, aktywne moduły `brain_model/qt_*.py` muszą importować moduł legacy, który ładuje `tkinter`. To zaciera granicę między docelowym stosem Qt a warstwą kompatybilności.

## Decyzja

Wydzielamy lekki moduł `brain_model/gui_labels.py` bez zależności GUI. Moduł przechowuje współdzielone etykiety, opisy, pola reguł, mapowania komend i wersję aplikacji. Aktywne moduły PySide6 importują stałe wyłącznie z tego modułu, a `brain_model/gui_forms.py` pozostaje legacy warstwą tkinter i re-eksportuje te stałe dla dotychczasowej kompatybilności.

## Konsekwencje

Pozytywne:

- moduły `brain_model/qt_*.py` nie importują pośrednio `tkinter` przez `gui_forms.py`;
- wspólne polskie etykiety pozostają w jednym źródle prawdy;
- legacy formularze tkinter nadal działają bez zmiany publicznych nazw stałych.

Koszty:

- powstaje mały moduł prezentacyjny współdzielony przez Tk i Qt;
- test statyczny musi pilnować, aby nowe moduły Qt nie wracały do importu `gui_forms.py`.

## Alternatywy rozważane

- Duplikacja stałych w modułach Qt: odrzucona, ponieważ zwiększa ryzyko niespójnych etykiet i opisów.
- Całkowite usunięcie eksportów z `gui_forms.py`: odrzucone, ponieważ mogłoby zerwać istniejące importy legacy tkinter i testy kompatybilności.
- Pozostawienie importów z `gui_forms.py`: odrzucone, ponieważ utrzymuje niepotrzebną zależność Qt od `tkinter`.

## Powiązane dokumenty / issue / PR

- `brain_model/gui_labels.py`
- `brain_model/gui_forms.py`
- `brain_model/qt_app.py`
- `brain_model/qt_sections.py`
- `brain_model/qt_config.py`
- `tests/test_gui_dependencies_static.py`
