# ADR-0022: Konfiguracje YAML i panele wyników Qt oparte na silniku

**Status:** proposed  
**Data:** 2026-06-03

## Kontekst

Desktopowe GUI PySide6 powinno służyć jako warstwa prezentacji i uruchamiania
eksperymentów, a nie jako druga implementacja protokołów zadań. Dotychczasowy
worker Qt potrafił generować minimalną konfigurację dla `brain_core`, ale część
przepływu serii używała bezpośrednio modelu domenowego. Utrudniało to
utrzymanie jednej ścieżki walidacji konfiguracji, osi czasu zdarzeń,
profilu klinicznego oraz artefaktów silnika.

Równolegle użytkownik GUI potrzebuje szybkiego wyboru gotowych scenariuszy YAML:
trzech wariantów roving oddball oraz demonstracji współsymulacji SNN hipokampa.
Te scenariusze zawierają informacje istotne dla interpretacji klinicznej i
powinny być pokazywane bez kopiowania logiki tasków do widżetów.

## Decyzja

Dodajemy w warstwie `brain_model/qt_*` wybór gotowych konfiguracji YAML jako
presetów wskazujących pliki z `configs/`. GUI może zastosować taki preset do
formularza, ale uruchomienie nadal odbywa się przez walidowany dokument
`ExperimentConfig` i funkcję `brain_core.simulation.engine.run_experiment`.

Worker Qt buduje lub ładuje konfigurację, uzupełnia wyłącznie wartości
formularza użytkownika (`duration`, `timestep`, `seed`, `save_results`) i
przekazuje całość do silnika. Wynik silnika jest jedynym źródłem danych dla:

- wykresów,
- podglądu `event_timeline`,
- panelu profilu klinicznego,
- zapisu wyników wykonywanego przez silnik.

Panele `EventTimelinePanel` i `ClinicalProfilePanel` pozostają w GUI jako
prezentacja gotowych struktur wynikowych, bez rekonstrukcji protokołów zadań.

## Konsekwencje

**Pozytywne:**

- GUI korzysta z jednej ścieżki walidacji YAML/JSON i uruchamiania silnika,
- łatwiej testować statycznie, że warstwa Qt nie importuje implementacji tasków,
- użytkownik widzi oś czasu zdarzeń i profil kliniczny pochodzące z wyniku
  eksperymentu,
- preset SNN używa tej samej konfiguracji, co uruchomienia CLI.

**Negatywne / koszty:**

- preset YAML ma pierwszeństwo nad częścią ręcznie edytowanych parametrów modelu,
  aby nie mieszać dwóch źródeł prawdy w jednym uruchomieniu,
- GUI musi utrzymywać mapowanie etykiet użytkownika na pliki YAML,
- seria batch dla presetów YAML pozostaje prostą sekwencją uruchomień silnika,
  a nie osobnym mechanizmem optymalizowanym pod wydajność.

## Alternatywy rozważane

- Reimplementacja roving oddball w GUI: odrzucona, bo dubluje `brain_core` i
  zwiększa ryzyko rozjazdu wyników.
- Osobne klasy scenariuszy Qt: odrzucone jako nadmiarowa abstrakcja względem
  prostego mapowania etykieta → plik YAML.
- Pokazywanie profilu klinicznego tylko po zapisie raportu: odrzucone, bo panel
  GUI może bezpiecznie prezentować już zwalidowane metadane konfiguracji.

## Powiązane dokumenty / issue / PR

- `brain_model/qt_config.py`
- `brain_model/qt_runner.py`
- `brain_model/qt_results.py`
- `configs/roving_oddball_healthy.yaml`
- `configs/roving_oddball_disorder_gaba.yaml`
- `configs/roving_oddball_lesion_hippocampus.yaml`
- `configs/snn_hippocampus_demo.yaml`
- ADR-0016: Migracja desktopowego GUI na PySide6
- ADR-0018: Worker symulacji jako QObject uruchamiany w QThread
- ADR-0019: Profile kliniczne i raport różnic między uruchomieniami
- ADR-0020: Oś czasu zdarzeń symulacji
