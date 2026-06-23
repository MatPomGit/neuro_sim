# ADR-0040: Modularne walidatory sekcji konfiguracji symulacji

**Status:** proposed  
**Data:** 2026-06-23

## Kontekst

Walidacja konfiguracji eksperymentu symulacyjnego była skupiona w jednym module
`brain_core/simulation/config_schema.py`. Plik zachowywał publiczne API
`validate_config` i `ExperimentConfig`, ale jednocześnie zawierał szczegółową
logikę dla modelu, integratora, zadania, bodźców, profili, connectome,
patologii, SNN, analiz i wyjścia. Utrudniało to lokalne testowanie komunikatów
błędów oraz zwiększało ryzyko niezamierzonych zmian przy rozwijaniu pojedynczej
sekcji schematu.

## Decyzja

Pozostawiamy `brain_core/simulation/config_schema.py` jako publiczny punkt
orkiestracji walidacji oraz miejsce definicji `ExperimentConfig`, ale
szczegółowe walidatory sekcji przenosimy do pakietu
`brain_core/simulation/config_validators/`. Wspólne predykaty typów i klasa
`ConfigValidationError` trafiają do `config_validators/common.py`, aby uniknąć
zależności cyklicznych między orkiestratorem i walidatorami.

## Konsekwencje

Pozytywne:

- walidatory sekcji można rozwijać i testować lokalnie bez rozbudowywania
  centralnego modułu schematu;
- publiczne API `validate_config`, `ExperimentConfig` i `ConfigValidationError`
  pozostaje kompatybilne dla dotychczasowych importerów;
- komunikaty błędów dla sekcji konfiguracji pozostają domenowe i zawierają
  ścieżki pól.

Negatywne / koszty:

- rośnie liczba małych modułów w pakiecie symulacji;
- zmiany przekrojowe w regułach typów wymagają aktualizacji wspólnych helperów
  oraz przeglądu zależnych walidatorów.

## Alternatywy rozważane

- Pozostawienie całej walidacji w `config_schema.py`: prostsza nawigacja po
  jednym pliku, ale dalszy wzrost modułu pogarszałby czytelność i testowalność.
- Wprowadzenie klas walidatorów dla każdej sekcji: daje większą rozszerzalność,
  ale byłoby nadmiarowe względem obecnych funkcji i naruszałoby zasadę KISS.

## Powiązane dokumenty / issue / PR

- `brain_core/simulation/config_schema.py`
- `brain_core/simulation/config_validators/`
- `tests/test_config_schema.py`
