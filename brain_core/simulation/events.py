"""Struktury osi czasu zdarzeń dla replikowalnych symulacji."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

EVENT_TERM_GLOSSARY: dict[str, str] = {
    "event_timeline": "oś czasu eksperymentu",
    "stimulus_onset": "początek bodźca",
    "response": "odpowiedź",
    "error": "błąd",
    "correctness": "poprawność",
    "neuromodulation_change": "zmiana neuromodulacji",
    "lesion_pathology_event": "zdarzenie lezji lub patologii",
    "significant_region_activity_change": "istotna zmiana aktywności regionu",
    "prediction_error": "błąd predykcji",
    "task_evoked_activity": "aktywność wywołana zadaniem",
}
"""Słownik pojęć EN→PL zgodny z terminologią warstwy prezentacji."""

EVENT_TERM_EXPLANATIONS: dict[str, str] = {
    "event_timeline": "chronologiczny zapis zdarzeń istotnych dla interpretacji wyniku",
    "stimulus_onset": "czas rozpoczęcia prezentacji bodźca w trialu",
    "response": "zarejestrowana odpowiedź modelu wraz z czasem reakcji",
    "error": "niepoprawna albo brakująca odpowiedź w punktacji trialu",
    "correctness": "informacja, czy odpowiedź w trialu była poprawna",
    "neuromodulation_change": "wykryty skok sygnału neuromodulacyjnego w diagnostyce",
    "lesion_pathology_event": "jawna lezja, patologia albo profil kliniczny użyty w uruchomieniu",
    "significant_region_activity_change": (
        "duża zmiana aktywności regionu względem poprzedniej próbki"
    ),
    "prediction_error": "różnica między bodźcem a predykcją modelu",
    "task_evoked_activity": "aktywność regionów wywołana bodźcami zadania",
}
"""Polskie objaśnienia pojęć używanych w osi czasu eksperymentu."""

_NEUROMODULATOR_KEYS = (
    "dopamine_delta",
    "noradrenaline",
    "acetylcholine",
    "serotonin",
    "gaba",
    "glutamate",
    "endorphins",
    "cortisol",
)


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """Opisuje pojedynczy, jawnie datowany fakt z przebiegu symulacji.

    Parameters
    ----------
    time_s:
        Czas zdarzenia w sekundach od początku uruchomienia.
    event_type:
        Techniczny typ zdarzenia, np. ``stimulus_onset`` albo ``response``.
    label_pl:
        Polska etykieta prezentacyjna spójna ze słownikiem pojęć.
    description_pl:
        Krótki opis zdarzenia przeznaczony do raportu użytkownika.
    source:
        Źródło zdarzenia, np. ``task`` lub ``diagnostics``.
    trial_id:
        Stabilny identyfikator trialu albo ``n/a`` dla zdarzeń globalnych.
    trial_number:
        Numeryczny numer trialu używany do grupowania raportów roving oddball;
        ``None`` oznacza zdarzenie globalne.
    condition:
        Warunek eksperymentalny trialu albo ``n/a`` dla zdarzeń globalnych.
    details:
        Dodatkowe metadane potrzebne do reprodukcji i filtrowania osi czasu.
    plot_anchor:
        Opcjonalny znacznik łączący zdarzenie z serią lub panelem wykresu.
    """

    time_s: float
    event_type: str
    label_pl: str
    description_pl: str
    source: str
    trial_id: int | str = "n/a"
    trial_number: int | None = None
    condition: str = "n/a"
    details: dict[str, Any] = field(default_factory=dict)
    plot_anchor: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Zwraca zdarzenie jako słownik bez obiektów NumPy.

        Returns
        -------
        dict[str, Any]
            Serializowalny słownik z czasem, typem, etykietą i metadanymi.
        """
        payload = asdict(self)
        payload["time_s"] = round(float(self.time_s), 6)
        payload["details"] = _to_builtin(payload["details"])
        if payload.get("trial_number") is None:
            payload["trial_number"] = _trial_number_from_id(payload.get("trial_id"))
        if payload.get("plot_anchor") is None:
            payload.pop("plot_anchor", None)
        return payload


