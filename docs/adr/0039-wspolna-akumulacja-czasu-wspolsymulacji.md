# ADR-0039: Wspólna akumulacja czasu współsymulacji

**Status:** proposed  
**Data:** 2026-06-22

## Kontekst

`CoSimulationHook` w harmonogramie symulacji oraz `TimeScaleTask` w silniku
wieloskalowym realizowały tę samą odpowiedzialność: akumulowały bazowy krok
czasu, porównywały go z lokalnym `dt` i uruchamiały moduł po osiągnięciu progu.
Implementacje różniły się tolerancją numeryczną oraz sposobem raportowania
liczby uruchomień, co zwiększało ryzyko rozbieżności dla długich eksperymentów i
przypadków granicznych zmiennoprzecinkowych.

## Decyzja

Wprowadzamy mały komponent `TimeAccumulator` w `brain_core/simulation/timebase.py`.
Komponent odpowiada wyłącznie za deterministyczne zliczanie gotowych uruchomień
na podstawie zakumulowanego czasu i jednej wspólnej tolerancji względnej.
`CoSimulationHook` oraz `TimeScaleTask` pozostają właścicielami wywołania
modułów, ale korzystają z tego samego akumulatora i zwracają liczbę wykonań.
Nie zmieniamy kolejności faz `SimulationScheduler.run_step`.

## Konsekwencje

Pozytywne:

- jeden punkt utrzymania tolerancji numerycznej współsymulacji;
- identyczne raportowanie liczby uruchomień w hookach i zadaniach
  wieloskalowych;
- prostsze testy deterministyczności dla przypadków `dt == base_dt`,
  wielokrotności `base_dt` i małych błędów zmiennoprzecinkowych.

Negatywne / koszty:

- pojawia się dodatkowy, niewielki moduł infrastrukturalny w warstwie symulacji;
- stare introspekcje prywatnego pola `_accumulator` jako liczby zmiennoprzecinkowej
  nie są częścią publicznego API i nie powinny być używane.

## Alternatywy rozważane

- Pozostawienie dwóch implementacji i ujednolicenie tylko stałej tolerancji:
  prostsze lokalnie, ale nadal wymagałoby utrzymywania dwóch pętli akumulacji.
- Funkcja pomocnicza bez stanu: wymagałaby zwracania zarówno liczby uruchomień,
  jak i nowego resztkowego czasu, co zwiększa ryzyko błędnego użycia.
- Zmiana kolejności faz schedulera: odrzucona, ponieważ wymaga osobnej decyzji
  architektonicznej i nie jest potrzebna do ujednolicenia akumulacji czasu.

## Powiązane dokumenty / issue / PR

- `brain_core/simulation/scheduler.py`
- `brain_core/simulation/multiscale_engine.py`
- `brain_core/simulation/timebase.py`
- `docs/simulation_time_flow.md`
