# Presety SCENARIO_YAML dla GUI PySide6

Ten dokument opisuje gotowe pliki YAML wybierane w sekcji **Szybki start**
interfejsu PySide6. Każdy preset jest ładowany przez `brain_core` jako pełna
konfiguracja eksperymentu, dzięki czemu GUI nie odtwarza logiki tasków ani
nie konstruuje sekwencji bodźców poza silnikiem symulacji.

| Etykieta w GUI | Plik YAML | Cel dydaktyczny |
| --- | --- | --- |
| Roving oddball — zdrowy | `configs/roving_oddball_healthy.yaml` | Profil referencyjny bez patologii, używany do obserwacji standardów, dewiantów, habituacji i readaptacji. |
| Roving oddball — zaburzenie GABA | `configs/roving_oddball_disorder_gaba.yaml` | Porównanie wpływu obniżonej inhibicji GABA na szum, stabilność uwagi i odpowiedź na dewiant. |
| Roving oddball — lezja hipokampa | `configs/roving_oddball_lesion_hippocampus.yaml` | Pokazanie, jak słabsza integracja epizodyczna wpływa na wykrywanie nowości oraz readaptację. |
| SNN — demo hipokampa | `configs/snn_hippocampus_demo.yaml` | Demonstracja sprzężenia lokalnego obwodu SNN regionu HIP z modelem masowym w trybie closed-loop. |

## Zasady utrzymania

- Nowy preset SCENARIO_YAML powinien być kompletnym plikiem YAML przechodzącym
  walidację `brain_core.simulation.config_loader.load_config`.
- Każdy preset powinien mieć polską etykietę i opis w
  `brain_model.qt_config.SCENARIO_YAML_DESCRIPTIONS`.
- Jeśli preset dotyczy profilu klinicznego, musi zawierać pola
  `clinical_profile.mechanism`, `clinical_profile.affected_regions` oraz
  `clinical_profile.cognitive_functions`.
- GUI może wybierać i opisywać preset, ale wykonanie eksperymentu pozostaje po
  stronie `brain_core.simulation.engine.run_experiment`.