def build_event_timeline(
    *,
    time: np.ndarray,
    activity: np.ndarray,
    diagnostics: dict[str, Any],
    trial_events: list[dict[str, Any]],
    trial_results: list[dict[str, Any]],
    pathology: dict[str, Any],
    clinical_profile: dict[str, Any],
    region_names: list[str],
    max_activity_events: int = 12,
    max_neuromodulation_events: int = 12,
) -> list[dict[str, Any]]:
    """Buduje chronologiczną oś czasu najważniejszych zdarzeń symulacji.

    Parameters
    ----------
    time:
        Jednowymiarowa tablica czasu symulacji w sekundach.
    activity:
        Macierz aktywności regionów/modułów w kolejnych próbkach.
    diagnostics:
        Słownik sygnałów diagnostycznych, w tym neuromodulatorów.
    trial_events:
        Zdarzenia bodźcowe wygenerowane przez harmonogram zadania.
    trial_results:
        Wyniki odpowiedzi i punktacji triali.
    pathology:
        Konfiguracja lezji lub patologii użyta w eksperymencie.
    clinical_profile:
        Metadane profilu klinicznego użyte w eksperymencie.
    region_names:
        Nazwy regionów zgodne z kolumnami macierzy aktywności.
    max_activity_events:
        Maksymalna liczba zdarzeń aktywności dopisana do osi czasu.
    max_neuromodulation_events:
        Maksymalna liczba zdarzeń neuromodulacyjnych dopisana do osi czasu.

    Returns
    -------
    list[dict[str, Any]]
        Lista zdarzeń posortowana według czasu i typu, gotowa do zapisu JSON.
    """
    events: list[SimulationEvent] = []
    trial_contexts = _trial_contexts(trial_events)
    events.extend(_stimulus_onset_events(trial_events))
    events.extend(_response_and_error_events(trial_results, trial_events))
    events.extend(_pathology_events(pathology, clinical_profile))
    events.extend(
        _neuromodulation_events(
            time=time,
            diagnostics=diagnostics,
            trial_contexts=trial_contexts,
            max_events=max_neuromodulation_events,
        )
    )
    events.extend(
        _activity_change_events(
            time=time,
            activity=activity,
            region_names=region_names,
            trial_contexts=trial_contexts,
            max_events=max_activity_events,
        )
    )

    ordered = sorted(events, key=lambda event: (event.time_s, event.event_type))
    return [event.to_dict() for event in ordered]


def _stimulus_onset_events(trial_events: list[dict[str, Any]]) -> list[SimulationEvent]:
    """Zamienia zdarzenia triali na wpisy początku bodźca."""
    events: list[SimulationEvent] = []
    for trial_event in trial_events:
        condition = str(trial_event.get("condition", "n/a"))
        trial_id = trial_event.get("trial_id", "n/a")
        events.append(
            SimulationEvent(
                time_s=float(trial_event.get("onset_s", 0.0)),
                event_type="stimulus_onset",
                label_pl=EVENT_TERM_GLOSSARY["stimulus_onset"],
                description_pl=f"Początek bodźca w trialu {trial_id} ({condition}).",
                source="task",
                trial_id=trial_id,
                trial_number=_trial_number_from_id(trial_id),
                condition=condition,
                details={
                    "trial_id": trial_id,
                    "trial_number": _trial_number_from_id(trial_id),
                    "condition": condition,
                    "duration_s": trial_event.get("duration_s"),
                    "regional_input": trial_event.get("regional_input", {}),
                    "payload": trial_event.get("payload", {}),
                },
                plot_anchor="task_timeline",
            )
        )
    return events


