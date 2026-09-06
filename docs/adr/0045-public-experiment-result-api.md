# ADR-0045: Publiczny kontrakt `ExperimentResult`

Status: Accepted

## Kontekst

Silnik eksperymentu buduje kompletny `ExperimentResult`, a publiczne API ma udostępniać ten typ bez utraty zgodności z historycznym indeksowaniem słownikowym używanym przez GUI, CLI i starsze integracje.

## Decyzja

Publiczny punkt wejścia znajduje się w `brain_core.simulation.api`:

- `run_experiment(...) -> ExperimentResult` jest docelowym API;
- `brain_core.simulation.engine.run_experiment(...) -> ExperimentResult` zwraca ten sam typ bez pośredniej konwersji do słownika;
- `ExperimentResult` implementuje `Mapping[str, Any]` dla stabilnych kluczy legacy;
- `run_experiment_legacy(...) -> dict[str, Any]` jest jedyną jawną granicą kompatybilności dla integracji wymagających literalnego `dict`;
- CLI korzysta z publicznego typed API;
- nowe integracje nie powinny importować silnika bezpośrednio, mimo że jego kontrakt jest już typowany.

## Konsekwencje

Kod może korzystać z jawnych pól, np. `result.analysis_report`, `result.config` i `result.metrics`, bez utraty zgodności z istniejącym `result["time"]` oraz `result.get("save_info")`.

Przepływ wyniku jest jednokierunkowy:

```text
engine -> ExperimentResult -> public API
                         \-> run_experiment_legacy() -> dict
```

Publiczna fasada nie rekonstruuje już `ExperimentResult` z payloadu legacy. Dzięki temu metadane reprodukowalności, sygnały, wyniki triali i raport analityczny mają jedno źródło prawdy tworzone w silniku.
