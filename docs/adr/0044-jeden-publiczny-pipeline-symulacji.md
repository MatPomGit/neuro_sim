# ADR-0044: Jeden publiczny pipeline symulacji

## Status

Accepted

## Kontekst

Repozytorium utrzymywało dwa publiczne sposoby uruchamiania symulacji. Skrypt
`main.py` tworzył bezpośrednio `CognitiveBrainModel`, natomiast
`brain_core.simulation.run` wczytywał `ExperimentConfig` i uruchamiał
`brain_core.simulation.engine.run_experiment`. GUI PySide6 również korzysta z
`run_experiment`.

Taki układ powodował, że użytkownik mógł otrzymać różne kontrakty konfiguracji,
zapisu artefaktów i analizy zależnie od wybranego polecenia. Utrudniało to
reprodukowalność i dalszą integrację tasków, konektomu oraz modelu populacyjnego.

## Decyzja

Publiczne polecenia instalowane przez pakiet `neuro-sim` i `neuro-sim-run`
prowadzą do `brain_core.simulation.run:main`. Konfiguracja YAML/JSON i
`ExperimentConfig` są jedynym wspieranym kontraktem uruchamiania eksperymentu.

`main.py` pozostaje przejściowo skryptem zgodności dla pracy bez instalacji
pakietu. Nie jest źródłem docelowej architektury i nie należy dodawać do niego
nowych funkcji domenowych.

Docelowy przepływ jest następujący:

```text
ExperimentConfig
    -> task/stimulus
    -> simulation engine
    -> model state
    -> behavioral readout
    -> EEG/BOLD/analysis
    -> ExperimentResult
    -> GUI/report
```

Kolejne zmiany mają stopniowo usuwać rozdzielenie pomiędzy symulacją ciągłą i
osobnym generowaniem wyników triali. Odpowiedzi behawioralne mają wynikać ze
stanu modelu, a nie z identyfikatora trialu i seeda. Regionalny model
Wilsona-Cowana z `brain_core.populations` jest docelowym miejscem dla dynamiki
E/I powiązanej z atlasem i konektomem. Fenomenologiczny bank oscylatorów w
`brain_model` może pozostawać tylko do czasu przeniesienia wymaganej logiki EEG.

## Konsekwencje

- CLI i GUI korzystają z tego samego silnika eksperymentów.
- Każdy nowy scenariusz musi przechodzić przez `ExperimentConfig`.
- Nie rozwijamy nowych funkcji w legacy pipeline `main.py`.
- Integracja behawioru, konektomu i regionalnego neural-mass jest wykonywana
  iteracyjnie w `brain_core`, z testami regresji po każdym kroku.
- SNN, nowe viewery i kolejne taski nie są priorytetem do czasu zamknięcia
  przepływu bodziec -> dynamika -> odpowiedź -> obserwacja.

## Alternatywy

1. Utrzymywanie dwóch równorzędnych pipeline'ów odrzucono z powodu rozjazdu
   konfiguracji, wyników i kosztu testowania.
2. Natychmiastowe przeniesienie całego `brain_model` do `brain_core` odrzucono
   jako zbyt duży, trudny do zweryfikowania refaktor.
3. Całkowite usunięcie `main.py` odłożono do czasu potwierdzenia, że dokumentacja
   i użytkownicy nie wymagają już uruchomienia legacy.
