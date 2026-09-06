# ADR-0045: Publiczny kontrakt `ExperimentResult`

Status: Accepted

## Kontekst

Silnik eksperymentu od dłuższego czasu buduje `ExperimentResult`, ale na granicy `run_experiment()` natychmiast konwertuje go do luźnego słownika. Utrudnia to typowanie, odkrywanie pól API i kontrolę zmian kontraktu, a jednocześnie GUI, CLI i testy nadal korzystają z historycznego indeksowania słownikowego.

## Decyzja

Publiczny punkt wejścia zostaje przeniesiony do `brain_core.simulation.api`:

- `run_experiment(...) -> ExperimentResult` jest docelowym API;
- `ExperimentResult` implementuje `Mapping[str, Any]` dla stabilnych kluczy legacy;
- `run_experiment_legacy(...) -> dict[str, Any]` jest jawną granicą kompatybilności dla integracji wymagających literalnego `dict`;
- CLI korzysta z publicznego typed API;
- wewnętrzny `brain_core.simulation.engine.run_experiment` pozostaje tymczasowo backendem legacy, aby nie mieszać zmiany publicznego kontraktu z refaktorem dużego modułu silnika.

## Konsekwencje

Kod może korzystać z jawnych pól, np. `result.analysis_report`, `result.config` i `result.metrics`, bez utraty zgodności z istniejącym `result["time"]` oraz `result.get("save_info")`. Nowe integracje powinny importować API z `brain_core.simulation` albo `brain_core.simulation.api`, a nie bezpośrednio z `engine`.

Kolejny etap może bezpiecznie zmienić wewnętrzny engine tak, aby zwracał `ExperimentResult` bez pośredniej konwersji do słownika; wtedy façade przestanie rekonstruować wynik z payloadu legacy.
