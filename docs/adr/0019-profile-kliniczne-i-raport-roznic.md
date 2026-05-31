# ADR-0019: Profile kliniczne i raport różnic między uruchomieniami

**Status:** accepted  
**Data:** 2026-05-30

## Kontekst

Symulacje kliniczne muszą porównywać warianty patologii przy tym samym zadaniu i tym samym ziarnie losowości. Bez jawnych profili w plikach konfiguracyjnych różnice między uruchomieniami są trudniejsze do odtworzenia i powiązania z mechanizmem klinicznym.

## Decyzja

Dodajemy katalog `configs/clinical_profiles/` z profilami YAML opisującymi:

- identyfikator profilu,
- polską nazwę prezentacyjną,
- mechanizm kliniczny,
- regiony i funkcje poznawcze,
- nadpisania parametrów modelu oraz sekcji patologii.

Schemat `ExperimentConfig` waliduje sekcję `clinical_profile`, a silnik udostępnia funkcję uruchomienia tego samego taska z tym samym seedem dla wielu profili. Raport różnic wskazuje region, czas, funkcję poznawczą i mechanizm dla największej zmiany względem profilu referencyjnego.

## Konsekwencje

**Pozytywne:**

- porównania kliniczne są deterministyczne i łatwiejsze do reprodukcji,
- profile można wersjonować razem z kodem,
- raport różnic bezpośrednio wiąże wynik z mechanizmem klinicznym.

**Negatywne / koszty:**

- lista dozwolonych profili musi być utrzymywana w schemacie,
- profile są na razie lekkimi fragmentami konfiguracji, a nie pełnym systemem efektów biologicznych.

## Alternatywy rozważane

- Profile zaszyte w kodzie: prostsze technicznie, ale słabsze dla replikowalności.
- Oddzielny framework porównywania eksperymentów: zbyt duży narzut względem obecnego zakresu.

## Powiązane dokumenty / issue / PR

- `configs/clinical_profiles/`
- `brain_core/simulation/config_schema.py`
- `brain_core/simulation/config_loader.py`
- `brain_core/simulation/engine.py`
- `brain_core/analysis/reports.py`
