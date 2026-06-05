from typing import Any

import pytest

from brain_core.analysis.reports import AnalysisReport
from brain_core.cognition.mapping import functions_for_task, regions_for_task
from brain_core.experiments.protocols import (
    GoNoGoTask,
    NBackTask,
    RovingOddballTask,
    StroopTask,
    get_task,
)
from brain_core.simulation.config_loader import load_config
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import (
    run_experiment,
    run_task_across_clinical_profiles,
)


def test_tasks_generate_deterministic_stimuli() -> Any:
    """Opis funkcji test_tasks_generate_deterministic_stimuli."""
    duration = 10.0
    s1 = StroopTask().generate_stimuli(seed=7, duration_s=duration)
    s2 = StroopTask().generate_stimuli(seed=7, duration_s=duration)
    assert s1 == s2

    g1 = GoNoGoTask().generate_stimuli(seed=7, duration_s=duration)
    g2 = GoNoGoTask().generate_stimuli(seed=7, duration_s=duration)
    assert g1 == g2

    n1 = NBackTask(n=2).generate_stimuli(seed=7, duration_s=duration)
    n2 = NBackTask(n=2).generate_stimuli(seed=7, duration_s=duration)
    assert n1 == n2

    r1 = RovingOddballTask(
        n_runs=3, run_length_min=2, run_length_max=4, jitter=0.05
    ).generate_stimuli(seed=7, duration_s=duration)
    r2 = RovingOddballTask(
        n_runs=3, run_length_min=2, run_length_max=4, jitter=0.05
    ).generate_stimuli(seed=7, duration_s=duration)
    assert r1 == r2


def test_trial_results_have_unified_schema_and_are_deterministic() -> Any:
    """Opis funkcji test_trial_results_have_unified_schema_and_are_deterministic."""
    cfg = ExperimentConfig(
        task={"name": "stroop", "scenario": "stroop", "duration": 5.0},
        output={"save_results": False},
    )
    r1 = run_experiment(cfg)
    r2 = run_experiment(cfg)

    assert r1["trial_results"] == r2["trial_results"]
    assert len(r1["trial_events"]) > 0

    first = r1["trial_results"][0]
    assert set(first.keys()) == {
        "trial_id",
        "reaction_time_s",
        "correct",
        "error_type",
        "condition",
        "regional_input",
    }
    assert isinstance(first["correct"], bool)


def test_all_task_configs_exist() -> Any:
    """Opis funkcji test_all_task_configs_exist."""
    pytest.importorskip("yaml")
    from pathlib import Path

    import yaml

    for path in (
        "configs/stroop.yaml",
        "configs/go_nogo.yaml",
        "configs/n_back.yaml",
        "configs/roving_oddball_healthy.yaml",
        "configs/roving_oddball_disorder_gaba.yaml",
        "configs/roving_oddball_lesion_hippocampus.yaml",
    ):
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        assert payload["task"]["name"]


def test_roving_oddball_sequence_aliases_and_metrics() -> Any:
    """Sprawdza strukturę sekwencji i metryk trial-level dla roving oddball."""
    assert get_task("roving-oddball").name == "roving_oddball"
    task = RovingOddballTask(
        n_runs=3,
        run_length_min=2,
        run_length_max=2,
        deviant_probability=1.0,
        inter_stimulus_interval=0.5,
        jitter=0.0,
    )

    stimuli = task.generate_stimuli(seed=5, duration_s=10.0)

    assert [stim.condition for stim in stimuli] == [
        "standard",
        "standard",
        "deviant",
        "standard",
        "standard",
        "deviant",
        "standard",
        "standard",
    ]
    assert stimuli[3].payload["is_new_standard"] is True
    assert stimuli[3].payload["tone_hz"] == stimuli[2].payload["tone_hz"]
    for stimulus in stimuli:
        assert {"surprise_index", "habituation_level", "readaptation_latency"}.issubset(
            stimulus.payload
        )


def test_roving_oddball_metrics_have_stable_sequence_definitions() -> Any:
    """Sprawdza deterministyczną sekwencję, habituację i reset po zmianie standardu."""
    task = RovingOddballTask(
        n_runs=3,
        run_length_min=3,
        run_length_max=3,
        deviant_probability=1.0,
        inter_stimulus_interval=0.5,
        jitter=0.0,
    )

    first_sequence = task.generate_stimuli(seed=5, duration_s=10.0)
    second_sequence = task.generate_stimuli(seed=5, duration_s=10.0)

    assert first_sequence == second_sequence
    assert [stimulus.condition for stimulus in first_sequence] == [
        "standard",
        "standard",
        "standard",
        "deviant",
        "standard",
        "standard",
        "standard",
        "deviant",
        "standard",
        "standard",
        "standard",
    ]
    first_run_habituation = [
        stimulus.payload["habituation_level"]
        for stimulus in first_sequence
        if stimulus.payload["run_index"] == 0 and stimulus.condition == "standard"
    ]
    assert first_run_habituation == pytest.approx([0.333333, 0.666667, 1.0])

    new_standard = first_sequence[4]
    assert new_standard.payload["is_new_standard"] is True
    assert new_standard.payload["tone_hz"] == first_sequence[3].payload["tone_hz"]
    assert new_standard.payload["habituation_level"] == pytest.approx(0.333333)
    assert new_standard.payload["readaptation_latency"] == 2
    assert first_sequence[6].payload["readaptation_latency"] == 0


