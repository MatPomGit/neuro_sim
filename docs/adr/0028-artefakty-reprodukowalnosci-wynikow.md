# ADR-0028: Artefakty reprodukowalności w katalogu wynikowym

**Status:** proposed
**Data:** 2026-06-08

## Kontekst

Katalog wynikowy symulacji zawierał podstawowe artefakty danych (`metadata.json`,
`run_data.npz`) oraz oś czasu zdarzeń (`event_timeline.json`). Taki zestaw nie
wystarczał do pełnej replikacji uruchomienia, ponieważ konfiguracja, metryki,
informacje o środowisku, stanie Git i dziennik uruchomienia nie były zapisywane
w jednym, stabilnym kontrakcie artefaktów.

## Decyzja

Rozszerzamy kontrakt katalogu wynikowego o obowiązkowe artefakty
reprodukowalności:

- `config.json` — zweryfikowana konfiguracja eksperymentu użyta w uruchomieniu;
- `metrics.json` — metryki raportu analitycznego i porównania benchmarkowe;
- `environment.json` — wersja Pythona, platforma oraz wersje zależności
  `numpy`, `matplotlib`, `PyYAML` i `PySide6`;
- `git_info.json` — commit, gałąź i informacja o niezacommitowanych zmianach;
- `run.log` — krótki dziennik zapisu artefaktów po polsku;
- dotychczasowe `metadata.json`, `run_data.npz` i `event_timeline.json`.

Kontrakt zapisujemy w warstwie I/O (`brain_model/io.py`), a silnik symulacji
przekazuje do niej konfigurację i metryki oraz zawsze zapisuje `event_timeline.json`
w przypadku włączonego zapisu wyników.

## Konsekwencje

Pozytywne:

- pojedynczy katalog wynikowy zawiera minimalny zestaw informacji potrzebny do
  audytu i powtórzenia uruchomienia;
- testy mogą statycznie sprawdzać obecność kluczy i plików bez wykonywania
  ciężkich symulacji;
- kontrakt jest jawny i może być używany przez GUI, CLI oraz przyszłe pipeline'y.

Koszty i ograniczenia:

- katalog wyniku zawiera więcej małych plików JSON;
- gdy uruchomienie odbywa się poza repozytorium Git albo bez zainstalowanej
  zależności, odpowiednia wartość w artefakcie może być `null`, ale klucz
  pozostaje obecny;
- zapis konfiguracji używa `config.json`, aby uniknąć dodatkowej zależności
  runtime dla serializacji YAML.

## Alternatywy rozważane

- Pozostawienie tylko `metadata.json`: prostsze, ale miesza metadane modelu,
  środowisko i metryki oraz utrudnia automatyczną walidację kontraktu.
- Zapis pojedynczego dużego manifestu: mniej plików, ale słabsza czytelność dla
  użytkownika i trudniejsze porównywanie wybranych sekcji między uruchomieniami.
- Wymuszanie `config.yaml`: zgodne z wieloma konfiguracjami wejściowymi, ale
  `config.json` jest wystarczający dla wymogu reprodukcji i łatwiejszy do
  stabilnej serializacji obiektów po walidacji.

## Powiązane dokumenty / issue / PR

- `brain_model/io.py`
- `brain_core/simulation/engine.py`
- `tests/test_reproducibility_artifacts.py`
- `docs/architecture_decision_records.md`
