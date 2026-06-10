# ADR-0029: Tryb porównania profili Qt i stabilne API batch

**Status:** proposed  
**Data:** 2026-06-09

## Kontekst

Porównania profili klinicznych muszą być dydaktycznie czytelne i replikowalne:
profil zdrowy powinien być uruchamiany jako referencja, a 1–2 profile zaburzeń
lub uszkodzeń powinny korzystać z tego samego seeda oraz tej samej sekwencji
bodźców. Dotychczasowe wyniki batch zawierały różnice kliniczne, ale nie miały
jednego, stabilnego kontraktu raportowego dla GUI i eksportów.

## Decyzja

Stabilizujemy API `run_task_across_clinical_profiles()` tak, aby zwracało
wspólny `stimulus_sequence_signature`, listę profili, różnice metryk,
komentarze dydaktyczne oraz tabelę porównawczą: profil, oczekiwany kierunek,
obserwowany kierunek, próg jakościowy i interpretacja.

Dodajemy pliki `configs/comparisons/*.yaml` jako lekkie zestawy porównawcze dla
`roving_oddball`, `stroop`, `go_nogo` i `n_back`. Każdy zestaw wskazuje bazową
konfigurację tasku, zdrowy profil referencyjny `healthy_v1` oraz 1–2 profile
kliniczne do porównania.

GUI Qt otrzymuje tryb „Porównaj profile”, który wybiera zestaw porównawczy YAML
i deleguje wykonanie do tego samego API batch w `brain_core`, bez duplikowania
logiki eksperymentalnej w warstwie prezentacji.

## Konsekwencje

Pozytywne:

- porównania profili są wykonywane na wspólnym seedzie i wspólnej sekwencji
  bodźców;
- GUI, raport Markdown/CSV i testy korzystają z tych samych pól API;
- zestawy porównawcze są wersjonowane w `configs/`, więc można odtworzyć wybór
  profili użyty w lekcji.

Koszty i ograniczenia:

- dochodzi nowy, mały typ pliku konfiguracyjnego poza głównym schematem
  `ExperimentConfig`;
- GUI pokazuje wynik referencyjny na wykresach, a pełne porównanie opisuje w
  raporcie i tabeli;
- komentarze pozostają dydaktyczne i symulacyjne, bez znaczenia diagnostycznego.

## Alternatywy rozważane

- Ręczny wybór trzech pełnych YAML w GUI: większa elastyczność, ale wyższe
  ryzyko porównania różnych tasków, seedów albo czasów trwania.
- Osobny runner porównań w `brain_model`: prostsze UI lokalnie, ale duplikowałby
  logikę batch i osłabiał granicę `brain_core`/`brain_model`.
- Zaszycie profili w kodzie GUI: najprostsze technicznie, ale nie spełnia wymogu
  replikowalności konfiguracji.

## Powiązane dokumenty / issue / PR

- `brain_core/simulation/engine.py`
- `brain_core/simulation/config_loader.py`
- `brain_model/qt_runner.py`
- `brain_model/qt_sections.py`
- `configs/comparisons/`
- `tests/test_task_protocols_and_engine.py`
