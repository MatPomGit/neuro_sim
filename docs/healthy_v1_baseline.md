# Baseline `healthy_v1`

## Cel profilu

`healthy_v1` jest edukacyjnym profilem bazowym używanym jako punkt odniesienia
w porównaniach z profilami klinicznymi. Profil nie modeluje jawnej patologii,
nie opisuje normy populacyjnej i nie może być interpretowany jako diagnoza
kliniczna.

## Parametry profilu

Źródłem konfiguracji profilu jest `configs/clinical_profiles/healthy_v1.yaml`.
Profil zawiera komplet pól wymaganych przez schemat `clinical_profile`:

- `id`: `healthy_v1`;
- `display_name`: `Zdrowy profil bazowy v1`;
- `mechanism`: brak jawnie modelowanej patologii i rola referencyjna;
- `affected_regions`: pusta lista, ponieważ baseline nie wskazuje regionu
  objętego patologią;
- `cognitive_functions`: kontrola poznawcza, uwaga i pamięć robocza jako funkcje
  obserwowane w zadaniach demonstracyjnych;
- `expected_effects`: opis roli baseline, ograniczeń klinicznych i oczekiwania
  stabilności regresji;
- `expected_direction`: `stable_reference`;
- `severity_level`: progi `small=0.0`, `medium=0.02`, `large=0.05`;
- `primary_metric`: `mean_abs_difference`.

## Seed i konfiguracja regresji

Dla regresji jakościowej baseline używana jest konfiguracja
`configs/roving_oddball_healthy.yaml` z `seed=21` i `rng_seed=21`. Stały seed
zapewnia powtarzalną sekwencję zadania oraz stabilne metryki raportu przy tym
samym kodzie, konfiguracji i środowisku.

Progi regresji znajdują się w
`data/validation/healthy_v1_baseline_metrics.json`. Plik jest małym artefaktem
referencyjnym JSON i zawiera:

- identyfikator formatu `healthy_v1_baseline_metrics_v1`;
- profil, scenariusz, ścieżkę konfiguracji i seed;
- oczekiwane wartości wybranych metryk raportu;
- tolerancje absolutne oraz jakościowy opis pasma metryki.

## Interpretacja metryk

Metryki baseline służą do wykrywania niezamierzonych zmian w symulacji i
raportowaniu. Test regresyjny porównuje m.in. moc alfa, sprzężenie fazowe,
średnią bezwzględną łączność, średnią metrykę behawioralną oraz średnią aktywność
proxy fMRI. Przekroczenie tolerancji oznacza konieczność sprawdzenia, czy zmiana
wynika z zamierzonej modyfikacji modelu, konfiguracji lub pipeline'u analizy.

## Ograniczenia dydaktyczne

Baseline `healthy_v1` ma charakter edukacyjno-techniczny:

- nie pochodzi z danych uczestników;
- nie jest normą kliniczną ani psychometryczną;
- nie uwzględnia wariancji populacyjnej, artefaktów akwizycji ani pełnej
  złożoności EEG/fMRI;
- nie powinien być używany do kwalifikowania osób jako zdrowych lub chorych;
- służy wyłącznie jako replikowalny punkt odniesienia dla demonstracyjnych
  porównań profili w repozytorium.
