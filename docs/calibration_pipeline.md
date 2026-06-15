# Pipeline kalibracji modelu poznawczego

Ten dokument opisuje pomocniczy pipeline kalibracyjny z `brain_model/calibration.py`.
Pipeline służy do szybkiego przeglądu kandydatów parametrów modelu poznawczego i
sprawdzenia, czy przebieg spełnia podstawowe reguły stabilności, zgodności pasm EEG
oraz odpowiedzi funkcjonalnych. Nie jest to kalibracja kliniczna ani dopasowanie do
danych uczestników.

## Cel i zakres

Pipeline odpowiada na pytanie: które kombinacje wybranych parametrów `BrainParams`
warto dalej analizować w eksperymentach lub GUI?

Zakres pipeline'u jest celowo ograniczony:

- losuje albo przegląda siatkę kandydatów z jawnego `SEARCH_SPACE`;
- dla każdego kandydata uruchamia `CognitiveBrainModel.simulate()` z kontrolowanym
  ziarnem losowości;
- ocenia wynik przez `evaluate_run()`;
- zapisuje pełniejsze rekordy do JSONL oraz tabelę podsumowującą do CSV.

Pipeline nie zmienia konfiguracji źródłowych, nie modyfikuje danych surowych i nie
zapisuje dużych artefaktów sygnałowych. Wyniki są artefaktami roboczymi, które należy
traktować jako materiał do inspekcji, a nie jako dowód walidacji biologicznej.

## Wejścia

Główne parametry wejściowe funkcji `run_sweep()` i CLI:

| Parametr | Znaczenie | Uwagi replikowalności |
| --- | --- | --- |
| `scenario` / `--scenario` | Identyfikator scenariusza bodźca przekazywany do `CognitiveBrainModel`. | Powinien odpowiadać scenariuszowi z katalogu `brain_model.scenarios`. |
| `trials` / `--trials` | Liczba kandydatów parametrów do sprawdzenia. | Dla `grid` wybierany jest deterministycznie przetasowany prefiks siatki. |
| `method` / `--method` | `grid` albo `random`. | Obie strategie używają jawnego `seed`. |
| `time_horizon` / `--time` | Czas symulacji w sekundach. | Krótkie wartości nadają się do smoke testów, dłuższe do oceny stabilności. |
| `seed` / `--seed` | Bazowe ziarno losowości. | Z niego deterministycznie wyprowadzane są ziarna pojedynczych prób. |
| `output_dir` / `--output` | Katalog zapisu artefaktów kalibracji. | Domyślnie `outputs`; do testów używany jest katalog tymczasowy. |

Przestrzeń wyszukiwania jest jawnie zapisana jako `SEARCH_SPACE` i obejmuje m.in.
`noise`, `gw_threshold`, `gw_gain`, `learning_rate_semantic` oraz
`learning_rate_value`.

## Przebieg krok po kroku

1. `run_sweep()` wybiera kandydatów parametrów przez `_sample_params()`.
2. Dla każdej próby wyprowadza deterministyczne `run_seed` z bazowego `seed`.
3. Tworzy `BrainParams` przez nadpisanie domyślnych wartości kandydatem parametrów.
4. Buduje `CognitiveBrainModel` dla wskazanego scenariusza i `run_seed`.
5. Uruchamia `model.simulate(T=time_horizon)`.
6. Odbiera pełny kontrakt wyniku symulacji:
   `time`, `activity`, `diagnostics`, `oscillations`, `behavior`.
7. Przekazuje wszystkie sygnały, w tym `behavior`, do `evaluate_run()`.
8. Zapisuje rekord próby z parametrami, statusem reguł i metrykami.
9. Po zakończeniu prób zapisuje artefakty przez `save_results()`.

## Kontrakt wyniku symulacji

`CognitiveBrainModel.simulate()` zwraca pięć elementów:

```python
time, activity, diagnostics, oscillations, behavior = model.simulate(T=45.0)
```

Znaczenie elementów:

- `time` — wektor czasu symulacji;
- `activity` — aktywacje modułów poznawczych;
- `diagnostics` — błąd predykcji, neuromodulacja i global workspace;
- `oscillations` — sygnały oscylatorów Wilsona-Cowana, w tym proxy EEG i moc pasm;
- `behavior` — decyzje, latencje, pewność i zdarzenia decyzyjne.

Element `behavior` jest wymagany przez ocenę kalibracyjną, aby metryki behawioralne
w `evaluate_run()` nie opierały się wyłącznie na wartościach domyślnych.

## Reguły oceny

`evaluate_run()` raportuje trzy grupy metryk:

- `stability` — odsetek i maksymalna długość saturacji aktywacji;
- `band_alignment` — udział pasm theta/alpha/beta/gamma względem oczekiwanego
  profilu scenariusza;
- `functional` — odpowiedzi salience/interocepcji na zagrożenie, odpowiedź wartości
  na nagrodę oraz proxy trafności, fałszywych alarmów i czasu reakcji.

Pole `pass` jest wartością logiczną wynikającą z reguł:

- `trajectory_stable`,
- `bands_match`,
- `threat_response`,
- `reward_response`.

Progi są domyślnie zdefiniowane w `DEFAULT_RULES` w `brain_model/validation.py` i
mogą być przekazane jako jawne `rules` przy bezpośrednim użyciu `evaluate_run()`.

## Artefakty wyjściowe

Dla scenariusza i strategii pipeline zapisuje dwa pliki:

```text
<output_dir>/calibration_<scenario>_<method>.jsonl
<output_dir>/calibration_<scenario>_<method>.csv
```

JSONL zawiera pełny rekord każdej próby: numer próby, scenariusz, metodę, `seed`,
parametry, status reguł i metryki zagnieżdżone. CSV zawiera płaskie podsumowanie
najważniejszych pól do szybkiego sortowania i porównania.

## Przykład uruchomienia

```bash
python -m brain_model.calibration \
  --scenario reward-learning \
  --trials 20 \
  --method random \
  --time 45.0 \
  --seed 123 \
  --output outputs/calibration_reward_learning
```

Dla szybkiego smoke testu można skrócić czas i liczbę prób:

```bash
python -m brain_model.calibration --scenario reward-learning --trials 1 --time 0.02
```

## Weryfikacja regresyjna

Test `tests/test_calibration.py` uruchamia minimalny sweep, aby potwierdzić, że
aktualny kontrakt `simulate()` jest zgodny z pipeline'em kalibracji i że zapisywane
są oba artefakty wynikowe. Przy zmianach kontraktu symulacji, walidacji albo zapisu
wyników należy zaktualizować test oraz ten dokument.

## Ograniczenia interpretacyjne

- Metryki są syntetyczne i edukacyjne; nie służą do diagnozy klinicznej.
- Profile pasm EEG są uproszczonymi oczekiwaniami scenariuszy, a nie normami
  populacyjnymi.
- Krótkie przebiegi nadają się tylko do testów technicznych; ocena stabilności
  wymaga sensownego `time_horizon`.
- Kandydaci parametrów pochodzą z małej, jawnej przestrzeni wyszukiwania i nie
  zastępują systematycznej walidacji eksperymentalnej.
