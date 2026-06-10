# ADR-0026: Pakiety zajęciowe GUI oparte na presetach YAML

**Status:** proposed  
**Data:** 2026-06-06

## Kontekst

Desktopowe GUI PySide6 ma wspierać prowadzenie lekcji, wybór scenariusza i eksport materiałów zajęciowych. Jednocześnie konfiguracja eksperymentów pozostaje częścią metody badawczej, dlatego GUI nie powinno utrzymywać osobnego, równoległego schematu konfiguracji ani duplikować walidacji z `brain_core/simulation/config_schema.py`.

## Decyzja

GUI traktuje pliki `configs/*.yaml` jako źródło wyboru scenariuszy. Widok lekcji mapuje gotową lekcję na etykietę istniejącego presetu YAML, a worker przekazuje dokument do loadera i schematu `brain_core`. Wybór **Lekcja** jest nadrzędny wobec pojedynczego scenariusza: wskazuje gotowy przebieg dydaktyczny, który ustawia konfigurację YAML, a scenariusz silnika wynika dopiero z tego pliku. Eksport zajęciowy jest realizowany przez `brain_model/report_export.py` jako pakiet zawierający raport HTML/PDF, migawkę konfiguracji GUI, kopię YAML, seed, metadane uruchomienia, pytania kontrolne, skrót dla prowadzącego i `plan_lekcji.md` z opcjonalną tabelą „Co zmienić w kolejnym uruchomieniu”.

## Konsekwencje

Pozytywne:

- jedno źródło prawdy dla scenariuszy i walidacji pozostaje w konfiguracjach oraz `brain_core`;
- raport zajęciowy zawiera artefakty potrzebne do odtworzenia przebiegu lekcji;
- `plan_lekcji.md` porządkuje zajęcia według stałej struktury: cel, scenariusz YAML, profil, przewidywanie, obserwacja i pytania kontrolne;
- GUI zachowuje odpowiedzialność prezentacyjną i nie odtwarza logiki protokołów zadaniowych.

Koszty:

- etykiety scenariuszy zależą od poprawnego utrzymania metadanych w plikach YAML;
- eksport pakietu zapisuje kilka plików pomocniczych, więc testy statyczne muszą pilnować spójności kontraktu I/O;
- prowadzący, który chce tabeli zmian na kolejne uruchomienie, musi przekazać ją jawnie do eksportu zamiast polegać na ukrytych domysłach GUI.

## Alternatywy rozważane

- Osobny katalog scenariuszy GUI: odrzucony, ponieważ tworzyłby równoległą konfigurację i ryzyko rozjazdu z silnikiem.
- Raport wyłącznie PDF: odrzucony, ponieważ prowadzący potrzebuje też plików tekstowych, pytań kontrolnych i metadanych do łatwego przeglądu oraz archiwizacji.
- Walidacja pól scenariusza w GUI: odrzucona na rzecz walidacji w `brain_core/simulation/config_schema.py`.

## Powiązane dokumenty / issue / PR

- `brain_model/qt_config.py`
- `brain_model/qt_runner.py`
- `brain_model/report_export.py`
- `docs/gui_lesson_scenarios_report.md`
