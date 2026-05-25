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
        description="Spokojny przebieg kontrolny z łagodnymi bodźcami wzrokowo-słuchowymi i stałym sygnałem zadaniowym.",
        what_changes="Niewielkie fluktuacje aktywacji; brak gwałtownych skoków stresu i nagrody.",
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
        description="Symuluje przełączanie uwagi między blokiem wzrokowym i słuchowym pod ciągłą presją zadaniową.",
        what_changes="Naprzemienne wzrosty aktywacji VIS/AUD oraz większe obciążenie ATT i EXEC przy zmianie bloku.",
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
        description="Scenariusz ekspozycji na zagrożenie z podbiciem sygnału interoceptywnego i długim oknem napięcia.",
        what_changes="Silny wzrost SAL/INT, skok kortyzolu i noradrenaliny oraz spadek stabilności poznawczej podczas zagrożenia.",
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
        description="Trening skojarzeń: bodźce sensoryczne poprzedzają sekwencje nagród, wspierając uczenie wartościowania.",
        what_changes="Narastanie odpowiedzi VAL i SEM oraz wyraźne piki po impulsach nagrody.",
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
    "sensory-overload": StimulusScenario(
        id="sensory-overload",
        name="sensory-overload",
        description="Przeciążenie sensoryczne: równoczesne, silne bodźce wzrokowe i słuchowe z okresowym nasileniem.",
        what_changes="Wysoka amplituda VIS/AUD i rosnące obciążenie ATT; możliwe wahania GW przy silnej konkurencji sygnałów.",
        tags=["high-load", "sensory"],
        phases=[
            {"name": "ramp-up", "window": {"start": 0.0, "end": 12.0}},
            {"name": "overload", "window": {"start": 12.0, "end": 30.0}},
            {"name": "recovery", "window": {"start": 30.0, "end": 45.0}},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(2.0, 30.0, 0.95)]),
            "auditory": ChannelProfile(pulses=[_p(4.0, 30.0, 0.9)]),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 35.0, 0.75)]),
            "interoceptive": ChannelProfile(baseline=0.2),
        },
    ),
    "stress-recovery": StimulusScenario(
        id="stress-recovery",
        name="stress-recovery",
        description="Epizod stresu z późniejszym wygaszaniem pobudzenia i powrotem do stanu zadaniowego.",
        what_changes="Najpierw skok stresu (SAL, kortyzol), potem stopniowa normalizacja i odbudowa stabilności EXEC/ATT.",
        tags=["stress", "recovery"],
        events=[{"type": "stress_peak", "time": 15.0}, {"type": "recovery_start", "time": 24.0}],
        channels={
            "threat": ChannelProfile(pulses=[_p(8.0, 24.0, 0.85)]),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 38.0, 0.6)]),
            "interoceptive": ChannelProfile(baseline=0.22),
            "reward": ChannelProfile(pulses=[_p(30.0, 36.0, 0.55)]),
        },
        perturbations=[StimulusPerturbation(channel="interoceptive", window=_w(8.0, 24.0), delta=0.25, mode="add")],
    ),
}


def list_scenarios():
    return sorted(SCENARIOS.keys())


def get_scenario(scenario_id: str) -> StimulusScenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise ValueError(f"Nieznany scenariusz: {scenario_id}. Dostępne: {', '.join(list_scenarios())}") from exc