def test_roving_oddball_trial_results_include_metrics() -> Any:
    """Sprawdza deterministyczność wyników i obecność metryk w silniku."""
    cfg = ExperimentConfig(
        task={
            "name": "roving_oddball",
            "scenario": "roving_oddball",
            "duration": 8.0,
            "n_runs": 3,
            "run_length_min": 2,
            "run_length_max": 2,
            "deviant_probability": 1.0,
            "inter_stimulus_interval": 0.5,
            "jitter": 0.0,
        },
        output={"save_results": False},
    )

    r1 = run_experiment(cfg)
    r2 = run_experiment(cfg)

    assert r1["trial_events"] == r2["trial_events"]
    assert r1["trial_results"] == r2["trial_results"]
    assert len(r1["trial_results"]) == 8
    assert {"surprise_index", "habituation_level", "readaptation_latency"}.issubset(
        r1["trial_results"][0]
    )
    assert any(result["condition"] == "deviant" for result in r1["trial_results"])


def test_task_functional_mapping_examples() -> Any:
    """Sprawdza przykładowe mapowania task→funkcje→regiony."""
    assert regions_for_task("stroop") == ("ACC", "DLPFC")
    assert regions_for_task("go-nogo") == ("PFC", "basal-ganglia-proxy")
    assert regions_for_task("n_back") == ("DLPFC", "working-memory")
    assert "kontrola wykonawcza" in functions_for_task("stroop")
    assert "pamięć robocza" in functions_for_task("n-back")


def test_trial_stimulus_stores_regional_input_separately() -> Any:
    """Sprawdza jawne przechowywanie wejścia regionalnego poza payload."""
    stimulus = StroopTask().generate_stimuli(seed=7, duration_s=1.0)[0]

    enriched = stimulus.with_regional_input({"ACC": 1.35, "DLPFC": 0.675})

    assert stimulus.regional_input == {}
    assert "regional_input" not in stimulus.payload
    assert enriched.regional_input == {"ACC": 1.35, "DLPFC": 0.675}
    assert enriched.payload == stimulus.payload


def test_run_experiment_reports_task_activation() -> Any:
    """Sprawdza raportowanie regionów i funkcji pobudzonych przez zadanie."""
    cfg = ExperimentConfig(
        task={"name": "go_nogo", "scenario": "go_nogo", "duration": 3.0},
        output={"save_results": False},
    )

    result = run_experiment(cfg)

    task_activation = result["task_activation"]
    assert task_activation["regions"] == ["PFC", "basal-ganglia-proxy"]
    assert "salience" in task_activation["functions"]
    assert task_activation["mean_regional_input"]["PFC"] > 0.0
    assert result["trial_events"][0]["regional_input"]
    assert result["analysis_report"]["task_activation"] == task_activation


def test_run_experiment_returns_event_timeline_and_report_section() -> Any:
    """Oś czasu zawiera bodźce, odpowiedzi i sekcję raportu Markdown."""
    cfg = ExperimentConfig(
        output={"save_results": False, "label": "test", "output_dir": "outputs"},
        seed=3,
        task={"name": "stroop", "scenario": "reward-learning", "duration": 3.0},
    )

    result = run_experiment(cfg)

    event_timeline = result["event_timeline"]
    event_types = {event["event_type"] for event in event_timeline}
    assert "stimulus_onset" in event_types
    assert "response" in event_types
    assert event_timeline == sorted(
        event_timeline, key=lambda event: (event["time_s"], event["event_type"])
    )
    assert result["analysis_report"]["event_timeline"] == event_timeline

    report = AnalysisReport(result["analysis_report"]).to_markdown()
    assert "## Oś czasu eksperymentu" in report
    assert "### Słownik pojęć osi czasu" in report
    assert "stimulus_onset" in report


def test_run_experiment_records_clinical_pathology_event() -> Any:
    """Profil kliniczny jest widoczny jako zdarzenie lezji lub patologii."""
    cfg = ExperimentConfig(
        output={"save_results": False, "label": "test", "output_dir": "outputs"},
        seed=3,
        task={"name": "stroop", "scenario": "reward-learning", "duration": 0.2},
        clinical_profile={
            "id": "dopamine_deficit",
            "display_name": "Deficyt dopaminowy",
            "mechanism": "Obniżona modulacja dopaminowa.",
            "affected_regions": ["VAL"],
            "cognitive_functions": ["uczenie nagrodą"],
            "expected_effects": {},
        },
    )

    result = run_experiment(cfg)

    pathology_events = [
        event
        for event in result["event_timeline"]
        if event["event_type"] == "lesion_pathology_event"
    ]
    assert pathology_events
    assert pathology_events[0]["details"]["profile_id"] == "dopamine_deficit"


