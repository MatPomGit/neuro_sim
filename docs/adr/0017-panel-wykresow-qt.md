# ADR-0017: Panel wykresów oparty o QtAgg

**Status:** accepted  
**Data:** 2026-05-29

## Kontekst

Funkcje `draw_*` w `brain_model/plotting.py` odpowiadają za logikę rysowania wykresów i powinny pozostać niezależne od konkretnego GUI. Jednocześnie docelowy interfejs desktopowy działa w PySide6, więc osadzanie figur Matplotlib przez backend Tk (`FigureCanvasTkAgg`, `NavigationToolbar2Tk`) tworzy zbędne powiązanie z poprzednią implementacją okna.

## Decyzja

Panel kontenerowy wykresów przenosimy do `brain_model/qt_plotting.py` jako `QtPlotPanel`. Panel używa `FigureCanvasQTAgg` i `NavigationToolbar2QT`, a `brain_model/qt_results.py` pozostaje odpowiedzialny tylko za dodawanie wykresów wybranych w `QtGuiState.plots`.

Funkcje `draw_*` pozostają w `brain_model/plotting.py` i nadal przyjmują oś Matplotlib oraz dane wejściowe, bez zależności od widżetów Qt albo Tk.

## Konsekwencje

Pozytywne:

- logika rysowania jest testowalna niezależnie od GUI,
- desktopowe GUI PySide6 nie importuje backendu Tk Matplotlib,
- wybór widocznych wykresów pozostaje jawny w `qt_results.py`.

Negatywne / koszty:

- moduł panelu Qt importuje prywatny mechanizm podpowiedzi linii z `plotting.py`, aby zachować dotychczasowe zachowanie interaktywne bez duplikowania kodu.

## Alternatywy rozważane

- Pozostawienie `PlotWindow` w `plotting.py`: odrzucone, bo utrzymywało zależność funkcji rysujących od Tk.
- Przepisanie funkcji `draw_*` na klasy Qt: odrzucone jako nadmierny zakres i ryzyko regresji logiki wykresów.
- Umieszczenie `QtPlotPanel` bezpośrednio w `qt_results.py`: poprawne funkcjonalnie, ale mniej czytelne, bo miesza kontener GUI z logiką wyboru wykresów.

## Powiązane dokumenty / issue / PR

- `docs/adr/0016-migracja-gui-na-pyside6.md`
- `brain_model/plotting.py`
- `brain_model/qt_plotting.py`
- `brain_model/qt_results.py`
