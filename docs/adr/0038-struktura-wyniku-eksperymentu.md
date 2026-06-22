# ADR-0038: Jawna struktura wyniku eksperymentu

**Status:** proposed  
**Data:** 2026-06-22

## Kontekst

`run_experiment` budował dotychczas końcowy wynik jako luźny słownik. Taki
format był wygodny dla istniejących odbiorców API, ale utrudniał kontrolę
kompletności artefaktów reprodukowalności, metryk, raportu analizy i sygnałów
runtime. Projekt wymaga jawnego powiązania wyniku eksperymentu z konfiguracją,
środowiskiem oraz informacjami Git.

## Decyzja

Wprowadzamy `ExperimentResult` w `brain_core/simulation/results.py` jako
wewnętrzny kontrakt wyniku eksperymentu. `run_experiment` buduje tę strukturę po
zakończeniu symulacji, a następnie na granicy kompatybilności zwraca
`to_legacy_dict()`, czyli słownik zgodny z dotychczasowym API.

## Konsekwencje

Pozytywne skutki:

- wynik wewnętrzny ma jawne pola dla konfiguracji, sygnałów, metryk, raportu,
  zdarzeń prób, katalogu wynikowego, informacji Git i środowiska;
- istniejące testy i odbiorcy API nadal otrzymują słownik z dotychczasowymi
  kluczami;
- przyszłe rozszerzenia reprodukowalności mogą być dodawane do dataclass bez
  przypadkowego rozbijania słownikowego kontraktu kompatybilności.

Koszty i ryzyka:

- przez okres przejściowy utrzymujemy dwa widoki tego samego wyniku: strukturę
  wewnętrzną oraz format legacy;
- stabilność kluczy legacy wymaga testu statycznego/kontraktowego.

## Alternatywy rozważane

1. Pozostawienie wyłącznie słownika wynikowego — najprostsze, ale nadal ukrywa
   wymagane pola reprodukowalności i utrudnia kontrolę kontraktu.
2. Zwracanie `ExperimentResult` bez warstwy zgodności — czytelniejsze
   wewnętrznie, ale byłoby breaking change dla obecnych odbiorców API.
3. Dodanie osobnej funkcji fabrykującej słownik bez dataclass — ogranicza diff,
   ale nie daje typowanego, jawnego nośnika semantyki wyniku eksperymentu.

## Powiązane dokumenty / issue / PR

- `brain_core/simulation/results.py`
- `brain_core/simulation/engine.py`
- `tests/test_experiment_result.py`
- ADR-0028: Artefakty reprodukowalności w katalogu wynikowym
- ADR-0030: Kontrakty danych między modułami `brain_core`
