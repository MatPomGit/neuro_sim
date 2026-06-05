# ADR 0025: Format regresji baseline `healthy_v1`

## Status

Accepted

## Kontekst

Profil `healthy_v1` pełni rolę punktu odniesienia w edukacyjnych porównaniach
profili klinicznych. Aby wykrywać niezamierzone zmiany w metrykach baseline,
potrzebny jest mały, wersjonowany artefakt referencyjny z wartościami
oczekiwanymi i tolerancjami. Artefakt nie może zawierać dużych wyników symulacji
ani danych uczestników.

## Decyzja

Wprowadzamy plik JSON `data/validation/healthy_v1_baseline_metrics.json` w
formacie `healthy_v1_baseline_metrics_v1`. Plik zawiera metadane profilu,
konfiguracji, scenariusza i seeda oraz mapę kluczowych metryk z wartością
oczekiwaną, tolerancją absolutną i opisem jakościowego pasma interpretacji.

Format JSON jest wystarczający, ponieważ artefakt jest mały, czytelny w diffie i
łatwy do walidacji w testach bez dodatkowych zależności. Nie zapisujemy pełnych
przebiegów czasowych ani artefaktów wynikowych.

## Konsekwencje

- Testy regresyjne mogą porównywać metryki baseline bez generowania dużych
  plików wynikowych.
- Zmiana oczekiwanych metryk wymaga jawnej aktualizacji artefaktu i uzasadnienia
  w PR.
- Artefakt pozostaje edukacyjno-techniczny i nie jest źródłem norm klinicznych.
- Format można rozszerzyć w kolejnej wersji przez zmianę pola `artifact_format`.

## Alternatywy

- CSV z metrykami i tolerancjami: odrzucone, ponieważ metadane zagnieżdżone i
  opisy ograniczeń byłyby mniej czytelne.
- Zapis pełnych wyników symulacji: odrzucony ze względu na rozmiar, szum w diffie
  i ryzyko traktowania wyników jako danych empirycznych.
- Brak artefaktu referencyjnego: odrzucony, ponieważ testy musiałyby mieć progi
  zaszyte wyłącznie w kodzie testów.
