# ADR-0030: Kontrakty danych między modułami `brain_core`

**Status:** accepted  
**Data:** 2026-06-10

## Status implementacji

Implementacja jest docelowa: `docs/data_contracts.md` jest źródłem kontraktów
danych między modułami `brain_core`, a istniejące testy kształtów, zakresów i
metryk pełnią rolę lekkiej straży regresji.

## Kontekst

Moduły `brain_core/anatomy`, `brain_core/networks`, `brain_core/populations`,
`brain_core/synapses` i `brain_core/physiology` wymieniają tablice o wspólnej
kolejności regionów, ale wymagania dotyczące jednostek, kształtów i
replikowalności były dotąd rozproszone między docstringami i testami. Przed
dodawaniem nowych profili neuromodulacji, opóźnień przewodzenia oraz metryk
EEG/BOLD potrzebna jest jedna granica kontraktowa.

## Decyzja

Dodajemy `docs/data_contracts.md` jako dokument źródłowy dla kontraktów danych
między wymienionymi modułami. Kontrakty opisują:

- jednostki i interpretację wielkości numerycznych;
- kształty tablic oraz kolejność indeksowania regionów;
- wymagane pola konfiguracji eksperymentu;
- zasady deterministyczności i jawnego użycia RNG;
- bramkę jakościową dla przyszłych rozszerzeń neuromodulacji, opóźnień oraz
  metryk EEG/BOLD.

Testy kształtów i zakresów wartości w istniejących plikach testowych traktujemy
jako lekką automatyczną straż kontraktów.

## Konsekwencje

Pozytywne:

- granice między modułami są jawne i łatwiejsze do weryfikacji w review;
- nowe metryki lub profile muszą zadeklarować jednostki, kształty i
  deterministyczność przed implementacją;
- testy szybciej wykryją regresje kształtów, zakresów i kolejności regionów.

Koszty i ograniczenia:

- dokument trzeba aktualizować przy zmianie semantyki tablic lub konfiguracji;
- kontrakty nie zastępują pełnej walidacji runtime dla każdego możliwego wejścia;
- obecny zakres stabilizuje istniejące API, bez dodawania nowych profili,
  opóźnień ani metryk.

## Alternatywy rozważane

- Pozostawienie kontraktów wyłącznie w docstringach: mniej plików, ale większe
  ryzyko niespójności między modułami.
- Wprowadzenie nowych klas DTO dla każdego przepływu danych: silniejsze typowanie,
  ale zbyt duża zmiana strukturalna względem aktualnego celu stabilizacji.
- Opis kontraktów tylko w ADR: dobry kontekst decyzyjny, ale niewygodny jako
  codzienna referencja implementacyjna.

## Powiązane dokumenty / issue / PR

- `docs/data_contracts.md`
- `docs/program_structure.md`
- `tests/test_atlas_connectome.py`
- `tests/test_wilson_cowan_network.py`
- `tests/test_signal_metrics_modules.py`
