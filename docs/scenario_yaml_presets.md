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
| Stroop — osłabienie DLPFC | `configs/scenario_yaml_stroop_dlpfc.yaml` | Lekcja konfliktu poznawczego z osłabioną kontrolą wykonawczą i komunikacją DLPFC–ACC. |
| Go/No-Go — dysregulacja GABA | `configs/scenario_yaml_go_nogo_gaba.yaml` | Lekcja hamowania reakcji w przeciążeniu sensorycznym z obniżoną inhibicją GABA. |
| N-back — deficyt dopaminowy | `configs/scenario_yaml_n_back_dopamine.yaml` | Lekcja pamięci roboczej 2-back z kontekstem uczenia nagrody i słabszą modulacją wartościującą. |
| Stres i regeneracja — serotonina | `configs/scenario_yaml_stress_recovery_serotonin.yaml` | Lekcja epizodu stresu, wygaszania pobudzenia i ostrożniejszego progu decyzji przy zaburzeniu serotoninowym. |

## Porównanie trzech presetów roving oddball

Presety `roving_oddball_healthy`, `roving_oddball_disorder_gaba` i
`roving_oddball_lesion_hippocampus` mają wspólny seed `21` oraz tę samą sekcję
`task`. Dzięki temu można używać ich jako zestawu demonstracyjnego, w którym
raport porównawczy pokazuje `same_sequence: true` i pozwala omawiać różnice
metryk profilu bez zmiany sekwencji bodźców.

Sekcja `roving_profile_comparison` w raporcie Markdown zawiera tabelę
**Tabela porównawcza habituacja-readaptacja-amplituda-latencja** z kolumnami:

- profil i grupa profilu (`healthy`, `disorder`, `lesion`);
- `habituation_rate`;
- `mean_readaptation_latency`, opisywane w tabeli jako readaptacja/latencja;
- `response_amplitude`, czyli amplituda proxy z
  `amplitude_latency_mechanism`;
- komentarz `amplitude-latency-mechanism` z konfiguracji profilu.

Tabela służy do nauki interpretacji mechanizmów symulacyjnych. Nie wolno
traktować jej jako klasyfikatora klinicznego ani jako podstawy rozpoznania.

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
