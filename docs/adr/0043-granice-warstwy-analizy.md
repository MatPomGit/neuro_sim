# ADR-0043: Granice warstwy analizy i raportów kompatybilnościowych

**Status:** proposed  
**Data:** 2026-07-05

## Kontekst

Repozytorium zawiera właściwy pakiet analityczny `brain_core/analysis/` oraz
historyczny moduł `analysis/reports.py`. Weryfikacja użyć wykazała, że aktywny
kod aplikacji, silnika i testów importuje raporty oraz metryki z
`brain_core.analysis`, natomiast `analysis.reports.final_experiment_report` nie
ma wewnętrznych referencji poza samą definicją kompatybilnościową.

Taki układ jest mylący: nazwa katalogu `analysis/` może sugerować osobną warstwę
aplikacyjną, mimo że realna logika obliczeń i agregacji raportów znajduje się w
`brain_core/analysis/`.

## Decyzja

Docelową warstwą analizy jest `brain_core/analysis/`. Moduły w tym pakiecie mogą
liczyć metryki sygnałowe, ładować benchmarki oraz budować raporty analityczne
niezależne od GUI. Katalog główny `analysis/` nie jest rozwijany jako osobna
warstwa aplikacyjna; pozostaje wyłącznie przestrzenią kompatybilnościową dla
starszych importów.

Pierwszy mały krok migracyjny polega na przeniesieniu implementacji
`final_experiment_report` do `brain_core.analysis.reports` i pozostawieniu
`analysis.reports` jako cienkiego importu kompatybilnościowego.

## Konsekwencje

- Nowy kod ma importować raport końcowy z `brain_core.analysis.reports`.
- Starsze skrypty używające `analysis.reports.final_experiment_report` nadal
  działają bez zmiany kontraktu.
- Kolejne migracje można wykonywać stopniowo, bez jednoczesnego przenoszenia
  wielu modułów.
- Dokumentacja struktury programu jawnie rozróżnia warstwę analizy od fasady
  kompatybilnościowej.

## Alternatywy rozważane

- Usunięcie `analysis/reports.py` od razu: odrzucone, bo mogłoby przerwać
  zewnętrzne skrypty użytkowników.
- Rozwijanie `analysis/` jako osobnej warstwy aplikacyjnej: odrzucone, bo
  dublowałoby odpowiedzialność `brain_core/analysis/` i utrudniało utrzymanie
  granic pakietów.
- Przeniesienie wielu modułów jednocześnie: odrzucone zgodnie z zasadą małego,
  lokalnego kroku migracyjnego.

## Powiązane dokumenty / issue / PR

- `docs/program_structure.md`
- `brain_core/analysis/reports.py`
- `analysis/reports.py`
