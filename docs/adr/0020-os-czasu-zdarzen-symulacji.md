# ADR-0020: Oś czasu zdarzeń symulacji

**Status:** proposed
**Data:** 2026-05-31

## Kontekst

Eksperymenty symulacyjne zapisują sygnały, metryki i raporty, ale bez wspólnej struktury zdarzeń trudno powiązać wynik z konkretnym bodźcem, odpowiedzią, błędem, zmianą neuromodulacji albo profilem patologii. Replikowalna analiza wymaga osi czasu, którą można zapisać razem z artefaktami oraz pokazać w raporcie użytkownika.

## Decyzja

Dodajemy lekką strukturę `SimulationEvent` w `brain_core/simulation/events.py`. Silnik eksperymentu buduje `event_timeline` z istniejących źródeł: triali zadania, punktacji odpowiedzi, diagnostyki neuromodulacyjnej, konfiguracji patologii/profilu klinicznego oraz zmian aktywności regionów. Raport Markdown pokazuje sekcję „Oś czasu eksperymentu” i słownik pojęć EN→PL spójny z `docs/english_polish_glossary.md`. Przy zapisie wyników silnik opcjonalnie zapisuje `event_timeline.json`.

Zdarzenia powiązane z trialem muszą nieść ten sam identyfikator w dwóch
czytelnych polach:

- `trial_id` — stabilny identyfikator zgodny ze źródłem bodźca albo wyniku;
- `trial_number` — numeryczna postać używana do sortowania i grupowania
  raportów trial-by-trial.

Jeżeli zdarzenie ma słownik `details`, a dotyczy konkretnego trialu, `details`
powinno powtarzać `trial_number`. Dotyczy to nie tylko bodźców i odpowiedzi, ale
także błędów, zmian neuromodulacji oraz istotnych zmian aktywności regionów
przypisanych do przedziału czasowego trialu. Dzięki temu konsumenci raportu nie
muszą odtwarzać numeru trialu z tekstowego opisu ani z kolejności zdarzeń.

## Konsekwencje

**Pozytywne:**

- przebieg eksperymentu jest łatwiejszy do odtwórczej interpretacji,
- raport łączy metryki z konkretnymi zdarzeniami,
- zapis JSON umożliwia dalszą analizę osi czasu poza Markdownem,
- sekcje raportu trial-by-trial mogą grupować bodźce, odpowiedzi, błędy,
  neuromodulację i zmiany aktywności po wspólnym `trial_number`.

**Negatywne / koszty:**

- detekcja istotnych zmian aktywności i neuromodulacji używa prostego progu statystycznego, więc jest heurystyką diagnostyczną, a nie testem klinicznym,
- słownik terminów osi czasu trzeba utrzymywać razem ze słownikiem prezentacyjnym.

## Alternatywy rozważane

- Zapisywanie tylko surowych sygnałów: bezpośrednio replikowalne, ale trudniejsze do audytu zdarzeń.
- Osobny moduł w `brain_core/analysis/`: korzystny dla analiz post-hoc, ale zdarzenia powstają w trakcie symulacji i logicznie należą do warstwy `brain_core/simulation/`.
- Pełny system event sourcing: nadmierny narzut względem obecnego zakresu.

## Powiązane dokumenty / issue / PR

- `brain_core/simulation/events.py`
- `brain_core/simulation/engine.py`
- `brain_core/analysis/reports.py`
- `docs/english_polish_glossary.md`
