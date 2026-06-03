# Przewodnik `roving_oddball`

`roving_oddball` jest scenariuszem referencyjnym do obserwacji predykcji sensorycznej,
nowości, habituacji i readaptacji po zmianie regularności bodźców. Zadanie używa
jawnego seeda, dlatego ta sama konfiguracja generuje tę samą sekwencję triali i
pozwala porównywać profile `healthy`, `disorder` oraz `lesion` bez mieszania efektów
profilu klinicznego z losowością bodźców.

## Pojęcia w sekwencji

- **Standard** — powtarzający się bodziec o tej samej częstotliwości tonu. Kolejne
  standardy w ramach runu zwiększają przewidywalność bodźca i budują habituację.
- **Deviant** — bodziec odbiegający od aktualnego standardu. W modelu jest
  oznaczany warunkiem `deviant`, ma dodatni `surprise_index` i reprezentuje sygnał
  naruszenia oczekiwania.
- **Nowy standard** — pierwszy standard po dewiancie. Ma tę samą częstotliwość co
  poprzedni dewiant i rozpoczyna kolejny run adaptacji, dlatego w payloadzie trialu
  jest oznaczony jako `is_new_standard`.
- **Habituacja** — stopniowy wzrost przewidywalności w runie standardów. Metryka
  `habituation_level` rośnie od początku do końca runu, a raport agreguje średnie
  tempo przyrostu jako `habituation_rate`.
- **Surprise index** — indeks zaskoczenia przypisany do trialu. Standardy mają
  wartość bliską zera, a dewiant ma dodatnią wartość ograniczoną do zakresu 0–1.
  Raport pokazuje `mean_surprise_index`, czyli średnią po całej sekwencji.
- **Readaptacja** — okres ponownego dopasowania po dewiancie, gdy dewiant staje się
  nowym standardem. Raport agreguje dodatnie wartości `readaptation_latency` jako
  `mean_readaptation_latency`.

## Raport dla pojedynczego uruchomienia

Dla zadania `roving_oddball` raport analizy zawiera sekcję **Raport roving oddball**.
Sekcja agreguje:

1. liczbę triali `standard`, `deviant` i `nowy standard`;
2. średni `surprise_index`;
3. tempo habituacji (`habituation_rate`), liczone jako średni dodatni przyrost
   `habituation_level` między kolejnymi standardami tego samego runu;
4. latency readaptacji (`mean_readaptation_latency`), liczone jako średnia dodatnich
   wartości `readaptation_latency`.

Te metryki należy interpretować jako wskaźniki dydaktyczne i regresyjne dla
symulacji, a nie jako zwalidowane markery kliniczne.

## Porównanie profili przy tym samym seedzie

Porównanie `healthy`/`disorder`/`lesion` powinno zachowywać ten sam `seed` i tę samą
sekcję `task`, aby każdy profil otrzymał identyczną sekwencję standardów,
dewiantów i nowych standardów. W kodzie zapewnia to funkcja
`run_task_across_clinical_profiles`, która uruchamia wspólną konfigurację bazową dla
kolejnych profili klinicznych i dodaje `roving_profile_comparison` dla zadania
`roving_oddball`.

Minimalny schemat porównania:

```python
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import run_task_across_clinical_profiles

base_config = ExperimentConfig(
    seed=21,
    task={
        "name": "roving_oddball",
        "scenario": "roving_oddball",
        "duration": 30.0,
        "n_runs": 6,
        "run_length_min": 3,
        "run_length_max": 6,
        "deviant_probability": 1.0,
        "inter_stimulus_interval": 0.8,
        "jitter": 0.05,
    },
    output={"save_results": False},
)

batch = run_task_across_clinical_profiles(
    base_config,
    [healthy_profile, disorder_profile, lesion_profile],
)
```

Wynik `batch["roving_profile_comparison"]` zawiera flagi `same_seed` i
`same_sequence`, grupę porównawczą `profile_group` (`healthy`, `disorder` albo
`lesion`) oraz agregaty `mean_surprise_index`, `habituation_rate` i
`mean_readaptation_latency` dla każdego profilu. Jeżeli `same_sequence` ma wartość
`False`, porównanie profili nie powinno być interpretowane jako czysty efekt profilu.
