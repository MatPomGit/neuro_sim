import json
from pathlib import Path
from typing import Any

import numpy as np

from brain_core.analysis.benchmark_loader import load_reference_benchmarks
from brain_core.analysis.signal_metrics import (
    band_powers,
    comparative_report,
    connectivity_matrix,
    phase_locking_value,
)
from brain_core.physiology.bold_hrf import canonical_hrf, convolve_with_hrf
from brain_core.physiology.eeg_forward_model import (
    EEGForwardModel,
    EEGInverseSolver,
    ForwardModelConfig,
)
from brain_core.physiology.neurovascular_coupling import neural_drive_from_activity
from brain_core.simulation.config_loader import (
    load_clinical_profile,
    load_clinical_profiles,
    load_config,
)
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import (
    run_experiment,
    run_task_across_clinical_profiles,
)


def test_eeg_forward_projection_shapes() -> Any:
    """Opis funkcji test_eeg_forward_projection_shapes."""
    model = EEGForwardModel(np.array([[1.0, 0.5], [0.2, 1.0]]))
    vec = model.project(np.array([1.0, 2.0]))
    assert vec.shape == (2,)
    mat = model.project(np.array([[1.0, 2.0], [0.5, 0.5]]))
    assert mat.shape == (2, 2)


def test_eeg_forward_average_reference_zero_mean_per_sample() -> Any:
    """Opis funkcji test_eeg_forward_average_reference_zero_mean_per_sample."""
    model = EEGForwardModel(
        np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]),
        config=ForwardModelConfig(reference="average"),
    )
    eeg = model.project(np.array([[1.0, 2.0], [2.0, 3.0]]))
    assert np.allclose(np.mean(eeg, axis=1), 0.0)


def test_eeg_inverse_recovers_sources_for_low_noise_case() -> Any:
    """Opis funkcji test_eeg_inverse_recovers_sources_for_low_noise_case."""
    leadfield = np.array([[1.0, 0.2], [0.1, 1.2], [0.7, 0.3]])
    sources = np.array([[0.5, 1.0], [1.2, -0.4], [0.0, 0.3]])
    eeg = EEGForwardModel(leadfield).project(sources)
    inv = EEGInverseSolver(leadfield)

    mne = inv.minimum_norm(eeg, lam=1e-4)
    wmne = inv.weighted_minimum_norm(eeg, lam=1e-4, depth=np.array([1.0, 0.8]))

    assert mne.shape == sources.shape
    assert wmne.shape == sources.shape
    assert np.mean(np.abs(mne - sources)) < 0.15


def test_bold_pipeline_shapes() -> Any:
    """Opis funkcji test_bold_pipeline_shapes."""
    neural = np.array([[0.0, 0.2], [0.4, 0.6], [0.1, 0.3]])
    drive = neural_drive_from_activity(neural, baseline=0.1)
    hrf = canonical_hrf(length=10, dt=0.5)
    bold = convolve_with_hrf(drive, hrf)
    assert bold.shape == neural.shape


def test_analysis_metrics_outputs() -> Any:
    """Opis funkcji test_analysis_metrics_outputs."""
    fs = 200.0
    t = np.arange(0, 1.0, 1.0 / fs)
    s1 = np.sin(2 * np.pi * 10 * t)
    s2 = np.sin(2 * np.pi * 10 * t + np.pi / 4)

    bp = band_powers(s1, fs)
    assert bp["alpha"] > bp["delta"]
    plv = phase_locking_value(s1, s2)
    assert 0.0 <= plv <= 1.0

    conn = connectivity_matrix(np.column_stack([s1, s2]))
    assert conn.shape == (2, 2)

    rep = comparative_report(np.column_stack([s1, s2]), np.column_stack([s1, s2]))
    assert rep["mae"] == 0.0


def test_reference_benchmark_loader_shapes() -> Any:
    """Opis funkcji test_reference_benchmark_loader_shapes."""
    benchmark = load_reference_benchmarks()
    assert set(benchmark.keys()) == {"eeg", "fmri", "behavior"}
    assert benchmark["eeg"].ndim == 2
    assert benchmark["fmri"].ndim == 2
    assert benchmark["behavior"].ndim == 2


def test_report_structure_and_metric_stability() -> Any:
    """Opis funkcji test_report_structure_and_metric_stability."""
    cfg = ExperimentConfig(
        output={"save_results": False, "label": "test", "output_dir": "outputs"},
        seed=11,
    )
    run_a = run_experiment(cfg)
    run_b = run_experiment(cfg)

    report_a = run_a["analysis_report"]
    report_b = run_b["analysis_report"]

    assert "metrics" in report_a
    assert "comparison" in report_a
    required = {
        "band_power_alpha",
        "band_power_beta",
        "erp_proxy_peak_to_peak",
        "phase_locking_value",
        "connectivity_mean",
        "behavior_mean",
        "fmri_mean",
    }
    assert required.issubset(report_a["metrics"].keys())

    for key in required:
        assert np.isclose(report_a["metrics"][key], report_b["metrics"][key])


