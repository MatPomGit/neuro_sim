"""Porównania profili klinicznych uruchamianych na wspólnym zadaniu."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any, Callable

from brain_core.analysis.reports import (
    build_clinical_difference_report,
    build_roving_oddball_report,
)
from brain_core.experiments.protocols import TrialStimulus

from .config_schema import ExperimentConfig


def build_stimulus_sequence_signature(
    stimulus_sequence: list[TrialStimulus],
) -> list[dict[str, Any]]:
    """Zbuduj stabilny podpis sekwencji bodźców do porównań profili.

    Parameters
    ----------
    stimulus_sequence:
        Bodźce wygenerowane raz dla wspólnego seeda i przekazywane do wszystkich
        profili klinicznych w porównaniu.

    Returns:
    -------
    list[dict[str, Any]]
        Minimalna lista pól determinujących sekwencję bodźców, bez wyników modelu
        i bez metadanych profilu klinicznego.
    """
    return [
        {
            "trial_id": stimulus.trial_id,
            "onset_s": stimulus.onset_s,
            "duration_s": stimulus.duration_s,
            "condition": stimulus.condition,
            "payload": (
                {key: stimulus.payload[key] for key in sorted(stimulus.payload)}
                if isinstance(stimulus.payload, dict)
                else {}
            ),
        }
        for stimulus in stimulus_sequence
    ]


def classify_roving_profile_group(profile_id: str, result: dict[str, Any]) -> str:
    """Klasyfikuje profil roving oddball do grupy healthy/disorder/lesion."""
    profile = result.get("clinical_profile") or {}
    profile_text = " ".join(
        str(value).lower()
        for value in (
            profile_id,
            profile.get("id", ""),
            profile.get("mechanism", ""),
            profile.get("display_name", ""),
        )
    )
    pathology = (result.get("analysis_report") or {}).get("clinical_profile") or {}
    pathology_text = str(pathology.get("pathology_scenario", "")).lower()
    combined_text = f"{profile_text} {pathology_text}"
    if "lesion" in combined_text or "uszkod" in combined_text:
        return "lesion"
    if "healthy" in combined_text or "zdrow" in combined_text:
        return "healthy"
    return "disorder"


def describe_roving_signed_difference(
    value: float,
    *,
    positive_label: str,
    negative_label: str,
) -> str:
    """Opisuje znak różnicy profilu względem wariantu zdrowego."""
    tolerance = 1e-7
    if value > tolerance:
        return positive_label
    if value < -tolerance:
        return negative_label
    return "bez obserwowanej różnicy"


def build_roving_profile_pair_comparisons(
    profiles: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Buduje dydaktyczne porównania profili roving oddball względem zdrowego."""
    if not profiles:
        return []
    reference = next(
        (profile for profile in profiles if profile.get("profile_group") == "healthy"),
        profiles[0],
    )
    reference_mechanism = (
        reference.get("amplitude_latency_mechanism")
        if isinstance(reference.get("amplitude_latency_mechanism"), dict)
        else {}
    )
    reference_amplitude = float(reference_mechanism.get("response_amplitude", 0.0))
    reference_latency = float(reference.get("mean_readaptation_latency", 0.0))
    comparisons: list[dict[str, object]] = []
    for profile in profiles:
        if profile is reference:
            continue
        mechanism = (
            profile.get("amplitude_latency_mechanism")
            if isinstance(profile.get("amplitude_latency_mechanism"), dict)
            else {}
        )
        amplitude_difference = round(
            float(mechanism.get("response_amplitude", 0.0)) - reference_amplitude,
            6,
        )
        readaptation_difference = round(
            float(profile.get("mean_readaptation_latency", 0.0)) - reference_latency,
            6,
        )
        threshold = float(mechanism.get("qualitative_threshold", 0.05))
        if (
            abs(amplitude_difference) >= threshold
            or abs(readaptation_difference) >= threshold
        ):
            threshold_result = "przekroczony próg jakościowy"
        else:
            threshold_result = "poniżej progu jakościowego"
        observed_amplitude_direction = describe_roving_signed_difference(
            amplitude_difference,
            positive_label="wyższa amplituda proxy niż w profilu zdrowym",
            negative_label="niższa amplituda proxy niż w profilu zdrowym",
        )
        observed_readaptation_direction = describe_roving_signed_difference(
            readaptation_difference,
            positive_label="dłuższa readaptacja niż w profilu zdrowym",
            negative_label="krótsza readaptacja niż w profilu zdrowym",
        )
        observed_difference_comment = (
            f"Obserwacja: {observed_amplitude_direction}; "
            f"{observed_readaptation_direction}. "
            f"Wynik jakościowy: {threshold_result}."
        )
        comparisons.append(
            {
                "reference_profile_id": reference.get("profile_id", "healthy_v1"),
                "profile_id": profile.get("profile_id", "n/a"),
                "profile_group": profile.get("profile_group", "n/a"),
                "expected_amplitude_direction": mechanism.get(
                    "expected_amplitude_direction", "stable_reference"
                ),
                "expected_readaptation_direction": mechanism.get(
                    "expected_readaptation_direction", "stable_reference"
                ),
                "observed_amplitude_difference": amplitude_difference,
                "observed_readaptation_difference": readaptation_difference,
                "observed_amplitude_direction": observed_amplitude_direction,
                "observed_readaptation_direction": observed_readaptation_direction,
                "qualitative_threshold": threshold,
                "threshold_result": threshold_result,
                "observed_difference_comment": observed_difference_comment,
                "educational_comment": mechanism.get(
                    "educational_comment",
                    "Porównanie pokazuje kierunek różnicy w symulacji względem "
                    "profilu zdrowego; nie zastępuje walidacji empirycznej.",
                ),
            }
        )
    return comparisons


