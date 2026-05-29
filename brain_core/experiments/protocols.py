from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class ProtocolPhase(str, Enum):
    """
    Faza protokołu eksperymentalnego.
    """
    TRAIN = "train"
    TEST = "test"


class ErrorType(str, Enum):
    """
    Typ błędu w zadaniu eksperymentalnym.
    """
    NONE = "none"
    COMMISSION = "commission"
    OMISSION = "omission"
    INTERFERENCE = "interference"


@dataclass(frozen=True, slots=True)
class ProtocolStep:
    """
    Pojedynczy krok protokołu eksperymentalnego.

    Attributes:
        phase (ProtocolPhase): Faza protokołu.
        duration_s (float): Czas trwania kroku.
        label (str): Etykieta kroku.
    """
    phase: ProtocolPhase
    duration_s: float
    label: str = ""


@dataclass(frozen=True, slots=True)
class TrialStimulus:
    """
    Bodziec prezentowany w pojedynczym trialu.

    Attributes:
        trial_id (int): Identyfikator trialu.
        onset_s (float): Czas rozpoczęcia.
        duration_s (float): Czas trwania.
        payload (dict[str, Any]): Dane bodźca.
        condition (str): Warunek eksperymentalny.
    """
    trial_id: int
    onset_s: float
    duration_s: float
    payload: dict[str, Any]
    condition: str


@dataclass(frozen=True, slots=True)
class TrialResult:
    """
    Wynik pojedynczego trialu eksperymentalnego.

    Attributes:
        trial_id (int): Identyfikator trialu.
        reaction_time_s (float | None): Czas reakcji.
        correct (bool): Czy odpowiedź była poprawna.
        error_type (ErrorType): Typ błędu.
        condition (str): Warunek eksperymentalny.
    """
    trial_id: int
    reaction_time_s: float | None
    correct: bool
    error_type: ErrorType
    condition: str


class CognitiveTask(Protocol):
    """
    Protokół zadania kognitywnego.
    """
    name: str

    def generate_stimuli(self, seed: int, duration_s: float) -> list[TrialStimulus]:
        """
        Generuje listę bodźców dla zadania.
        """
        ...

    def expected_response(self, stimulus: TrialStimulus) -> Any:
        """
        Zwraca oczekiwaną odpowiedź na bodziec.
        """
        ...

    def score_trial(self, stimulus: TrialStimulus, observed_response: Any, reaction_time_s: float | None) -> TrialResult:
        """
        Ocenia wynik trialu.
        """
        ...


@dataclass(frozen=True, slots=True)
class ExperimentProtocol:
    """
    Protokół eksperymentu składający się z kroków.

    Attributes:
        name (str): Nazwa protokołu.
        steps (tuple[ProtocolStep, ...]): Kroki protokołu.
    """
    name: str
    steps: tuple[ProtocolStep, ...]

    def total_duration(self, phase: ProtocolPhase | None = None) -> float:
        """
        Zwraca łączny czas trwania protokołu lub wybranej fazy.

        Args:
            phase (ProtocolPhase | None): Faza do zsumowania lub None dla całości.

        Returns:
            float: Łączny czas trwania.
        """
        if phase is None:
            return sum(step.duration_s for step in self.steps)
        return sum(step.duration_s for step in self.steps if step.phase == phase)


def _lcg(seed: int) -> int:
    """
    Prosty generator liczb pseudolosowych (LCG).

    Args:
        seed (int): Ziarno.

    Returns:
        int: Nowa wartość ziarna.
    """
    return (1664525 * seed + 1013904223) % (2**32)


class StroopTask:
    """
    Zadanie Stroopa — generuje bodźce i ocenia odpowiedzi.
    """
    name: str = "stroop"

    def generate_stimuli(self, seed: int, duration_s: float) -> list[TrialStimulus]:
        """
        Generuje bodźce do zadania Stroopa.
        """
        colors = ("red", "green", "blue", "yellow")
        t = 0.5
        trial_id = 0
        state = seed
        trials: list[TrialStimulus] = []
        while t < duration_s:
            state = _lcg(state)
            word = colors[state % len(colors)]
            state = _lcg(state)
            ink = colors[state % len(colors)]
            condition = "congruent" if word == ink else "incongruent"
            trials.append(TrialStimulus(trial_id, t, 1.0, {"word": word, "ink": ink}, condition))
            t += 2.0
            trial_id += 1
        return trials

    def expected_response(self, stimulus: TrialStimulus) -> str:
        """
        Zwraca oczekiwany kolor (ink) dla bodźca.
        """
        return str(stimulus.payload["ink"])

    def score_trial(self, stimulus: TrialStimulus, observed_response: Any, reaction_time_s: float | None) -> TrialResult:
        """
        Ocenia wynik trialu w zadaniu Stroopa.
        """
        expected = self.expected_response(stimulus)
        if observed_response is None:
            return TrialResult(stimulus.trial_id, reaction_time_s, False, ErrorType.OMISSION, stimulus.condition)
        correct = str(observed_response) == expected
        err = ErrorType.NONE if correct else ErrorType.INTERFERENCE
        return TrialResult(stimulus.trial_id, reaction_time_s, correct, err, stimulus.condition)