def test_run_task_across_clinical_profiles_keeps_seed_and_reports_differences() -> Any:
    """Porównanie profili klinicznych zachowuje task, seed i sekcję różnic."""
    cfg = ExperimentConfig(
        output={"save_results": False, "label": "test", "output_dir": "outputs"},
        seed=5,
        task={"name": "stroop", "scenario": "reward-learning", "duration": 0.2},
    )
    profiles = load_clinical_profiles(
        [
            "configs/clinical_profiles/healthy_v1.yaml",
            "configs/clinical_profiles/dopamine_deficit.yaml",
        ]
    )

    batch = run_task_across_clinical_profiles(cfg, profiles)

    assert batch["seed"] == 5
    assert batch["task"] == cfg.task
    assert batch["reference_profile_id"] == "healthy_v1"
    assert set(batch["runs"]) == {"healthy_v1", "dopamine_deficit"}
    differences = batch["clinical_difference_report"]["clinical_differences"]
    assert differences[0]["profile_id"] == "dopamine_deficit"
    assert {"region", "time_s", "cognitive_function", "mechanism"}.issubset(
        differences[0]
    )


def test_reference_benchmark_metadata_validation() -> Any:
    """Metadane benchmarków powinny opisywać źródło, zakres, ograniczenia i poziom."""
    from brain_core.analysis.benchmark_loader import load_reference_benchmark_metadata

    metadata = load_reference_benchmark_metadata()

    assert set(metadata.keys()) == {"eeg", "fmri", "behavior"}
    assert metadata["eeg"].level == "synthetic"
    assert metadata["behavior"].level == "educational"
    for item in metadata.values():
        assert item.source
        assert item.scope
        assert item.limitations
        assert item.compliance_criteria
        assert item.level in {
            "synthetic",
            "educational",
            "literature-inspired",
            "empirical",
        }


def test_reference_benchmark_metadata_rejects_invalid_level(tmp_path: Any) -> Any:
    """Walidacja metadanych powinna odrzucać poziomy spoza rejestru."""
    import json

    from brain_core.analysis.benchmark_loader import (
        BenchmarkValidationError,
        load_reference_benchmark_metadata,
    )

    metadata_path = tmp_path / "benchmark_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "eeg": {
                    "source": "test",
                    "scope": "test",
                    "limitations": "test",
                    "level": "unknown",
                    "compliance_criteria": "test",
                },
                "fmri": {
                    "source": "test",
                    "scope": "test",
                    "limitations": "test",
                    "level": "synthetic",
                    "compliance_criteria": "test",
                },
                "behavior": {
                    "source": "test",
                    "scope": "test",
                    "limitations": "test",
                    "level": "empirical",
                    "compliance_criteria": "test",
                },
            }
        ),
        encoding="utf-8",
    )
    load_reference_benchmark_metadata.cache_clear()

    try:
        load_reference_benchmark_metadata(tmp_path)
    except BenchmarkValidationError as error:
        assert "nieobsługiwany poziom" in str(error)
    else:
        raise AssertionError("Oczekiwano błędu walidacji poziomu benchmarku.")
    finally:
        load_reference_benchmark_metadata.cache_clear()


def test_report_marks_benchmark_origin_in_markdown() -> Any:
    """Raport powinien pokazywać syntetyczny albo empiryczny charakter benchmarku."""
    from brain_core.analysis.reports import AnalysisReport

    report = AnalysisReport(
        payload={
            "metrics": {},
            "comparison": {},
            "benchmark_metadata": {
                "eeg": {
                    "source": "test",
                    "scope": "test",
                    "limitations": "test",
                    "level": "synthetic",
                    "compliance_criteria": "test",
                    "comparison_origin_pl": "syntetyczny",
                },
                "behavior": {
                    "source": "test",
                    "scope": "test",
                    "limitations": "test",
                    "level": "empirical",
                    "compliance_criteria": "test",
                    "comparison_origin_pl": "empiryczny",
                },
            },
        }
    )

    markdown = report.to_markdown()
    csv_rows = report.to_csv_rows()

    assert "## Status walidacji" in markdown
    assert "walidacja syntetyczna" in markdown
    assert "walidacja empiryczna" in markdown
    assert "benchmark syntetyczny" in markdown
    assert "benchmark empiryczny" in markdown
    assert {
        (row["metric"], row["value"])
        for row in csv_rows
        if row["section"] == "validation_status"
    } == {("eeg", "synthetic"), ("behavior", "empirical")}


