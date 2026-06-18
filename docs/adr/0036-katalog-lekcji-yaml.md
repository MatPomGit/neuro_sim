# ADR-0036: Katalog lekcji dydaktycznych oparty o YAML

**Status:** accepted
**Data:** 2026-06-18

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
Kontrakt autorski, wymagane pola i procedurę dodawania wpisów utrzymujemy w
`docs/lesson_catalog_guidelines.md`.

Kompletna karta lekcji zawiera również jawny profil i task, checklistę etapów,
opis oczekiwanego raportu oraz kryteria oceny odpowiedzi. Te pola są źródłem
dla trybu nauczyciela, planu lekcji i karty pracy studenta. Eksport pakietu
zapisuje wykresy jako osobne pliki PNG, aby materiały nie zależały wyłącznie od
osadzenia w PDF.

## Konsekwencje

Pozytywne skutki:

- jedno źródło prawdy dla lekcji dydaktycznych,
- mniejsze ryzyko niespójności między GUI i plikami YAML,
- statyczne testy mogą weryfikować kompletność katalogu lekcji.
- prowadzący otrzymuje spójną checklistę, oczekiwany raport i kryteria oceny,
- eksport może wygenerować plan oraz kartę pracy bez ręcznego kopiowania treści.

Koszty:

- import sekcji szybkiego startu może zgłosić błąd walidacji, jeśli plik lekcji
  jest niekompletny,
- dodanie nowej lekcji wymaga utrzymania kompletnego pliku YAML zgodnego z
  kontraktem katalogu.
- zmiana kontraktu pól wymaga jednoczesnej aktualizacji loadera, testów,
  dokumentacji oraz istniejących kart lekcji.

## Alternatywy rozważane

- Pozostawienie listy w `qt_sections.py`: prostsze lokalnie, ale utrzymuje dwa
  źródła prawdy.
- Generowanie listy lekcji bez walidacji: mniej kodu, ale błędy pojawiałyby się
  dopiero podczas pracy użytkownika w GUI.

## Powiązane dokumenty / issue / PR

- `configs/lessons/*.yaml`
- `brain_model/qt_sections.py`
- `tests/test_lesson_configs_static.py`
- `docs/lesson_catalog_guidelines.md`
