# ADR-0036: Katalog lekcji dydaktycznych oparty o YAML

**Status:** proposed  
**Data:** 2026-06-15

## Kontekst

Desktopowe GUI zawiera sekcję „Szybki start”, w której użytkownik wybiera gotową
lekcję dydaktyczną. Dotychczas lista lekcji była utrzymywana ręcznie w kodzie
formularza Qt, mimo że metadane lekcji istnieją w `configs/lessons/*.yaml`.
Powodowało to ryzyko rozjazdu między opisem dydaktycznym a presetem YAML
uruchamianym przez silnik.

## Decyzja

Wydzielamy moduł `brain_model.lesson_catalog`, który wczytuje lekcje z katalogu
`configs/lessons`, waliduje obecność wymaganych pól i udostępnia proste API dla
warstwy GUI: listę lekcji, listę etykiet oraz wyszukiwanie po etykiecie.
Sekcja Qt korzysta z tego loadera zamiast z ręcznie utrzymywanej listy presetów.

## Konsekwencje

Pozytywne skutki:

- jedno źródło prawdy dla lekcji dydaktycznych,
- mniejsze ryzyko niespójności między GUI i plikami YAML,
- statyczne testy mogą weryfikować kompletność katalogu lekcji.

Koszty:

- import sekcji szybkiego startu może zgłosić błąd walidacji, jeśli plik lekcji
  jest niekompletny,
- dodanie nowej lekcji wymaga utrzymania kompletnego pliku YAML zgodnego z
  kontraktem katalogu.

## Alternatywy rozważane

- Pozostawienie listy w `qt_sections.py`: prostsze lokalnie, ale utrzymuje dwa
  źródła prawdy.
- Generowanie listy lekcji bez walidacji: mniej kodu, ale błędy pojawiałyby się
  dopiero podczas pracy użytkownika w GUI.

## Powiązane dokumenty / issue / PR

- `configs/lessons/*.yaml`
- `brain_model/qt_sections.py`
- `tests/test_lesson_configs_static.py`
