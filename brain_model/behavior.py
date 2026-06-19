from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BehaviorSample:
    """Pojedynczy odczyt behawioralny modelu w danym kroku symulacji.

    Attributes
    ----------
    decision:
        Etykieta decyzji użytkowej. Wartość ``"wait"`` oznacza brak
        przekroczenia progu decyzyjnego, ``"explore"`` neutralną eksplorację,
        ``"avoid"`` reakcję unikania przy niskiej aktywacji VAL, a
        ``"reward-approach"`` podejście do nagrody przy wysokiej aktywacji VAL.
    latency:
        Czas od początku symulacji do bieżącej próbki behawioralnej w
        sekundach, liczony jako ``(step_index + 1) * dt``. Wartość jest
        nieujemna, jeśli ``dt`` jest dodatnie.
    confidence:
        Bezwymiarowa pewność decyzji w zakresie ``[0, 1]``. Powstaje przez
        liniowe przeskalowanie odległości ``decision_score`` od progu i obcięcie
        do dopuszczalnego zakresu.
    decision_score:
        Surowy, bezwymiarowy wynik decyzyjny obliczony jako ważona suma
        aktywacji modułów EXEC, VAL, MOT i GW. W typowej pracy modelu składowe
        aktywacji są w zakresie ``[0, 1]``; wartości większe lub równe progowi
        wyzwalają etykietę decyzji inną niż ``"wait"``.
    """

    decision: str
    latency: float
    confidence: float
    decision_score: float


def map_behavior_state(
    x: Any,
    idx: dict[str, int],
    dt: float,
    step_index: int,
    decision_threshold: float,
    confidence_gain: float,
) -> BehaviorSample:
    """Przelicz stan kluczowych modułów na odczyt behawioralny.

    Parameters
    ----------
    x:
        Wektor aktywacji modułów; musi umożliwiać indeksowanie po pozycjach
        EXEC, VAL, MOT i GW. Oczekiwane wartości aktywacji są bezwymiarowe i
        mieszczą się w zakresie ``[0, 1]``.
    idx:
        Mapowanie nazw modułów na indeksy w ``x``. Musi zawierać klucze
        ``"EXEC"``, ``"VAL"``, ``"MOT"`` i ``"GW"``.
    dt:
        Krok czasu symulacji w sekundach, używany do obliczenia latencji.
    step_index:
        Zerowany indeks kroku symulacji.
    decision_threshold:
        Bezwymiarowy próg, którego przekroczenie oznacza wystąpienie decyzji.
    confidence_gain:
        Wzmocnienie przeliczające odległość od progu na pewność.

    Returns
    -------
    BehaviorSample
        Próbka zawierająca etykietę decyzji, latencję w sekundach, pewność
        ``[0, 1]`` oraz surowy wynik decyzyjny.

    Raises
    ------
    KeyError
        Gdy ``idx`` nie zawiera wymaganego modułu.
    IndexError
        Gdy indeks modułu wykracza poza długość ``x``.
    TypeError
        Gdy wartości w ``x`` nie mogą zostać przekonwertowane na ``float``.
    """
    exec_level = float(x[idx["EXEC"]])
    val_level = float(x[idx["VAL"]])
    mot_level = float(x[idx["MOT"]])
    gw_level = float(x[idx["GW"]])

    decision_score = (
        0.34 * exec_level + 0.22 * val_level + 0.22 * mot_level + 0.22 * gw_level
    )

    if decision_score >= decision_threshold:
        if val_level >= 0.66:
            decision = "reward-approach"
        elif val_level <= 0.34:
            decision = "avoid"
        else:
            decision = "explore"
    else:
        decision = "wait"

    confidence_raw = confidence_gain * (decision_score - decision_threshold)
    confidence = max(0.0, min(1.0, 0.5 + confidence_raw))

    latency = float((step_index + 1) * dt)

    return BehaviorSample(
        decision=decision,
        latency=latency,
        confidence=confidence,
        decision_score=decision_score,
    )