def _response_and_error_events(
    trial_results: list[dict[str, Any]],
    trial_events: list[dict[str, Any]],
) -> list[SimulationEvent]:
    """Tworzy wpisy odpowiedzi oraz błędów na podstawie wyników triali."""
    onset_by_trial = {
        event.get("trial_id"): float(event.get("onset_s", 0.0))
        for event in trial_events
    }
    events: list[SimulationEvent] = []
    for result in trial_results:
        trial_id = result.get("trial_id", "n/a")
        reaction_time = result.get("reaction_time_s")
        onset_s = onset_by_trial.get(trial_id, 0.0)
        event_time = (
            onset_s if reaction_time is None else onset_s + float(reaction_time)
        )
        correct = bool(result.get("correct", False))
        error_type = str(result.get("error_type", "none"))
        events.append(
            SimulationEvent(
                time_s=event_time,
                event_type="response",
                label_pl=EVENT_TERM_GLOSSARY["response"],
                description_pl=(
                    f"Odpowiedź w trialu {trial_id}: "
                    f"{'poprawna' if correct else 'niepoprawna'}."
                ),
                source="task_scoring",
                trial_id=trial_id,
                trial_number=_trial_number_from_id(trial_id),
                condition=str(result.get("condition", "n/a")),
                details={
                    "trial_id": trial_id,
                    "trial_number": _trial_number_from_id(trial_id),
                    "condition": result.get("condition", "n/a"),
                    "reaction_time_s": reaction_time,
                    "correct": correct,
                    "error_type": error_type,
                    "surprise_index": result.get("surprise_index"),
                    "habituation_level": result.get("habituation_level"),
                    "readaptation_latency": result.get("readaptation_latency"),
                },
            )
        )
        events.append(
            SimulationEvent(
                time_s=event_time,
                event_type="correctness",
                label_pl=EVENT_TERM_GLOSSARY["correctness"],
                description_pl=(
                    f"Trial {trial_id}: "
                    f"{'odpowiedź poprawna' if correct else 'odpowiedź niepoprawna'}."
                ),
                source="task_scoring",
                trial_id=trial_id,
                trial_number=_trial_number_from_id(trial_id),
                condition=str(result.get("condition", "n/a")),
                details={
                    "trial_id": trial_id,
                    "trial_number": _trial_number_from_id(trial_id),
                    "condition": result.get("condition", "n/a"),
                    "correct": correct,
                    "error_type": error_type,
                    "reaction_time_s": reaction_time,
                    "surprise_index": result.get("surprise_index"),
                    "habituation_level": result.get("habituation_level"),
                    "readaptation_latency": result.get("readaptation_latency"),
                },
            )
        )
        if not correct or error_type not in {"none", "None"}:
            events.append(
                SimulationEvent(
                    time_s=event_time,
                    event_type="error",
                    label_pl=EVENT_TERM_GLOSSARY["error"],
                    description_pl=f"Błąd w trialu {trial_id}: {error_type}.",
                    source="task_scoring",
                    trial_id=trial_id,
                    trial_number=_trial_number_from_id(trial_id),
                    condition=str(result.get("condition", "n/a")),
                    details={
                        "trial_id": trial_id,
                        "trial_number": _trial_number_from_id(trial_id),
                        "condition": result.get("condition", "n/a"),
                        "error_type": error_type,
                    },
                )
            )
    return events


