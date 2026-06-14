# ADR-0031: Limit tabeli triali w raportach

**Status:** accepted
**Data:** 2026-06-12

## Kontekst

Raporty dydaktyczne mogą zawierać długie osie trial-by-trial. Pełna tabela jest
przydatna w eksportach HTML/Markdown, bo te formaty są łatwe do przeszukiwania i
archiwizacji. PDF powinien pozostać krótszy i czytelny, ale bez ukrywania faktu,
że część triali została pominięta.

## Decyzja

Dodajemy pola `analysis.max_report_trials` i
`analysis.include_full_trial_table` do schematu konfiguracji. Pierwsze pole jest
nieujemnym limitem skróconych sekcji raportowych, a drugie kontroluje, czy
eksport HTML/Markdown ma domyślnie zapisać komplet triali. Eksport PDF zawsze
stosuje limit i raportuje liczbę pominiętych triali.

## Konsekwencje

- Konfiguracja kontroluje długość skróconych raportów bez zmiany danych
  źródłowych ani wyników symulacji.
- HTML/Markdown mogą służyć jako pełniejszy artefakt audytowy trial-by-trial, ale konfiguracja może świadomie przełączyć je w tryb skrócony.
- PDF pozostaje zwięzły, ale jawnie informuje o pominięciach.
- Wartość `0` jest dozwolona i oznacza świadome ukrycie wierszy triali w
  skróconym widoku.

## Alternatywy rozważane

- Limit w `output.max_report_trials`: odrzucono jako mniej precyzyjny, bo limit
  dotyczy interpretacyjnej sekcji analizy, a nie samego katalogu wynikowego.
- Jeden globalny limit dla wszystkich formatów: odrzucono, ponieważ HTML/Markdown
  i PDF mają różne zastosowania użytkowe.
- Brak limitu w PDF: odrzucono ze względu na czytelność i rozmiar raportów.

## Powiązane dokumenty / issue / PR

- `brain_core/simulation/config_schema.py`
- `brain_core/analysis/reports.py`
- `brain_model/report_export.py`
