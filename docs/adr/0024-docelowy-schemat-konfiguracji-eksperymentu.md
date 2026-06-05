# ADR-0024: Docelowy schemat konfiguracji eksperymentu symulacyjnego

**Status:** proposed  
**Data:** 2026-06-05

## Kontekst

Dotychczasowa konfiguracja eksperymentów symulacyjnych używała mieszanego
zestawu pól historycznych i opcjonalnych sekcji. Kluczowe pojęcia metodologiczne,
takie jak profil mózgu, bodziec, connectome i ziarno losowości, nie były jawnie
wyróżnione w każdym przykładzie konfiguracji. Utrudniało to walidację pełnej
ścieżki pola, migrację do bardziej replikowalnych eksperymentów oraz spójne
ładowanie YAML i JSON.

Repozytorium nadal korzysta z historycznego pola `seed`, dlatego zmiana schematu
nie może po cichu zmienić semantyki losowości ani utrudnić odtworzenia
wcześniejszych uruchomień.

## Decyzja

Wprowadzamy docelowy schemat `ExperimentConfig` z jawnymi sekcjami:
`model`, `integrator`, `task`, `stimulus`, `brain_profile`, `clinical_profile`,
`connectome`, `pathology`, `snn`, `analysis` i `output`. Ziarno losowości jest
reprezentowane przez docelowe pole `rng_seed`, przy zachowaniu kompatybilnego
pola `seed`.

Walidator mapuje `seed` na `rng_seed`, gdy konfiguracja używa tylko pola
historycznego. Jeżeli konfiguracja zawiera oba pola, ale ich wartości są różne,
walidator zgłasza jawny błąd zamiast wybierać jedną wartość po cichu.

Loader YAML i JSON kieruje surowe dane przez tę samą ścieżkę `validate_config`,
a komunikaty błędów wskazują pełną ścieżkę pola, np. `task.duration` albo
`pathology.mutations[0].target`.

## Konsekwencje

- Przykładowe konfiguracje eksperymentów zawierają komplet jawnych sekcji
  metodologicznych potrzebnych do odtworzenia uruchomienia.
- Brak wymaganej sekcji lub błędny typ jest wykrywany przed startem symulacji.
- Starsze konfiguracje z samym `seed` pozostają obsługiwane przez migrację w
  walidatorze.
- Konfiguracje zawierające sprzeczne wartości `seed` i `rng_seed` wymagają
  ręcznej korekty, aby uniknąć niejawnej niedeterministyczności.
- Fragmenty profili klinicznych nadal mogą być walidowane jako nakładki na
  konfigurację pełnego eksperymentu.

## Alternatywy rozważane

1. **Pozostawienie tylko pola `seed`** — odrzucone, ponieważ nie wskazuje jasno,
   że wartość dotyczy źródeł losowości i utrudnia docelową strukturę schematu.
2. **Natychmiastowe usunięcie `seed`** — odrzucone ze względu na kompatybilność
   konfiguracji i testów korzystających z dotychczasowego pola.
3. **Ciche preferowanie `rng_seed` przy konflikcie z `seed`** — odrzucone,
   ponieważ zmieniałoby semantykę reprodukowalności bez czytelnego błędu.

## Powiązane dokumenty / issue / PR

- `docs/architecture_decision_records.md`
- `brain_core/simulation/config_schema.py`
- `brain_core/simulation/config_loader.py`