def _pathology_events(
    pathology: dict[str, Any], clinical_profile: dict[str, Any]
) -> list[SimulationEvent]:
    """Opisuje jawne zdarzenia lezji lub patologii z konfiguracji."""
    events: list[SimulationEvent] = []
    if not isinstance(clinical_profile, dict):
        clinical_profile = {}
    mutations = pathology.get("mutations", []) if isinstance(pathology, dict) else []
    if isinstance(pathology, dict) and pathology.get("enabled"):
        for mutation in mutations:
            events.append(
                SimulationEvent(
                    time_s=float(mutation.get("onset_s", 0.0)),
                    event_type="lesion_pathology_event",
                    label_pl=EVENT_TERM_GLOSSARY["lesion_pathology_event"],
                    description_pl=(
                        "Aktywna konfiguracja patologii: "
                        f"{mutation.get('kind', 'n/a')} dla {mutation.get('target', 'n/a')}."
                    ),
                    source="pathology_config",
                    details=dict(mutation),
                    plot_anchor="diagnostics",
                )
            )

    profile_id = str(clinical_profile.get("id", "healthy_v1"))
    affected_regions = clinical_profile.get("affected_regions", [])
    if profile_id != "healthy_v1" or affected_regions:
        events.append(
            SimulationEvent(
                time_s=0.0,
                event_type="lesion_pathology_event",
                label_pl=EVENT_TERM_GLOSSARY["lesion_pathology_event"],
                description_pl=(
                    "Profil kliniczny: "
                    f"{clinical_profile.get('display_name', profile_id)}."
                ),
                source="clinical_profile",
                details={
                    "profile_id": profile_id,
                    "mechanism": clinical_profile.get("mechanism", "n/a"),
                    "affected_regions": affected_regions,
                    "cognitive_functions": clinical_profile.get(
                        "cognitive_functions", []
                    ),
                },
            )
        )
    return events


def _neuromodulation_events(
    *,
    time: np.ndarray,
    diagnostics: dict[str, Any],
    trial_contexts: list[dict[str, Any]],
    max_events: int,
) -> list[SimulationEvent]:
    """Wykrywa największe skoki sygnałów neuromodulacyjnych."""
    candidates: list[tuple[float, int, str, float, float]] = []
    for key in _NEUROMODULATOR_KEYS:
        values = np.asarray(diagnostics.get(key, []), dtype=float)
        if values.size < 2:
            continue
        deltas = np.abs(np.diff(values))
        if deltas.size == 0:
            continue
        threshold = max(float(np.mean(deltas) + 2.0 * np.std(deltas)), 0.05)
        for index in np.where(deltas >= threshold)[0]:
            candidates.append(
                (
                    float(deltas[index]),
                    int(index + 1),
                    key,
                    float(values[index]),
                    float(values[index + 1]),
                )
            )

    selected = sorted(candidates, key=lambda item: item[0], reverse=True)[:max_events]
    events: list[SimulationEvent] = []
    for delta, sample_index, key, previous_value, current_value in selected:
        time_s = _time_at(time, sample_index)
        trial_context = _trial_context_at(time_s, trial_contexts)
        events.append(
            SimulationEvent(
                time_s=time_s,
                event_type="neuromodulation_change",
                label_pl=EVENT_TERM_GLOSSARY["neuromodulation_change"],
                description_pl=(
                    f"Zmiana neuromodulacji {key}: "
                    f"{previous_value:.3f} → {current_value:.3f}."
                ),
                source="diagnostics",
                trial_id=trial_context["trial_id"],
                trial_number=trial_context["trial_number"],
                condition=trial_context["condition"],
                details={
                    "signal": key,
                    "trial_number": trial_context["trial_number"],
                    "previous_value": round(previous_value, 6),
                    "current_value": round(current_value, 6),
                    "abs_delta": round(delta, 6),
                    "sample_index": sample_index,
                },
                plot_anchor=f"diagnostics.{key}",
            )
        )
    return events


