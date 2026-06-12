# ADR-0032: Szybkie walidatory kontraktów danych

**Status:** proposed  
**Data:** 2026-06-12

## Kontekst

Kontrakty danych w `docs/data_contracts.md` opisują oczekiwane kształty i
jednostki atlasu, konektomu, opóźnień przewodzenia oraz sygnałów EEG/BOLD.
Dotychczas część kontroli była rozproszona w loaderach i adapterach, przez co
raporty błędów nie zawsze wskazywały nazwę naruszonego kontraktu.

## Decyzja

Dodajemy mały moduł `brain_core.data_contracts` z szybkimi walidatorami
kształtów, skończoności wartości i podstawowych jednostek proxy. Walidatory są
uruchamiane na granicach wejścia danych: loaderach atlasu i konektomu, buforze
opóźnień, walidacji `ExperimentConfig` oraz adapterach fizjologii EEG/BOLD.

## Konsekwencje

- Błędy wejścia wskazują nazwę kontraktu z `docs/data_contracts.md`.
- Ciężka logika obliczeniowa pozostaje w dotychczasowych modułach; walidatory
  wykonują jedynie tanie kontrole kształtów i zakresów.
- Zmiany w kontraktach danych będą wymagały aktualizacji jednego wspólnego
  miejsca walidacji.

## Alternatywy rozważane

- Pozostawienie walidacji lokalnie w każdym module: mniej plików, ale większe
  ryzyko duplikacji i niespójnych komunikatów błędów.
- Pełny system typów danych z klasami pośrednimi: odrzucony jako nadmiarowy dla
  obecnego zakresu, który wymaga tylko szybkich kontroli brzegowych.

## Powiązane dokumenty / issue / PR

- `docs/data_contracts.md`
- `docs/adr/0030-kontrakty-danych-brain-core.md`
