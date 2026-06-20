# ADR-0025: Raport amplituda-latencja dla roving oddball

**Status:** proposed  
**Data:** 2026-06-05

## Kontekst

Scenariusz `roving_oddball` miał metryki sekwencji (`surprise_index`,
`habituation_level`, `readaptation_latency`), ale raport nie łączył ich z
amplitudą odpowiedzi modelu ani z mechanizmem profilu klinicznego. Porównanie
profilu zdrowego, zaburzenia i lezji wymaga jawnych pól konfiguracyjnych, aby
raport nie opierał się na ukrytych założeniach w kodzie.

## Decyzja

Dodajemy do `clinical_profile` opcjonalną, walidowaną sekcję
`amplitude_latency_mechanism` zawierającą tylko pola raportowe potrzebne dla
`roving_oddball`: oczekiwany kierunek amplitudy, oczekiwany kierunek
readaptacji, próg jakościowy, komentarz mechanizmu i komentarz dydaktyczny.
Raport `roving_oddball` otrzymuje podsekcję `amplitude_latency_mechanism`, a
porównanie profili otrzymuje listę porównań względem profilu zdrowego. Raport
porównawczy zapisuje też jawny wspólny seed oraz renderuje tabelę porównującą
habituację, readaptację/latencję, amplitudę proxy i komentarz
`amplitude-latency-mechanism` dla trzech profili referencyjnych.

## Konsekwencje

Pozytywne:

- raport pokazuje, jak amplituda proxy, readaptacja i mechanizm profilu są
  połączone w jednym miejscu;
- porównanie profili pokazuje wspólny seed i zwartą tabelę metryk, co ułatwia
  dydaktyczne porównanie `healthy`, `disorder` i `lesion` przy tej samej
  sekwencji bodźców;
- konfiguracja jawnie zapisuje oczekiwane kierunki i próg jakościowy;
- walidacja wykrywa literówki oraz brak wymaganych pól raportowych.

Negatywne / koszty:

- `clinical_profile` ma jedno dodatkowe pole schematu;
- amplituda w raporcie pozostaje proxy modelu i wymaga ostrożnej interpretacji;
- komentarz `amplitude-latency-mechanism` musi być opisywany jako wyjaśnienie
  mechanizmu symulacyjnego, bez sugerowania diagnozy klinicznej.

## Alternatywy rozważane

- Trzymanie komentarzy wyłącznie w dokumentacji: odrzucone, bo raport nie byłby
  replikowalny z samej konfiguracji.
- Wyliczanie kierunku oczekiwanego wyłącznie z `expected_effects`: odrzucone, bo
  pole to jest zbyt ogólne i nie rozróżnia amplitudy od readaptacji.
- Dodanie osobnej sekcji top-level konfiguracji: odrzucone, bo metadane dotyczą
  profilu klinicznego, a nie globalnej konfiguracji silnika.

## Powiązane dokumenty / issue / PR

- `brain_core/analysis/reports.py`
- `brain_core/simulation/config_schema.py`
- `configs/roving_oddball_healthy.yaml`
- `configs/roving_oddball_disorder_gaba.yaml`
- `configs/roving_oddball_lesion_hippocampus.yaml`
- `docs/roving_oddball_guide.md`