def _activity_change_events(
    *,
    time: np.ndarray,
    activity: np.ndarray,
    region_names: list[str],
    trial_contexts: list[dict[str, Any]],
    max_events: int,
) -> list[SimulationEvent]:
    """Wykrywa największe istotne zmiany aktywności regionów."""
    matrix = np.asarray(activity, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2:
        return []

    deltas = np.abs(np.diff(matrix, axis=0))
    threshold = max(float(np.mean(deltas) + 2.0 * np.std(deltas)), 0.05)
    candidate_indices = np.argwhere(deltas >= threshold)
    candidates = [
        (float(deltas[row, col]), int(row + 1), int(col))
        for row, col in candidate_indices
    ]
    selected = sorted(candidates, key=lambda item: item[0], reverse=True)[:max_events]

    events: list[SimulationEvent] = []
    for delta, sample_index, region_index in selected:
        previous_value = float(matrix[sample_index - 1, region_index])
        current_value = float(matrix[sample_index, region_index])
        region = (
            region_names[region_index]
            if region_index < len(region_names)
            else f"region_{region_index}"
        )
        time_s = _time_at(time, sample_index)
        trial_context = _trial_context_at(time_s, trial_contexts)
        events.append(
            SimulationEvent(
                time_s=time_s,
                event_type="significant_region_activity_change",
                label_pl=EVENT_TERM_GLOSSARY["significant_region_activity_change"],
                description_pl=(
                    f"Istotna zmiana aktywności regionu {region}: "
                    f"{previous_value:.3f} → {current_value:.3f}."
                ),
                source="activity",
                trial_id=trial_context["trial_id"],
                trial_number=trial_context["trial_number"],
                condition=trial_context["condition"],
                details={
                    "region": region,
                    "trial_number": trial_context["trial_number"],
                    "previous_value": round(previous_value, 6),
                    "current_value": round(current_value, 6),
                    "abs_delta": round(delta, 6),
                    "sample_index": sample_index,
                },
                plot_anchor=f"activity.{region}",
            )
        )
    return events


def _trial_contexts(trial_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Buduje przedziały czasowe triali do przypisania zdarzeń diagnostycznych."""
    contexts: list[dict[str, Any]] = []
    for event in trial_events:
        onset_s = float(event.get("onset_s", 0.0) or 0.0)
        duration_s = float(event.get("duration_s", 0.0) or 0.0)
        contexts.append(
            {
                "trial_id": event.get("trial_id") or "n/a",
                "trial_number": _trial_number_from_id(event.get("trial_id")),
                "condition": str(event.get("condition") or "n/a"),
                "start_s": onset_s,
                "end_s": onset_s + max(duration_s, 0.0) + 0.75,
            }
        )
    return sorted(contexts, key=lambda item: float(item["start_s"]))


def _trial_context_at(
    time_s: float, trial_contexts: list[dict[str, Any]]
) -> dict[str, Any]:
    """Zwraca kontekst trialu aktywny w danym czasie albo wartości globalne."""
    for context in trial_contexts:
        if float(context["start_s"]) <= time_s <= float(context["end_s"]):
            return {
                "trial_id": context["trial_id"],
                "trial_number": context.get("trial_number"),
                "condition": context["condition"],
            }
    return {"trial_id": "n/a", "trial_number": None, "condition": "n/a"}


def _time_at(time: np.ndarray, sample_index: int) -> float:
    """Zwraca czas dla indeksu próbki z bezpiecznym ograniczeniem zakresu."""
    if time is None or getattr(time, "size", 0) == 0:
        return 0.0
    bounded_index = min(max(sample_index, 0), int(time.size - 1))
    return float(time[bounded_index])


def _to_builtin(value: Any) -> Any:
    """Konwertuje wartości NumPy na typy wbudowane dla zapisu JSON."""
    if isinstance(value, dict):
        return {str(key): _to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_builtin(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _trial_number_from_id(trial_id: Any) -> int | None:
    """Zwraca numeryczny numer trialu albo ``None`` dla zdarzeń globalnych.

    Parameters
    ----------
    trial_id:
        Identyfikator trialu zapisany w bodźcu, wyniku albo osi czasu.

    Returns
    -------
    int | None
        Numer trialu używany do stabilnego grupowania raportów roving oddball.
    """
    if trial_id in {None, "n/a"}:
        return None
    try:
        return int(trial_id)
    except (TypeError, ValueError):
        return None
