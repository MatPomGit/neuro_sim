from __future__ import annotations

from pathlib import Path

from brain_model.scenarios import CHANNELS, get_scenario, list_scenarios
from brain_model.stimuli import build_stimulus_fn

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_GUI_PATH = REPO_ROOT / "docs" / "web_gui.html"
GLOSSARY_PATH = REPO_ROOT / "docs" / "english_polish_glossary.md"

REQUESTED_DAILY_LIFE_SCENARIOS = {
    "face-rinse",
    "sleep-onset",
    "quiet-sleep",
    "rem-sleep",
    "awakening",
    "pain-prick",
    "startle-response",
    "physical-activity",
    "sexual-activity",
    "reading-book",
}


def test_requested_daily_life_scenarios_are_available() -> None:
    """Sprawdź dostępność scenariuszy codziennych wskazanych dla prezentacji."""
    available_scenarios = set(list_scenarios())

    assert REQUESTED_DAILY_LIFE_SCENARIOS.issubset(available_scenarios)


def test_all_scenarios_have_valid_profiles() -> None:
    """Sprawdź podstawową spójność profili czasowych wszystkich scenariuszy."""
    known_channels = set(CHANNELS)

    for scenario_id in list_scenarios():
        scenario = get_scenario(scenario_id)
        assert scenario.description
        assert scenario.what_changes
        assert scenario.duration_hint > 0.0
        assert set(scenario.channels).issubset(known_channels)
        assert scenario.normalized_channels().keys() == known_channels

        for profile in scenario.channels.values():
            assert 0.0 <= profile.baseline <= 1.0
            for pulse in profile.pulses:
                assert 0.0 <= pulse.amplitude <= 1.0
                assert (
                    0.0
                    <= pulse.window.start
                    < pulse.window.end
                    <= scenario.duration_hint
                )

        for perturbation in scenario.perturbations:
            assert perturbation.channel in known_channels
            assert perturbation.mode in {"add", "set"}
            assert (
                0.0
                <= perturbation.window.start
                < perturbation.window.end
                <= scenario.duration_hint
            )

        stimulus = build_stimulus_fn(scenario)
        sample_times = {0.0, scenario.duration_hint - 0.001}
        sample_times.update(event["time"] for event in scenario.events)

        for phase in scenario.phases:
            window = phase["window"]
            assert 0.0 <= window["start"] < window["end"] <= scenario.duration_hint
            sample_times.add(window["start"] + 0.001)
            sample_times.add(window["end"] - 0.001)

        for sample_time in sample_times:
            stimulus_values = stimulus(sample_time)
            assert set(stimulus_values) == known_channels
            assert all(0.0 <= value <= 1.0 for value in stimulus_values.values())


def test_web_gui_exposes_requested_daily_life_scenarios() -> None:
    """Sprawdź, że demonstrator webowy pokazuje ten sam zestaw nowych scenariuszy."""
    source = WEB_GUI_PATH.read_text(encoding="utf-8")

    for scenario_id in REQUESTED_DAILY_LIFE_SCENARIOS:
        assert f'value="{scenario_id}"' in source
        assert f'"{scenario_id}": {{' in source


def test_glossary_maps_requested_daily_life_scenarios_to_polish() -> None:
    """Sprawdź, że nowe techniczne identyfikatory mają polskie odpowiedniki."""
    glossary = GLOSSARY_PATH.read_text(encoding="utf-8")

    for scenario_id in REQUESTED_DAILY_LIFE_SCENARIOS:
        assert f"| {scenario_id} |" in glossary
