from __future__ import annotations

from .types import (
    ChannelProfile,
    Pulse,
    StimulusPerturbation,
    StimulusScenario,
    TimeWindow,
)


def _w(start: float, end: float) -> TimeWindow:
    """Tworzy okno czasowe scenariusza w sekundach."""
    return TimeWindow(start=start, end=end)


def _p(start: float, end: float, amplitude: float) -> Pulse:
    """Tworzy impuls kanału bodźcowego z oknem czasu i amplitudą."""
    return Pulse(window=_w(start, end), amplitude=amplitude)


SCENARIOS = {
    "baseline": StimulusScenario(
        id="baseline",
        name="baseline",
        description=(
            "Spokojny przebieg kontrolny: visual 1.0-5.0 s, "
            "auditory 5.5-9.0 s, task_cue 1.0-11.5 s, "
            "interoceptive baseline=0.15."
        ),
        what_changes=(
            "Wyniki: stabilne, niskie fluktuacje aktywacji i neutralny profil stresu/nagrody."
        ),
        duration_hint=12.0,
        tags=["control", "low-arousal", "universal"],
        phases=[{"name": "adaptation", "window": {"start": 0.0, "end": 12.0}}],
        channels={
            "visual": ChannelProfile(pulses=[_p(1.0, 5.0, 0.6)]),
            "auditory": ChannelProfile(pulses=[_p(5.5, 9.0, 0.55)]),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 11.5, 0.45)]),
            "interoceptive": ChannelProfile(baseline=0.15),
        },
    ),
    "task-switching": StimulusScenario(
        id="task-switching",
        name="task-switching",
        description=(
            "Symuluje przełączanie uwagi między blokiem wzrokowym i słuchowym pod ciągłą presją "
            "zadaniową."
        ),
        what_changes=(
            "Wyniki: naprzemienne piki VIS/AUD i wzrost obciążenia ATT/EXEC przy przełączeniach."
        ),
        tags=["executive-control", "switching"],
        phases=[
            {"name": "visual-block", "window": {"start": 2.0, "end": 10.0}},
            {"name": "auditory-block", "window": {"start": 10.0, "end": 18.0}},
        ],
        channels={
            "visual": ChannelProfile(
                pulses=[_p(2.0, 10.0, 0.85), _p(18.0, 24.0, 0.85)]
            ),
            "auditory": ChannelProfile(
                pulses=[_p(10.0, 18.0, 0.8), _p(24.0, 34.0, 0.8)]
            ),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 35.0, 0.7)]),
            "reward": ChannelProfile(pulses=[_p(34.0, 38.0, 0.8)]),
            "interoceptive": ChannelProfile(baseline=0.15),
        },
    ),
    "threat-only": StimulusScenario(
        id="threat-only",
        name="threat-only",
        description=(
            "Scenariusz ekspozycji na zagrożenie z podbiciem sygnału interoceptywnego i długim "
            "oknem napięcia."
        ),
        what_changes=(
            "Wyniki: wyraźny wzrost SAL/INT, skok kortyzolu i noradrenaliny oraz spadek "
            "stabilności poznawczej."
        ),
        tags=["stress", "threat"],
        events=[
            {"type": "threat_onset", "time": 12.0},
            {"type": "threat_offset", "time": 32.0},
        ],
        channels={
            "task_cue": ChannelProfile(pulses=[_p(1.0, 35.0, 0.5)]),
            "threat": ChannelProfile(pulses=[_p(12.0, 32.0, 0.95)]),
            "interoceptive": ChannelProfile(baseline=0.25),
        },
        perturbations=[
            StimulusPerturbation(
                channel="interoceptive", window=_w(12.0, 32.0), delta=0.35, mode="add"
            )
        ],
    ),
    "reward-learning": StimulusScenario(
        id="reward-learning",
        name="reward-learning",
        description=(
            "Trening skojarzeń: bodźce sensoryczne poprzedzają sekwencje nagród, wspierając "
            "uczenie wartościowania."
        ),
        what_changes=(
            "Wyniki: narastanie odpowiedzi VAL/SEM oraz wyraźne piki po impulsach nagrody."
        ),
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
        description=(
            "Przeciążenie sensoryczne: równoczesne, silne bodźce wzrokowe i słuchowe z okresowym "
            "nasileniem."
        ),
        what_changes=(
            "Wyniki: wysoka amplituda VIS/AUD, rosnące obciążenie ATT i większa zmienność GW."
        ),
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
        description=(
            "Epizod stresu z późniejszym wygaszaniem pobudzenia i powrotem do stanu zadaniowego."
        ),
        what_changes=(
            "Wyniki: początkowy skok stresu (SAL, kortyzol), a następnie normalizacja i odbudowa "
            "EXEC/ATT."
        ),
        tags=["stress", "recovery"],
        events=[
            {"type": "stress_peak", "time": 15.0},
            {"type": "recovery_start", "time": 24.0},
        ],
        channels={
            "threat": ChannelProfile(pulses=[_p(8.0, 24.0, 0.85)]),
            "task_cue": ChannelProfile(pulses=[_p(1.0, 38.0, 0.6)]),
            "interoceptive": ChannelProfile(baseline=0.22),
            "reward": ChannelProfile(pulses=[_p(30.0, 36.0, 0.55)]),
        },
        perturbations=[
            StimulusPerturbation(
                channel="interoceptive", window=_w(8.0, 24.0), delta=0.25, mode="add"
            )
        ],
    ),
    "face-rinse": StimulusScenario(
        id="face-rinse",
        name="face-rinse",
        description=(
            "Opłukanie twarzy wodą: krótki bodziec dotykowo-interoceptywny po spokojnym "
            "przygotowaniu."
        ),
        what_changes=(
            "Wyniki: przejściowy wzrost INT/SAL, umiarkowane pobudzenie uwagi i szybki powrót do "
            "stabilnego baseline."
        ),
        duration_hint=18.0,
        tags=["interoception", "daily-life", "low-arousal"],
        phases=[
            {"name": "preparation", "window": {"start": 0.0, "end": 5.0}},
            {"name": "water-contact", "window": {"start": 5.0, "end": 9.0}},
            {"name": "settling", "window": {"start": 9.0, "end": 18.0}},
        ],
        events=[
            {"type": "water_contact", "time": 5.0},
            {"type": "rinse_end", "time": 9.0},
        ],
        channels={
            "task_cue": ChannelProfile(pulses=[_p(1.0, 12.0, 0.35)]),
            "interoceptive": ChannelProfile(baseline=0.18, pulses=[_p(5.0, 9.0, 0.75)]),
        },
    ),
    "sleep-onset": StimulusScenario(
        id="sleep-onset",
        name="sleep-onset",
        description=(
            "Zasypianie: stopniowe wyciszanie bodźców zewnętrznych i przechodzenie w stan niskiej "
            "kontroli zadaniowej."
        ),
        what_changes=(
            "Wyniki: spadek VIS/AUD/ATT/EXEC, mniejsze pobudzenie noradrenergiczne i względne "
            "utrzymanie DMN."
        ),
        duration_hint=60.0,
        tags=["sleep", "transition", "low-arousal"],
        phases=[
            {"name": "relaxation", "window": {"start": 0.0, "end": 20.0}},
            {"name": "drowsiness", "window": {"start": 20.0, "end": 42.0}},
            {"name": "sleep-entry", "window": {"start": 42.0, "end": 60.0}},
        ],
        events=[
            {"type": "eyes_closed", "time": 8.0},
            {"type": "sleep_entry", "time": 42.0},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(0.0, 8.0, 0.25)]),
            "auditory": ChannelProfile(pulses=[_p(0.0, 20.0, 0.2)]),
            "task_cue": ChannelProfile(pulses=[_p(0.0, 12.0, 0.25)]),
            "interoceptive": ChannelProfile(baseline=0.12),
        },
    ),
    "quiet-sleep": StimulusScenario(
        id="quiet-sleep",
        name="quiet-sleep",
        description=(
            "Sen spokojny: niska stymulacja sensoryczna, stabilny sygnał interoceptywny i brak "
            "wymagań zadaniowych."
        ),
        what_changes=(
            "Wyniki: niski napęd zadaniowy, stabilizacja pobudzenia i ograniczone zapłony global "
            "workspace."
        ),
        duration_hint=90.0,
        tags=["sleep", "rest", "low-arousal"],
        phases=[
            {"name": "stable-sleep", "window": {"start": 0.0, "end": 70.0}},
            {"name": "micro-adjustment", "window": {"start": 70.0, "end": 90.0}},
        ],
        events=[{"type": "sleep_stabilized", "time": 10.0}],
        channels={
            "auditory": ChannelProfile(pulses=[_p(70.0, 74.0, 0.18)]),
            "interoceptive": ChannelProfile(
                baseline=0.1, pulses=[_p(70.0, 78.0, 0.22)]
            ),
        },
    ),
    "rem-sleep": StimulusScenario(
        id="rem-sleep",
        name="rem-sleep",
        description=(
            "Faza REM: wewnętrznie generowane obrazy senne przy niskiej stymulacji zewnętrznej i "
            "większej zmienności salience."
        ),
        what_changes=(
            "Wyniki: epizodyczne piki VIS/EPIS/SAL bez zewnętrznego zadania oraz niestabilniejszy "
            "profil walencji."
        ),
        duration_hint=75.0,
        tags=["sleep", "rem", "dreaming"],
        phases=[
            {"name": "rem-entry", "window": {"start": 0.0, "end": 15.0}},
            {"name": "dream-imagery", "window": {"start": 15.0, "end": 58.0}},
            {"name": "rem-exit", "window": {"start": 58.0, "end": 75.0}},
        ],
        events=[
            {"type": "rem_onset", "time": 15.0},
            {"type": "rem_offset", "time": 58.0},
        ],
        channels={
            "visual": ChannelProfile(
                pulses=[_p(18.0, 26.0, 0.45), _p(34.0, 42.0, 0.5), _p(50.0, 56.0, 0.4)]
            ),
            "reward": ChannelProfile(pulses=[_p(35.0, 44.0, 0.35)]),
            "threat": ChannelProfile(pulses=[_p(48.0, 54.0, 0.25)]),
            "interoceptive": ChannelProfile(baseline=0.14),
        },
    ),
    "awakening": StimulusScenario(
        id="awakening",
        name="awakening",
        description=(
            "Wybudzenie się: narastający dopływ bodźców zewnętrznych, orientacja i odzyskanie "
            "kontroli zadaniowej."
        ),
        what_changes=(
            "Wyniki: wzrost VIS/AUD/ATT/EXEC, ponowny zapłon global workspace i normalizacja "
            "stanu czuwania."
        ),
        duration_hint=40.0,
        tags=["sleep", "transition", "arousal"],
        phases=[
            {"name": "sleep-tail", "window": {"start": 0.0, "end": 10.0}},
            {"name": "orientation", "window": {"start": 10.0, "end": 24.0}},
            {"name": "wakefulness", "window": {"start": 24.0, "end": 40.0}},
        ],
        events=[
            {"type": "awakening_onset", "time": 10.0},
            {"type": "eyes_open", "time": 18.0},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(18.0, 40.0, 0.55)]),
            "auditory": ChannelProfile(pulses=[_p(10.0, 24.0, 0.45)]),
            "task_cue": ChannelProfile(pulses=[_p(20.0, 40.0, 0.5)]),
            "interoceptive": ChannelProfile(
                baseline=0.16, pulses=[_p(10.0, 22.0, 0.35)]
            ),
        },
    ),
    "pain-prick": StimulusScenario(
        id="pain-prick",
        name="pain-prick",
        description=(
            "Poczucie ukłucia bólu w organizmie: krótki, ostry sygnał interoceptywny z reakcją "
            "salience."
        ),
        what_changes=(
            "Wyniki: szybki pik INT/SAL, wzrost noradrenaliny i krótkie zakłócenie stabilności "
            "poznawczej."
        ),
        duration_hint=25.0,
        tags=["pain", "interoception", "salience"],
        phases=[
            {"name": "baseline", "window": {"start": 0.0, "end": 8.0}},
            {"name": "pain", "window": {"start": 8.0, "end": 10.5}},
            {"name": "reappraisal", "window": {"start": 10.5, "end": 25.0}},
        ],
        events=[
            {"type": "pain_onset", "time": 8.0},
            {"type": "pain_offset", "time": 10.5},
        ],
        channels={
            "threat": ChannelProfile(pulses=[_p(8.0, 12.0, 0.55)]),
            "task_cue": ChannelProfile(pulses=[_p(10.5, 20.0, 0.45)]),
            "interoceptive": ChannelProfile(
                baseline=0.16, pulses=[_p(8.0, 10.5, 0.95)]
            ),
        },
        perturbations=[
            StimulusPerturbation(
                channel="interoceptive", window=_w(8.0, 10.5), delta=0.05, mode="add"
            )
        ],
    ),
    "startle-response": StimulusScenario(
        id="startle-response",
        name="startle-response",
        description=(
            "Wystraszenie się: nagły bodziec słuchowy lub wzrokowy wywołujący krótką reakcję "
            "alarmową."
        ),
        what_changes=(
            "Wyniki: gwałtowny pik AUD/VIS/SAL, wzrost noradrenaliny i szybka faza odzyskiwania "
            "kontroli."
        ),
        duration_hint=30.0,
        tags=["startle", "threat", "arousal"],
        phases=[
            {"name": "calm", "window": {"start": 0.0, "end": 7.0}},
            {"name": "startle", "window": {"start": 7.0, "end": 9.0}},
            {"name": "recovery", "window": {"start": 9.0, "end": 30.0}},
        ],
        events=[
            {"type": "startle_onset", "time": 7.0},
            {"type": "recovery_start", "time": 9.0},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(7.0, 8.5, 0.65)]),
            "auditory": ChannelProfile(pulses=[_p(7.0, 8.0, 0.95)]),
            "threat": ChannelProfile(pulses=[_p(7.0, 12.0, 0.85)]),
            "task_cue": ChannelProfile(pulses=[_p(11.0, 24.0, 0.45)]),
            "interoceptive": ChannelProfile(
                baseline=0.16, pulses=[_p(7.0, 14.0, 0.55)]
            ),
        },
    ),
    "physical-activity": StimulusScenario(
        id="physical-activity",
        name="physical-activity",
        description=(
            "Aktywność fizyczna: planowanie ruchu, narastający sygnał z ciała i przyjemna faza "
            "regeneracji."
        ),
        what_changes=(
            "Wyniki: utrzymany wzrost INT/ATT/EXEC, umiarkowana odpowiedź nagrody i stabilizacja "
            "po wysiłku."
        ),
        duration_hint=80.0,
        tags=["movement", "interoception", "exercise"],
        phases=[
            {"name": "warm-up", "window": {"start": 0.0, "end": 15.0}},
            {"name": "exercise", "window": {"start": 15.0, "end": 55.0}},
            {"name": "cool-down", "window": {"start": 55.0, "end": 80.0}},
        ],
        events=[
            {"type": "exercise_start", "time": 15.0},
            {"type": "cool_down_start", "time": 55.0},
        ],
        channels={
            "task_cue": ChannelProfile(pulses=[_p(0.0, 60.0, 0.65)]),
            "reward": ChannelProfile(pulses=[_p(45.0, 68.0, 0.45)]),
            "interoceptive": ChannelProfile(
                baseline=0.2, pulses=[_p(15.0, 55.0, 0.8), _p(55.0, 72.0, 0.45)]
            ),
        },
    ),
    "sexual-activity": StimulusScenario(
        id="sexual-activity",
        name="sexual-activity",
        description=(
            "Aktywność seksualna: stopniowe narastanie bodźców interoceptywnych i nagrodowych w "
            "bezpiecznym kontekście."
        ),
        what_changes=(
            "Wyniki: wzrost INT/VAL, silniejsza odpowiedź dopaminowa i obniżenie profilu "
            "zagrożenia przy stabilnym kontekście."
        ),
        duration_hint=90.0,
        tags=["reward", "interoception", "social"],
        phases=[
            {"name": "affiliative-context", "window": {"start": 0.0, "end": 20.0}},
            {"name": "arousal", "window": {"start": 20.0, "end": 65.0}},
            {"name": "resolution", "window": {"start": 65.0, "end": 90.0}},
        ],
        events=[
            {"type": "arousal_increase", "time": 20.0},
            {"type": "resolution_start", "time": 65.0},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(5.0, 55.0, 0.35)]),
            "task_cue": ChannelProfile(pulses=[_p(10.0, 65.0, 0.35)]),
            "reward": ChannelProfile(pulses=[_p(20.0, 72.0, 0.85)]),
            "interoceptive": ChannelProfile(
                baseline=0.18, pulses=[_p(20.0, 65.0, 0.85), _p(65.0, 80.0, 0.45)]
            ),
        },
    ),
    "reading-book": StimulusScenario(
        id="reading-book",
        name="reading-book",
        description=(
            "Czytanie książki: stabilny bodziec wzrokowy, uwaga zadaniowa i semantyczna "
            "integracja treści."
        ),
        what_changes=(
            "Wyniki: podwyższona aktywność VIS/ATT/SEM, niskie pobudzenie stresowe i umiarkowana "
            "stabilność global workspace."
        ),
        duration_hint=60.0,
        tags=["reading", "semantic", "attention"],
        phases=[
            {"name": "orientation", "window": {"start": 0.0, "end": 8.0}},
            {"name": "sustained-reading", "window": {"start": 8.0, "end": 52.0}},
            {"name": "pause", "window": {"start": 52.0, "end": 60.0}},
        ],
        events=[
            {"type": "reading_start", "time": 8.0},
            {"type": "page_turn", "time": 32.0},
        ],
        channels={
            "visual": ChannelProfile(pulses=[_p(2.0, 52.0, 0.75)]),
            "task_cue": ChannelProfile(pulses=[_p(8.0, 52.0, 0.6)]),
            "reward": ChannelProfile(pulses=[_p(40.0, 52.0, 0.25)]),
            "interoceptive": ChannelProfile(baseline=0.12),
        },
    ),
}


def list_scenarios() -> list[str]:
    """Zwraca posortowaną listę identyfikatorów dostępnych scenariuszy."""
    return sorted(SCENARIOS.keys())


def get_scenario(scenario_id: str) -> StimulusScenario:
    """Zwraca scenariusz bodźcowy dla podanego identyfikatora."""
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise ValueError(
            f"Nieznany scenariusz: {scenario_id}. Dostępne: {', '.join(list_scenarios())}"
        ) from exc
