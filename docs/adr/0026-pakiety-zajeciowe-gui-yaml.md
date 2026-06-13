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

## Uzupełnienie 2026-06-10

Panel szybkiego startu pokazuje opis każdej konfiguracji YAML wprost w GUI:
cel dydaktyczny, różnicę względem pozostałych presetów, scenariusz silnika,
czas z pliku YAML oraz profil kliniczny. Opis pozostaje warstwą prezentacji —
nie zmienia konfiguracji i nie odtwarza logiki tasków.

Pole „scenariusze serii (batch)” w opcjach zaawansowanych nie jest drugim
wyborem pojedynczego scenariusza. Służy wyłącznie do wielu uruchomień w trybie
serii i ma oddzielną podpowiedź, aby uniknąć mylenia go z wyborem
„konfiguracja YAML” w szybkim starcie.

Panel „Co obserwujesz?” i panel pytań kontrolnych dla roving oddball korzystają
z `event_timeline`, `clinical_profile` i `analysis_report` zwróconych przez
`run_experiment()`. GUI nadal nie importuje `brain_core.experiments.protocols`
ani nie rekonstruuje standardów, dewiantów, habituacji lub readaptacji poza
prezentacją gotowych pól raportu.

## Uzupełnienie 2026-06-12

Pakiet zajęciowy eksportowany przez `export_teaching_package()` zapisuje jawny
zestaw artefaktów reprodukowalności obok raportów dydaktycznych:
`environment.json`, `git_info.json`, rozszerzone `metadata_uruchomienia.json`,
kopię użytego pliku YAML wraz z hashem SHA-256 oraz `README_pakietu.md` z
instrukcją odtworzenia uruchomienia. Decyzja utrzymuje prosty kontrakt I/O bez
osobnego formatu archiwum: każdy artefakt pozostaje czytelnym plikiem w katalogu
pakietu.

Konsekwencją jest większy katalog eksportu, ale prowadzący może powiązać raport
z commitem, statusem dirty repozytorium, wersjami zależności i integralnością
konfiguracji YAML bez uruchamiania dodatkowych narzędzi. Odrzucono zapis tych
informacji wyłącznie w `metadata_uruchomienia.json`, ponieważ oddzielne pliki
`environment.json` i `git_info.json` są spójne z pozostałymi artefaktami
reprodukowalności projektu.
## Uzupełnienie 2026-06-13

Dodajemy katalog `configs/lessons/` jako lekki katalog gotowych lekcji. Pliki
lekcji nie zastępują konfiguracji eksperymentów: wskazują istniejący
`scenario_config`, opcjonalny `comparison_config`, cel dydaktyczny, pytania
przed i po uruchomieniu, oczekiwane obserwacje oraz propozycje zmian do
kolejnego przebiegu. Dzięki temu tryb nauczyciela może rozwijać się bez
tworzenia równoległego schematu silnika symulacji.

Minimalny katalog obejmuje lekcje dla `roving_oddball`, `go_nogo`, `n_back` i
`stroop`; testy statyczne pilnują kompletności pól oraz istnienia wskazanych
plików YAML.
