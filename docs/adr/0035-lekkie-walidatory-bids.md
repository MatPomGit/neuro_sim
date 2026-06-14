# ADR-0035: Lekkie walidatory BIDS w `brain_core`

**Status:** proposed  
**Data:** 2026-06-14

## Kontekst

Projekt dokumentuje wymagania BIDS dla danych obrazowych mózgu oraz EEG, ale brakowało małego API, które pozwalałoby szybko sprawdzić najczęstsze błędy nazw plików i minimalnych metadanych przed uruchomieniem pełnego BIDS Validatora.

## Decyzja

Dodajemy moduł `brain_core.bids` z lekkimi walidatorami:

- struktury nazw plików raw BIDS;
- minimalnego pliku `dataset_description.json`;
- stałej wersji BIDS używanej w projekcie.

Walidatory nie zastępują pełnego BIDS Validatora. Mają działać bez zależności sieciowych i bez dodatkowych pakietów, aby można było używać ich w testach jednostkowych oraz w przyszłych przepływach importu danych.

## Konsekwencje

- Można wcześnie wykrywać błędy kolejności encji, sufiksów, rozszerzeń i wymaganych pól metadanych.
- Zakres walidacji jest celowo ograniczony do reguł lokalnych, więc pełne zbiory danych nadal wymagają uruchomienia BIDS Validatora.
- Rozszerzenie listy modalności, sufiksów lub reguł powinno być dodawane iteracyjnie wraz z testami.

## Alternatywy rozważane

1. Bezpośrednia integracja z BIDS Validator jako zależnością uruchomieniową — odrzucona, ponieważ zwiększa zależności i komplikuje szybkie testy jednostkowe.
2. Brak lokalnych walidatorów — odrzucony, ponieważ nie pomaga zapobiegać prostym błędom przed walidacją pełnego zbioru.

## Powiązane dokumenty / issue / PR

- `docs/bids_brain_imaging_requirements.md`
- `docs/bids_eeg_requirements.md`
