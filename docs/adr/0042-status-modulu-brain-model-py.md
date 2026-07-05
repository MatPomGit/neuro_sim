# ADR-0042: Status legacy pliku `brain_model.py`

**Status:** proposed  
**Data:** 2026-07-05

## Kontekst

Repozytorium zawiera jednocześnie pakiet `brain_model/` oraz historyczny plik
`brain_model.py`. Wyszukanie referencji w kodzie, testach, dokumentacji i
konfiguracji dystrybucyjnej nie wykazało aktywnych importów pliku
`brain_model.py`. Import `import brain_model` jest rozwiązywany do pakietu
`brain_model/__init__.py`, a nie do pliku modułu w katalogu głównym.

Plik może nadal być używany poza repozytorium jako skrypt uruchamiany bezpośrednio
przez `python brain_model.py`, dlatego natychmiastowe usunięcie mogłoby być
nieczytelną zmianą dla użytkowników starszych instrukcji.

## Decyzja

Traktujemy `brain_model.py` jako tymczasowy skrypt zgodności, a nie jako część
aktywnej architektury domenowej. Plik deleguje do pakietu `brain_model/`, ma
jawny nagłówek legacy i nie jest utrwalany w wyjątkach `ruff` ani w wykluczeniu
`mypy`.

Docelowym miejscem rozwoju modelu poznawczego pozostaje pakiet `brain_model/`.
Nowe importy, testy i skrypty dystrybucyjne nie powinny odwoływać się do pliku
`brain_model.py`. Usunięcie pliku powinno nastąpić w osobnym, małym PR po
potwierdzeniu, że dokumentacja użytkowa i przykłady wskazują na `main.py`,
`brain_model/` albo `python -m brain_core.simulation.run`.

## Konsekwencje

- Podział między pakietem `brain_model/` i plikiem `brain_model.py` jest jawny.
- Narzędzia jakości nie utrzymują specjalnej ścieżki dla pliku legacy.
- Użytkownicy uruchamiający `python brain_model.py` nadal dostają demonstracyjną
  symulację, ale widzą w kodzie, że jest to ścieżka przejściowa.
- Następny PR usuwający plik będzie mały i łatwy do zrecenzowania.

## Alternatywy rozważane

1. **Natychmiastowe usunięcie `brain_model.py`** — odrzucone w tej zmianie, aby
   nie łączyć dokumentacji statusu, konfiguracji jakości i usunięcia punktu
   uruchomieniowego w jednym diffie.
2. **Pozostawienie pełnej historycznej implementacji** — odrzucone, bo utrwala
   niejasny podział odpowiedzialności i wymaga osobnych wyjątków jakości.
3. **Dodanie `brain_model.py` do dystrybucji jako modułu** — odrzucone, bo
   konfliktowałoby nazwą z pakietem `brain_model/` i zwiększało ryzyko błędów
   importu.

## Powiązane dokumenty / issue / PR

- `brain_model.py`
- `brain_model/`
- `docs/program_structure.md`
- `pyproject.toml`