class GoNoGoTask:
    """
    Zadanie Go/NoGo — generuje bodźce i ocenia odpowiedzi.
    """
    name: str = "go_nogo"

    def generate_stimuli(self, seed: int, duration_s: float) -> list[TrialStimulus]:
        """
        Generuje bodźce do zadania Go/NoGo.
        """
        t = 0.2
        trial_id = 0
        state = seed
        trials: list[TrialStimulus] = []
        while t < duration_s:
            state = _lcg(state)
            is_go = (state % 5) != 0
            condition = "go" if is_go else "nogo"
            trials.append(TrialStimulus(trial_id, t, 0.6, {"cue": condition}, condition))
            t += 1.2
            trial_id += 1
        return trials

    def expected_response(self, stimulus: TrialStimulus) -> str | None:
        """
        Zwraca oczekiwaną odpowiedź dla bodźca Go/NoGo.
        """
        return "press" if stimulus.condition == "go" else None

    def score_trial(self, stimulus: TrialStimulus, observed_response: Any, reaction_time_s: float | None) -> TrialResult:
        """Ocenia poprawność odpowiedzi i typ błędu w zadaniu Go/NoGo."""
        expected = self.expected_response(stimulus)
        if expected is None:
            correct = observed_response is None
            err = ErrorType.NONE if correct else ErrorType.COMMISSION
        else:
            correct = observed_response == expected
            err = ErrorType.NONE if correct else ErrorType.OMISSION
        return TrialResult(stimulus.trial_id, reaction_time_s, correct, err, stimulus.condition)


class NBackTask:
    """Zadanie n-back — generuje sekwencję symboli i ocenia trafienia celu."""

    name: str = "n_back"

    def __init__(self, n: int = 2) -> None:
        """Inicjalizuje zadanie z odległością porównania n."""
        if n < 1:
            raise ValueError("n must be at least 1 for NBackTask")
        self.n: int = n

    def generate_stimuli(self, seed: int, duration_s: float) -> list[TrialStimulus]:
        """Generuje deterministyczną sekwencję bodźców n-back."""
        symbols = tuple("ABCDEFGH")
        t = 0.3
        trial_id = 0
        state = seed
        trials: list[TrialStimulus] = []
        while t < duration_s:
            state = _lcg(state)
            symbol = symbols[state % len(symbols)]
            trials.append(TrialStimulus(trial_id, t, 0.8, {"symbol": symbol, "n": self.n}, "target_pending"))
            t += 1.5
            trial_id += 1
        for idx, stim in enumerate(trials):
            if idx >= self.n and stim.payload["symbol"] == trials[idx - self.n].payload["symbol"]:
                trials[idx] = TrialStimulus(stim.trial_id, stim.onset_s, stim.duration_s, stim.payload, "target")
            else:
                trials[idx] = TrialStimulus(stim.trial_id, stim.onset_s, stim.duration_s, stim.payload, "non_target")
        return trials

    def expected_response(self, stimulus: TrialStimulus) -> str | None:
        """Zwraca oczekiwaną odpowiedź dla bodźca n-back."""
        return "match" if stimulus.condition == "target" else None

    def score_trial(self, stimulus: TrialStimulus, observed_response: Any, reaction_time_s: float | None) -> TrialResult:
        """Ocenia odpowiedź użytkownika względem statusu celu n-back."""
        expected = self.expected_response(stimulus)
        if expected is None:
            correct = observed_response is None
            err = ErrorType.NONE if correct else ErrorType.COMMISSION
        else:
            correct = observed_response == expected
            err = ErrorType.NONE if correct else ErrorType.OMISSION
        return TrialResult(stimulus.trial_id, reaction_time_s, correct, err, stimulus.condition)


def get_task(task_name: str, **kwargs: Any) -> CognitiveTask:
    """Zwraca instancję zadania poznawczego na podstawie nazwy technicznej."""
    name = task_name.lower()
    if name == "stroop":
        return StroopTask()
    if name in {"go_nogo", "go-nogo"}:
        return GoNoGoTask()
    if name in {"n_back", "n-back"}:
        return NBackTask(n=int(kwargs.get("n", 2)))
    raise ValueError(f"Unknown task: {task_name}")


def default_train_test_protocol() -> ExperimentProtocol:
    """Buduje domyślny protokół z fazami treningu i testu."""
    return ExperimentProtocol(
        name="default_train_test",
        steps=(
            ProtocolStep(phase=ProtocolPhase.TRAIN, duration_s=30.0, label="train_baseline"),
            ProtocolStep(phase=ProtocolPhase.TRAIN, duration_s=30.0, label="train_perturbed"),
            ProtocolStep(phase=ProtocolPhase.TEST, duration_s=20.0, label="test_recall"),
        ),
    )
