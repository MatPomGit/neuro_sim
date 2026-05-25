from __future__ import annotations

from .types import ChannelProfile, Pulse, StimulusPerturbation, StimulusScenario, TimeWindow


def _w(start: float, end: float) -> TimeWindow:
    return TimeWindow(start=start, end=end)


def _p(start: float, end: float, amplitude: float) -> Pulse:
    return Pulse(window=_w(start, end), amplitude=amplitude)


SCENARIOS = {
    "baseline": StimulusScenario(
        id="baseline",
        name="baseline",
        description="Łagodna stymulacja bazowa bez silnych zdarzeń afektywnych.",
        tags=["control", "low-arousal"],
        phases=[{"name": "adaptation", "window": {"start": 0.0, "end": 45.0}}],
        channels={
            "visual": ChannelProfile(pulses=[_p(4.0, 14.0, 0.6)]),
            "auditory": ChannelProfile(pulses=[_p(10.0, 20.0, 0.55)]),
            "task_cue": ChannelProfile(pulses=[_p(2.0, 28.0, 0.45)]),
            "interoceptive": ChannelProfile(baseline=0.15),
        },
    ),
    "task-switching": StimulusScenario(
        id="task-switching",
        name="task-switching",
        description="Przełączanie między modalnościami z okresowym sygnałem zadaniowym.",
        tags=["executive-control", "switching"],
        phases=[
            {"name": "visual-block", "window": {"start": 2.0, "end": 10.0}},
            {"name": "auditory-block", "window": {"start": 10.0, "end": 18.0}},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(2.0, 10.0, 0.85), _p(18.0, 24.0, 0.85)]),
            "auditory": ChannelProfile(pulses=[_p(10.0, 18.0, 0.8), _p(24.0, 34.0, 0.8)]),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 35.0, 0.7)]),
            "reward": ChannelProfile(pulses=[_p(34.0, 38.0, 0.8)]),
            "interoceptive": ChannelProfile(baseline=0.15),
        },
    ),
    "threat-only": StimulusScenario(
        id="threat-only",
        name="threat-only",
        description="Scenariusz zagrożenia z silną reakcją interoceptywną.",
        tags=["stress", "threat"],
        events=[{"type": "threat_onset", "time": 12.0}, {"type": "threat_offset", "time": 32.0}],
        channels={
            "task_cue": ChannelProfile(pulses=[_p(1.0, 35.0, 0.5)]),
            "threat": ChannelProfile(pulses=[_p(12.0, 32.0, 0.95)]),
            "interoceptive": ChannelProfile(baseline=0.25),
        },
        perturbations=[StimulusPerturbation(channel="interoceptive", window=_w(12.0, 32.0), delta=0.35, mode="add")],
    ),
    "reward-learning": StimulusScenario(
        id="reward-learning",
        name="reward-learning",
        description="Bodźce sensoryczne kończące się sekwencją nagród.",
        tags=["learning", "reward"],
        events=[{"type": "reward", "time": 26.0}, {"type": "reward", "time": 34.0}],
        channels={
            "visual": ChannelProfile(pulses=[_p(2.0, 18.0, 0.9)]),
            "auditory": ChannelProfile(pulses=[_p(8.0, 24.0, 0.75)]),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 35.0, 0.65)]),
            "reward": ChannelProfile(pulses=[_p(26.0, 30.0, 1.0), _p(34.0, 38.0, 1.0)]),
            "interoceptive": ChannelProfile(baseline=0.15),
        },
    ),
}


def list_scenarios():
    return sorted(SCENARIOS.keys())


def get_scenario(scenario_id: str) -> StimulusScenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise ValueError(f"Nieznany scenariusz: {scenario_id}. Dostępne: {', '.join(list_scenarios())}") from exc
