# Wytyczne dla agentów: rozbudowa konfiguracji multi-region

Dokument definiuje **praktyczne reguły** dla agentów przygotowujących większe warianty konfiguracji w `configs/` dla modeli regionowych Wilson-Cowan ze sprzężeniem strukturalnym i opóźnieniami.

## 1. Zakres i cel
- Rozszerzaj konfiguracje bez zmiany semantyki istniejących kluczy.
- Priorytet: powtarzalność, walidowalność, mały i czytelny diff.
- Zmieniaj tylko to, co potrzebne do nowego scenariusza.

## 2. Wymagany minimalny zestaw pól
Każda konfiguracja multi-region powinna zawierać:
- `model.regions` (lista regionów, unikalna, stała kolejność),
- `model.region_params` (pełny zestaw parametrów per region),
- `model.connectivity` (macierz NxN),
- `model.delays_steps` (macierz NxN, liczby całkowite >= 0),
- `integrator.method`, `timestep`, `seed`, `task.duration`.

## 3. Spójność macierzy i walidacja
Agent MUSI sprawdzić:
1. `len(regions) == N`.
2. `connectivity` ma dokładnie rozmiar `N x N`.
3. `delays_steps` ma dokładnie rozmiar `N x N`.
4. Każdy region z `regions` istnieje w `region_params`.
5. `tau_E > 0`, `tau_I > 0`, `gain_* > 0`.
6. `delays_steps` są całkowite i nieujemne.

## 4. Zasady doboru parametrów region-specific
- Zacznij od bazowego zestawu i modyfikuj lokalnie (bez losowego „rozstrzału”).
- Dla regionów pokrewnych funkcjonalnie używaj podobnych parametrów startowych.
- Próg (`threshold_*`) i wzmocnienie (`gain_*`) zmieniaj małymi krokami (np. 0.02–0.1).
- Wagi lokalne (`w_*`) koryguj iteracyjnie, najpierw jedną grupę parametrów naraz.

## 5. Zasady opóźnień przewodzenia
- Przekątna `delays_steps[i][i]` powinna zwykle wynosić `0`.
- Krótsze połączenia: mniejsze opóźnienia; dłuższe: większe.
- Unikaj skoków o rząd wielkości między podobnymi połączeniami bez uzasadnienia.

## 6. Nazewnictwo i organizacja plików
- Nazwa pliku: `configs/multi_region_<scenario>.yaml`.
- Dla wariantów: `..._v2.yaml`, `..._ablation.yaml`, `..._high_delay.yaml`.
- Nie nadpisuj istniejących plików demo, jeśli tworzysz nowy wariant eksperymentalny.

## 7. Weryfikacja przed zakończeniem
Agent powinien uruchomić:
- testy jednostkowe modułów sieci i opóźnień,
- prosty check składni YAML (`python -c` + `yaml.safe_load`) dla nowych plików.

## 8. Zasady dla bardziej rozbudowanych wersji
Dla konfiguracji >20 regionów:
- preferuj generację półautomatyczną (skrypt) i commituj również źródło generacji,
- dodaj sekcję metadanych (`model.metadata`) z pochodzeniem macierzy i datą,
- dodaj krótki opis scenariusza w PR: co zmieniono, dlaczego, jak sprawdzono,
- jeśli zmieniasz strukturę konfiguracji, dodaj ADR przed implementacją.
