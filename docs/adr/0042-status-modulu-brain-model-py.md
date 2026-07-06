# ADR-0042: Usunięcie legacy pliku `brain_model.py`

**Status:** accepted  
**Data:** 2026-07-06

## Kontekst

Repozytorium zawiera pakiet `brain_model/`, który jest właściwym publicznym API
modelu poznawczego. Historyczny plik `brain_model.py` w katalogu głównym pełnił
wcześniej rolę przejściowego skryptu zgodności dla polecenia
`python brain_model.py`.

Weryfikacja referencji w kodzie, testach, dokumentacji i konfiguracji
dystrybucyjnej nie wykazała aktywnych importów tego pliku. Import
`import brain_model` jest rozwiązywany do pakietu `brain_model/__init__.py`, a
nie do pliku modułu w katalogu głównym. Utrzymywanie dodatkowego skryptu legacy
zwiększało niejednoznaczność nazw i wymagało osobnej ścieżki demonstracyjnej bez
wartości dla aktywnej architektury.

## Decyzja

Usuwamy root-level `brain_model.py` jako skrypt legacy. Polecenie
`python brain_model.py` nie jest już wspieranym sposobem uruchamiania
demonstracji.

Docelowymi punktami wejścia pozostają:

- `main.py` oraz skrypt `neuro-sim` dla szybkiej symulacji poznawczej;
- `python -m brain_core.simulation.run` oraz skrypt `neuro-sim-run` dla
  uruchomień konfigurowanych plikiem;
- importy z pakietu `brain_model/` dla kodu bibliotecznego;
- `main_gui.py` oraz `brain_model.gui:run_gui` dla desktopowego GUI.

Nowe importy, testy, przykłady i skrypty dystrybucyjne nie powinny odwoływać się
do usuniętego pliku `brain_model.py`.

## Konsekwencje

- Znika niejednoznaczność między pakietem `brain_model/` a plikiem
  `brain_model.py` w katalogu głównym.
- Nie utrzymujemy dodatkowej warstwy demonstracyjnej wyłącznie dla starszego
  polecenia `python brain_model.py`.
- Użytkownicy starszych instrukcji muszą przejść na `main.py`, `neuro-sim`,
  `neuro-sim-run` albo `python -m brain_core.simulation.run`.
- Konfiguracja dystrybucyjna pozostaje jawna: root-level modułami są tylko
  wspierane punkty wejścia `main` i `main_gui`.

## Alternatywy rozważane

1. **Pozostawienie cienkiego skryptu legacy** — odrzucone, ponieważ utrwala
   historyczny punkt wejścia i wymaga dalszego utrzymywania równoległej ścieżki
   demonstracyjnej.
2. **Delegacja `brain_model.py` do `main.py`** — odrzucona, ponieważ nadal
   pozostawiałaby konfliktującą nazwę root-level i wspierała starsze polecenie,
   które ma zostać wycofane.
3. **Dodanie `brain_model.py` do dystrybucji jako modułu** — odrzucone, bo
   konfliktowałoby nazwą z pakietem `brain_model/` i zwiększało ryzyko błędów
   importu.

## Powiązane dokumenty / issue / PR

- `brain_model/`
- `main.py`
- `main_gui.py`
- `docs/program_structure.md`
- `pyproject.toml`