def test_validation_registry_benchmarks_are_reported() -> Any:
    """Każdy benchmark z pliku metadanych ma wpis w rejestrze i raporcie."""
    import json
    from pathlib import Path

    from brain_core.analysis.benchmark_loader import load_reference_benchmark_bundle
    from brain_core.analysis.reports import (
        build_analysis_report,
        load_validation_registry,
    )

    bundle = load_reference_benchmark_bundle()
    metadata_from_file = json.loads(
        Path("data/validation/benchmark_metadata.json").read_text(encoding="utf-8")
    )
    registry = load_validation_registry()

    report = build_analysis_report(
        eeg=bundle.data["eeg"],
        fmri=bundle.data["fmri"],
        behavior=bundle.data["behavior"],
        benchmark=bundle.data,
        benchmark_metadata=bundle.metadata_payload(),
    )
    markdown = report.to_markdown()
    reported_benchmarks = {
        item["benchmark"] for item in report.payload["validation_compliance"]
    }

    assert set(metadata_from_file) == set(bundle.metadata)
    assert set(metadata_from_file) <= set(registry)
    assert reported_benchmarks == set(metadata_from_file)
    assert "## Zgodność walidacyjna" in markdown
    for benchmark_name, metadata in bundle.metadata_payload().items():
        assert f"| {benchmark_name} | {metadata['level']} |" in markdown
        assert f"{benchmark_name}_mae" in " ".join(report.payload["comparison"])


def test_roving_oddball_profiles_share_seed_and_sequence() -> Any:
    """Porównanie roving oddball zachowuje identyczny seed i sekwencję profili."""
    cfg = ExperimentConfig(
        output={"save_results": False, "label": "test", "output_dir": "outputs"},
        seed=21,
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
    )
    profiles = load_clinical_profiles(
        [
            "configs/clinical_profiles/healthy_v1.yaml",
            "configs/clinical_profiles/gaba_dysregulation.yaml",
            "configs/clinical_profiles/hippocampal_lesion.yaml",
        ]
    )

    batch = run_task_across_clinical_profiles(cfg, profiles)

    comparison = batch["roving_profile_comparison"]
    assert comparison["seed"] == 21
    assert comparison["same_seed"] is True
    assert comparison["same_sequence"] is True
    assert {profile["profile_id"] for profile in comparison["profiles"]} == {
        "healthy_v1",
        "gaba_dysregulation",
        "hippocampal_lesion",
    }
    profile_groups = {profile["profile_group"] for profile in comparison["profiles"]}
    assert profile_groups == {"healthy", "disorder", "lesion"}
    for profile in comparison["profiles"]:
        assert {
            "profile_group",
            "mean_surprise_index",
            "habituation_rate",
            "mean_readaptation_latency",
        }.issubset(profile)


def test_clinical_difference_report_classifies_disorders_and_lesions() -> Any:
    """Raport ma klasyfikować różnice dla trzech zaburzeń i dwóch lesion."""
    cfg = ExperimentConfig(
        output={"save_results": False, "label": "test", "output_dir": "outputs"},
        seed=13,
        task={"scenario": "reward-learning", "duration": 2.0},
    )
    profiles = load_clinical_profiles(
        [
            "configs/clinical_profiles/healthy_v1.yaml",
            "configs/clinical_profiles/dopamine_deficit.yaml",
            "configs/clinical_profiles/gaba_dysregulation.yaml",
            "configs/clinical_profiles/serotonin_imbalance.yaml",
            "configs/clinical_profiles/hippocampal_lesion.yaml",
            "configs/clinical_profiles/dlpfc_weakening.yaml",
        ]
    )

    batch = run_task_across_clinical_profiles(cfg, profiles)

    differences = batch["clinical_difference_report"]["clinical_differences"]
    differences_by_profile = {item["profile_id"]: item for item in differences}
    assert set(differences_by_profile) == {
        "dopamine_deficit",
        "gaba_dysregulation",
        "serotonin_imbalance",
        "hippocampal_lesion",
        "dlpfc_weakening",
    }
    assert {
        differences_by_profile["dopamine_deficit"]["difference_classification"],
        differences_by_profile["gaba_dysregulation"]["difference_classification"],
        differences_by_profile["serotonin_imbalance"]["difference_classification"],
    } <= {"mała różnica", "średnia różnica", "duża różnica"}
    assert {
        differences_by_profile["hippocampal_lesion"]["difference_classification"],
        differences_by_profile["dlpfc_weakening"]["difference_classification"],
    } <= {"mała różnica", "średnia różnica", "duża różnica"}
    for item in differences:
        assert item["primary_metric"] == "mean_abs_difference"
        assert item["expected_direction"] != "n/a"
        assert item["severity_level"]["medium"] == 0.02
        assert "Mechanizm:" in item["educational_comment"]
        assert item["mechanism"] in item["educational_comment"]
        assert item["cognitive_function"] in item["educational_comment"]