def build_roving_profile_comparison(
    *,
    seed: int,
    runs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Porównuje metryki roving oddball przy wspólnym seedzie i sekwencji."""
    profiles: list[dict[str, object]] = []
    signatures: list[Any] = []
    for profile_id, result in runs.items():
        roving_report = build_roving_oddball_report(
            result.get("trial_results") or [],
            profile_id=profile_id,
            clinical_profile=result.get("clinical_profile") or {},
        )
        roving_report["profile_group"] = classify_roving_profile_group(
            profile_id,
            result,
        )
        profiles.append(roving_report)
        signatures.append(roving_report.get("sequence_signature") or [])

    reference_signature = signatures[0] if signatures else []
    same_sequence = all(signature == reference_signature for signature in signatures)
    return {
        "seed": seed,
        "same_seed": True,
        "same_sequence": same_sequence,
        "profiles": profiles,
        "comparisons": build_roving_profile_pair_comparisons(profiles),
    }


def summarize_batch_profiles(runs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Zwraca stabilne metadane profili obecnych w porównaniu batch."""
    profiles: list[dict[str, Any]] = []
    for profile_id, result in runs.items():
        profile = result.get("clinical_profile") or {}
        profiles.append(
            {
                "profile_id": str(profile.get("id", profile_id)),
                "display_name": str(profile.get("display_name", profile_id)),
                "mechanism": str(profile.get("mechanism", "n/a")),
                "affected_regions": list(profile.get("affected_regions") or []),
                "cognitive_functions": list(
                    profile.get("cognitive_functions")
                    or result.get("task_activation", {}).get("functions", [])
                ),
                "expected_direction": str(
                    profile.get("expected_direction", "stable_reference")
                ),
            }
        )
    return profiles


def build_profile_comparison_table(
    clinical_differences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalizuje różnice kliniczne do tabeli raportowej porównania profili."""
    rows: list[dict[str, Any]] = []
    for item in clinical_differences:
        rows.append(
            {
                "profile": item.get("compared_profile")
                or item.get("profile_id", "n/a"),
                "expected_direction": item.get("expected_direction", "n/a"),
                "observed_direction": item.get("observed_direction", "n/a"),
                "qualitative_threshold": item.get("qualitative_threshold", "n/a"),
                "interpretation": item.get("educational_comment", "n/a"),
            }
        )
    return rows


def build_batch_educational_comments(
    clinical_differences: list[dict[str, Any]],
) -> list[str]:
    """Wyodrębnia komentarze dydaktyczne do stabilnego API batch."""
    return [
        str(item["educational_comment"])
        for item in clinical_differences
        if item.get("educational_comment") is not None
        and str(item["educational_comment"]).strip()
    ]


def apply_clinical_profile_config(
    base_config: ExperimentConfig,
    profile_config: dict[str, Any],
) -> ExperimentConfig:
    """Scal bazową konfigurację zadania z pojedynczym profilem klinicznym."""
    profile = deepcopy(profile_config)
    merged_model = deepcopy(base_config.model)
    merged_model.update(profile.get("model") or {})

    output = deepcopy(base_config.output)
    profile_metadata = profile.get("clinical_profile") or {}
    profile_id = profile_metadata.get("id", output.get("label", "clinical_profile"))
    output.update(profile.get("output") or {})
    output["label"] = str(profile_id)

    return replace(
        base_config,
        model=merged_model,
        pathology=deepcopy(profile.get("pathology") or base_config.pathology),
        output=output,
        clinical_profile=deepcopy(profile_metadata),
    )


def run_task_across_clinical_profiles(
    base_config: ExperimentConfig,
    clinical_profiles: list[dict[str, Any]],
    *,
    experiment_runner: Callable[..., dict[str, Any]],
    stimulus_generator: Callable[[ExperimentConfig], list[TrialStimulus]],
    progress_callback: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Uruchom ten sam task z tym samym seedem dla wielu profili klinicznych."""
    if not clinical_profiles:
        raise ValueError("Lista profili klinicznych nie może być pusta.")

    shared_stimulus_sequence = stimulus_generator(base_config)

    runs: dict[str, dict[str, Any]] = {}
    for profile_config in clinical_profiles:
        profile_id = str(
            profile_config.get("clinical_profile", {}).get("id", "profile")
        )
        profile_run_config = apply_clinical_profile_config(base_config, profile_config)
        runs[profile_id] = experiment_runner(
            profile_run_config,
            progress_callback=progress_callback,
            stimulus_sequence=shared_stimulus_sequence,
        )

    sequence_signatures = [
        result.get("stimulus_sequence_signature") or [] for result in runs.values()
    ]
    reference_signature = sequence_signatures[0] if sequence_signatures else []
    same_stimulus_sequence = all(
        signature == reference_signature for signature in sequence_signatures
    )

    reference_id = "healthy_v1" if "healthy_v1" in runs else next(iter(runs))
    compared = {key: value for key, value in runs.items() if key != reference_id}
    difference_report = build_clinical_difference_report(runs[reference_id], compared)
    clinical_differences = list(
        difference_report.payload.get("clinical_differences", [])
    )
    profiles = summarize_batch_profiles(runs)
    profile_comparison_table = build_profile_comparison_table(clinical_differences)
    educational_comments = build_batch_educational_comments(clinical_differences)
    difference_report.payload["stimulus_sequence_signature"] = reference_signature
    difference_report.payload["same_seed"] = True
    difference_report.payload["same_stimulus_sequence"] = same_stimulus_sequence
    difference_report.payload["reference_profile_id"] = reference_id
    difference_report.payload["profiles"] = profiles
    difference_report.payload["metric_differences"] = clinical_differences
    difference_report.payload["profile_comparison_table"] = profile_comparison_table
    difference_report.payload["educational_comments"] = educational_comments
    batch_report: dict[str, Any] = {
        "seed": base_config.seed,
        "same_seed": True,
        "same_stimulus_sequence": same_stimulus_sequence,
        "stimulus_sequence_signature": reference_signature,
        "shared_stimulus_sequence_reused": True,
        "task": dict(base_config.task),
        "reference_profile_id": reference_id,
        "profiles": profiles,
        "metric_differences": clinical_differences,
        "profile_comparison_table": profile_comparison_table,
        "educational_comments": educational_comments,
        "runs": runs,
        "clinical_difference_report": difference_report.payload,
    }
    if str(base_config.task.get("name") or "") in {"roving_oddball", "roving-oddball"}:
        roving_profile_comparison = build_roving_profile_comparison(
            seed=base_config.seed,
            runs=runs,
        )
        batch_report["roving_profile_comparison"] = roving_profile_comparison
        difference_report.payload["roving_profile_comparison"] = (
            roving_profile_comparison
        )
    return batch_report
