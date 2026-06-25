# Przepływ czasu w symulacji

Ten dokument opisuje obowiązujący przepływ liczenia czasu w aplikacji. Celem jest
uniknięcie rozbieżności między główną pętlą eksperymentu, harmonogramem faz,
współsymulacją SNN oraz walidacją konfiguracji.

## Zasady

1. `ExperimentConfig.timestep` jest bazowym krokiem czasu aplikacji.
2. Główna pętla eksperymentu wyznacza liczbę kroków przez
   `compute_step_count(duration_s, timestep)` z `brain_core/simulation/timebase.py`.
3. `SimulationScheduler.run_step` wykonuje fazy w stałej kolejności:
   bodźce, dynamika neuronalna, sprzężenia, fizjologia, hooki współsymulacji,
   logowanie, a dopiero na końcu `state.advance(dt)`.
4. Hooki współsymulacji (`CoSimulationHook`) i zadania wieloskalowe
   (`TimeScaleTask`) używają `TimeAccumulator`, żeby akumulować bazowy czas,
   uruchamiać moduły po osiągnięciu lokalnego `dt` i zwracać liczbę uruchomień.
5. Kroki synchronizacji, np. `snn.sync_dt`, muszą być dodatnią całkowitą
   wielokrotnością kroku bazowego. Do walidacji i liczenia odstępu kroków należy
   używać `is_time_multiple(...)` oraz `compute_time_stride(...)`.
6. Nie należy wprowadzać lokalnych porównań typu `abs(round(ratio) - ratio)` ani
   własnych `int(round(sync_dt / timestep))` poza `timebase.py`.

## Poprawny przepływ wykonania

```text
konfiguracja eksperymentu
        │
        ├─ walidacja: timestep > 0, sync_dt jako wielokrotność timestep
        │
        ├─ liczba kroków: compute_step_count(duration_s, timestep)
        │
        └─ pętla kroków
              ├─ SimulationScheduler.run_step(state, timestep)
              │    ├─ fazy domenowe w ustalonej kolejności
              │    ├─ CoSimulationHook.tick(...)
              │    │    └─ TimeAccumulator.run_due_steps(...)
              │    └─ state.advance(timestep)
              └─ moduły SNN używają compute_time_stride(sync_dt, timestep)
```

## Wymagania dla nowych modułów

- Nowy moduł uruchamiany rzadziej niż krok bazowy powinien dostać własny
  `TimeAccumulator` albo być podpięty jako `TimeScaleTask`/`CoSimulationHook`.
- Nowa walidacja czasu powinna importować helpery z `timebase.py`, a nie kopiować
  tolerancję numeryczną.
- Zmiana kolejności faz `SimulationScheduler.run_step` wymaga osobnego ADR.
- Testy powinny obejmować przypadki `dt == base_dt`, całkowitą wielokrotność
  `base_dt` oraz niewielkie błędy zmiennoprzecinkowe.