def test_roving_oddball_report_contains_conditions_and_habituation_metrics() -> Any:
    """Raport Markdown roving oddball pokazuje warunki i metryki habituacji."""
    cfg = ExperimentConfig(
        task={
            "name": "roving_oddball",
            "scenario": "roving_oddball",
            "duration": 8.0,
            "n_runs": 3,
            "run_length_min": 2,
            "run_length_max": 2,
            "deviant_probability": 1.0,
            "inter_stimulus_interval": 0.5,
            "jitter": 0.0,
        },
        output={"save_results": False},
    )

    result = run_experiment(cfg)
    roving_report = result["analysis_report"]["roving_oddball"]
    markdown = AnalysisReport(result["analysis_report"]).to_markdown()

    assert roving_report["standard_count"] > 0
    assert roving_report["deviant_count"] > 0
    assert roving_report["new_standard_count"] > 0
    assert roving_report["habituation_rate"] > 0.0
    assert "standard" in markdown
    assert "deviant" in markdown
    assert "nowy standard" in markdown
    assert "tempo habituacji" in markdown
    assert "latency readaptacji" in markdown


def test_roving_oddball_report_contains_amplitude_latency_mechanism_section() -> Any:
    """Raport roving oddball zawiera sekcję amplituda-latencja-mechanizm."""
    cfg = load_config("configs/roving_oddball_healthy.yaml")

    result = run_experiment(cfg)
    roving_report = result["analysis_report"]["roving_oddball"]
    mechanism = roving_report["amplitude_latency_mechanism"]
    markdown = AnalysisReport(result["analysis_report"]).to_markdown()

    assert mechanism["profile_id"] == "healthy_v1"
    assert mechanism["response_amplitude"] > 0.0
    assert mechanism["expected_amplitude_direction"] == "stable_reference"
    assert "### Amplituda-latencja-mechanizm" in markdown
    assert "amplituda odpowiedzi proxy" in markdown
    assert "komentarz mechanizmu" in markdown


def test_roving_oddball_profile_comparison_reports_direction_threshold_and_comment() -> (
    Any
):
    """Porównanie profili zawiera kierunek, różnicę, próg i polski komentarz."""
    healthy = load_config("configs/roving_oddball_healthy.yaml")
    disorder = load_config("configs/roving_oddball_disorder_gaba.yaml")
    lesion = load_config("configs/roving_oddball_lesion_hippocampus.yaml")

    batch = run_task_across_clinical_profiles(
        healthy,
        [
            {
                "clinical_profile": healthy.clinical_profile,
                "pathology": healthy.pathology,
            },
            {
                "clinical_profile": disorder.clinical_profile,
                "pathology": disorder.pathology,
            },
            {
                "clinical_profile": lesion.clinical_profile,
                "pathology": lesion.pathology,
            },
        ],
    )

    comparison = batch["roving_profile_comparison"]
    markdown = AnalysisReport({"roving_profile_comparison": comparison}).to_markdown()

    assert comparison["same_seed"] is True
    assert comparison["same_sequence"] is True
    assert {item["profile_group"] for item in comparison["profiles"]} == {
        "healthy",
        "disorder",
        "lesion",
    }
    assert len(comparison["comparisons"]) == 2
    for item in comparison["comparisons"]:
        assert item["expected_amplitude_direction"]
        assert "observed_amplitude_difference" in item
        assert item["observed_difference_comment"].startswith("Obserwacja:")
        assert item["qualitative_threshold"] == pytest.approx(0.05)
        assert item["educational_comment"]
    assert "### Porównanie healthy/disorder/lesion" in markdown
    assert "kierunek obserwowany" in markdown
    assert "próg jakościowy" in markdown
    assert "komentarz dydaktyczny" in markdown


def test_roving_oddball_event_timeline_has_trials_order_and_polish_labels() -> Any:
    """Oś czasu roving oddball zawiera triale, chronologię i polskie etykiety."""
    cfg = ExperimentConfig(
        task={
            "name": "roving_oddball",
            "scenario": "roving_oddball",
            "duration": 8.0,
            "n_runs": 3,
            "run_length_min": 2,
            "run_length_max": 2,
            "deviant_probability": 1.0,
            "inter_stimulus_interval": 0.5,
            "jitter": 0.0,
        },
        output={"save_results": False},
    )

    result = run_experiment(cfg)
    event_timeline = result["event_timeline"]
    required_fields = {
        "time_s",
        "event_type",
        "trial_id",
        "condition",
        "label_pl",
        "description_pl",
        "source",
        "details",
    }

    assert event_timeline
    assert all(required_fields.issubset(event) for event in event_timeline)
    assert event_timeline == sorted(
        event_timeline, key=lambda event: (event["time_s"], event["event_type"])
    )
    trial_events = [event for event in event_timeline if event["trial_id"] != "n/a"]
    assert {event["condition"] for event in trial_events} >= {"standard", "deviant"}
    assert all(event["label_pl"] for event in trial_events)
    assert any(event["label_pl"] == "poprawność" for event in trial_events)
    assert any("Początek bodźca" in event["description_pl"] for event in trial_events)