def test_roving_oddball_report_groups_trials_and_exports_text_reports(
    tmp_path: Any,
) -> Any:
    """Raport grupuje triale i eksportuje MD/HTML z tabelą oraz słownikiem."""
    from brain_core.analysis.reports import AnalysisReport
    from brain_model.report_export import export_experiment_report

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
    markdown = AnalysisReport(result["analysis_report"]).to_markdown()
    md_path = export_experiment_report(
        tmp_path / "raport.md",
        status_message="Symulacja zakończona.",
        summary_text="Skrót testowy.",
        state_config={"task": "roving_oddball"},
        event_timeline=result["event_timeline"],
        clinical_profile=result["clinical_profile"],
        analysis_report=result["analysis_report"],
    )
    html_path = export_experiment_report(
        tmp_path / "raport.html",
        status_message="Symulacja zakończona.",
        summary_text="Skrót testowy.",
        state_config={"task": "roving_oddball"},
        event_timeline=result["event_timeline"],
        clinical_profile=result["clinical_profile"],
        analysis_report=result["analysis_report"],
    )

    md_text = md_path.read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")
    assert "### Grupy triali" in markdown
    assert "**bodziec**" in markdown
    assert "**odpowiedź**" in markdown
    assert "**błąd/poprawność**" in markdown
    assert "**zmiana aktywności**" in markdown
    assert "**komentarz mechanizmu**" in markdown
    assert "| Trial | Warunek | Bodziec | Odpowiedź | Wynik |" in md_text
    assert "## Skrót metryk" in md_text
    assert "## Polski słownik pojęć" in md_text
    assert "początek bodźca" in md_text
    assert "<!doctype html>" in html_text
    assert "Tabela triali" in html_text


def test_healthy_v1_profile_has_complete_required_baseline_fields() -> Any:
    """Profil healthy_v1 ma komplet metadanych wymaganych dla baseline."""
    profile_payload = load_clinical_profile("configs/clinical_profiles/healthy_v1.yaml")
    clinical_profile = profile_payload["clinical_profile"]

    required_fields = {
        "id",
        "display_name",
        "mechanism",
        "affected_regions",
        "cognitive_functions",
        "expected_effects",
        "expected_direction",
        "severity_level",
        "primary_metric",
    }

    assert required_fields.issubset(clinical_profile)
    assert clinical_profile["id"] == "healthy_v1"
    assert clinical_profile["expected_direction"] == "stable_reference"
    assert clinical_profile["primary_metric"] == "mean_abs_difference"
    assert clinical_profile["expected_effects"]["clinical_interpretation"]
    assert clinical_profile["severity_level"] == {
        "small": 0.0,
        "medium": 0.02,
        "large": 0.05,
    }


def test_healthy_v1_baseline_metrics_match_reference_thresholds() -> Any:
    """Metryki baseline healthy_v1 mieszczą się w jakościowych tolerancjach."""
    reference_path = Path("data/validation/healthy_v1_baseline_metrics.json")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    config = load_config(reference["config_path"])

    assert reference["artifact_format"] == "healthy_v1_baseline_metrics_v1"
    assert reference["profile_id"] == config.clinical_profile["id"] == "healthy_v1"
    assert reference["seed"] == config.rng_seed == 21

    result = run_experiment(config)
    metrics = result["analysis_report"]["metrics"]

    for metric_name, metric_reference in reference["metrics"].items():
        assert (
            metric_name in metrics
        ), f"Metric '{metric_name}' is missing from the experiment results."
        expected = float(metric_reference["expected"])
        tolerance = float(metric_reference["absolute_tolerance"])
        observed = float(metrics[metric_name])

        assert metric_reference["quality_band"]
        assert abs(observed - expected) <= tolerance


def test_healthy_v1_report_marks_baseline_as_reference_not_diagnosis() -> Any:
    """Raport baseline pokazuje rolę punktu odniesienia bez diagnozy klinicznej."""
    from brain_core.analysis.reports import AnalysisReport

    config = load_config("configs/roving_oddball_healthy.yaml")
    result = run_experiment(config)
    report = AnalysisReport(result["analysis_report"])

    markdown = report.to_markdown()
    csv_rows = report.to_csv_rows()

    assert "## Baseline healthy_v1" in markdown
    assert "punkt odniesienia" in markdown
    assert "nie jest diagnozą kliniczną" in markdown
    assert any(row["section"] == "baseline_reference" for row in csv_rows)
