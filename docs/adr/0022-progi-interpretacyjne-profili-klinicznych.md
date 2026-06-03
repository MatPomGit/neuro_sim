# ADR-0022: Progi interpretacyjne profili klinicznych

**Status:** proposed  
**Data:** 2026-06-03

## Kontekst

Profile kliniczne są używane do deterministycznego porównywania uruchomień względem
profilu referencyjnego `healthy_v1`. Dotychczas raport wskazywał największą
różnicę, ale nie zapisywał w konfiguracji jawnych progów interpretacyjnych ani
nie tłumaczył wyniku przez mechanizm, regiony, funkcje poznawcze i oczekiwane
efekty profilu.

## Decyzja

Rozszerzamy sekcję `clinical_profile` o pola:

- `expected_direction` — oczekiwany kierunek zmiany względem profilu zdrowego,
- `primary_metric` — metryka używana do klasyfikacji różnicy,
- `severity_level` — progi `small`, `medium` i `large` dla małej, średniej i
  dużej różnicy.

Raport różnic klinicznych klasyfikuje każdą różnicę jako `mała różnica`,
`średnia różnica` albo `duża różnica` na podstawie jawnych progów profilu.
Raport dodaje też komentarz dydaktyczny, który łączy mechanizm, regiony,
funkcje poznawcze, oczekiwane efekty oraz obserwowany region i czas największej
różnicy.

## Konsekwencje

**Pozytywne:**

- interpretacja porównań klinicznych jest jawna i wersjonowana razem z profilem,
- raport lepiej nadaje się do dydaktycznej prezentacji wyników,
- testy mogą sprawdzać nie tylko obecność różnicy, ale też kontrakt pól
  interpretacyjnych.

**Negatywne / koszty:**

- progi są nadal edukacyjną heurystyką, a nie klinicznie zwalidowanym kryterium,
- zmiana zwiększa liczbę pól utrzymywanych w każdym profilu YAML.

## Alternatywy rozważane

- Progi zaszyte wyłącznie w kodzie raportu: prostsze, ale mniej replikowalne i
  trudniejsze do uzasadnienia dla pojedynczych profili.
- Osobny rejestr progów poza profilami: bardziej ogólny, ale niepotrzebnie
  zwiększa złożoność obecnego MVP.

## Powiązane dokumenty / issue / PR

- `configs/clinical_profiles/`
- `brain_core/simulation/config_schema.py`
- `brain_core/analysis/reports.py`
- `tests/test_observation_and_analysis.py`
- `docs/adr/0019-profile-kliniczne-i-raport-roznic.md`
