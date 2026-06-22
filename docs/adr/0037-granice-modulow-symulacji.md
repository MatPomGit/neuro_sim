# ADR-0037: Granice odpowiedzialności modułów symulacji

**Status:** proposed  
**Data:** 2026-06-21

## Kontekst

`brain_core/simulation/engine.py` agregował trzy różne poziomy odpowiedzialności:
wysokopoziomową orkiestrację eksperymentu, szczegółową logikę demonstracyjnego
sprzężenia SNN oraz budowanie raportów porównania profili klinicznych. Taki układ
utrudniał lokalną weryfikację zmian SNN i porównań batch, ponieważ modyfikacje
niskopoziomowe wymagały czytania całego silnika eksperymentu.

Jednocześnie publiczne API, zwłaszcza `run_experiment` i batchowe uruchomienie
profili klinicznych, musi pozostać stabilne dla GUI, CLI i istniejących testów.

## Decyzja

Wydzielamy odpowiedzialności w pakiecie `brain_core.simulation` następująco:

- `engine.py` pozostaje miejscem orkiestracji pojedynczego eksperymentu:
  buduje model, uruchamia symulację, składa raport analityczny, zapisuje
  artefakty i deleguje wyspecjalizowane kroki do modułów pomocniczych.
- `snn_runtime.py` przejmuje budowanie runtime SNN, wariant closed-loop,
  porównanie `baseline` / `report_only_snn` / `closed_loop_snn`, metryki śladów
  oraz klasyfikację ostrzeżeń amplitudy sprzężenia.
- `profile_comparison.py` przejmuje scalanie konfiguracji profilu klinicznego,
  wspólną sekwencję bodźców, podpis sekwencji, raport różnic profili oraz
  specyficzne porównania roving oddball.

Aby nie złamać starszych importów testowych, `engine.py` zachowuje cienkie aliasy
prywatnych helperów, ale implementacja znajduje się w nowych modułach.

## Konsekwencje

Pozytywne:

- zmiany SNN można testować i przeglądać bez naruszania orkiestracji
  eksperymentu;
- porównania profili klinicznych są oddzielone od pojedynczego uruchomienia;
- granice modułów lepiej odpowiadają kontraktom badawczym: runtime SNN,
  porównanie profili i orkiestracja eksperymentu.

Koszty:

- część prywatnych aliasów w `engine.py` pozostaje jako warstwa kompatybilności;
- `profile_comparison.py` otrzymuje runner eksperymentu i generator bodźców jako
  zależności wstrzykiwane, żeby uniknąć cyklicznego importu z `engine.py`.

## Alternatywy rozważane

1. Pozostawienie całej logiki w `engine.py` i dodanie komentarzy sekcyjnych.
   Odrzucono, bo nie zmniejsza sprzężenia modułów ani rozmiaru pliku.
2. Przeniesienie `run_experiment` do nowego modułu i pozostawienie importu
   fasadowego w `engine.py`. Odrzucono jako zbyt szeroką zmianę API w tym kroku.
3. Bezpośredni import `run_experiment` w `profile_comparison.py`. Odrzucono,
   ponieważ tworzyłby cykliczną zależność z silnikiem.

## Powiązane dokumenty / issue / PR

- ADR-0029: Tryb porównania profili Qt i stabilne API batch.
- ADR-0034: Architektura docelowego backendu SNN opartego o `brian2.Network`.
