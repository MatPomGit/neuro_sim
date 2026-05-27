import numpy as np

from brain_core.analysis.signal_metrics import (
    band_powers,
    comparative_report,
    connectivity_matrix,
    phase_locking_value,
)
from brain_core.physiology.bold_hrf import canonical_hrf, convolve_with_hrf
from brain_core.physiology.eeg_forward_model import EEGForwardModel, EEGInverseSolver, ForwardModelConfig
from brain_core.physiology.neurovascular_coupling import neural_drive_from_activity


def test_eeg_forward_projection_shapes():
    model = EEGForwardModel(np.array([[1.0, 0.5], [0.2, 1.0]]))
    vec = model.project(np.array([1.0, 2.0]))
    assert vec.shape == (2,)
    mat = model.project(np.array([[1.0, 2.0], [0.5, 0.5]]))
    assert mat.shape == (2, 2)


def test_eeg_forward_average_reference_zero_mean_per_sample():
    model = EEGForwardModel(
        np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]),
        config=ForwardModelConfig(reference="average"),
    )
    eeg = model.project(np.array([[1.0, 2.0], [2.0, 3.0]]))
    assert np.allclose(np.mean(eeg, axis=1), 0.0)


def test_eeg_inverse_recovers_sources_for_low_noise_case():
    leadfield = np.array([[1.0, 0.2], [0.1, 1.2], [0.7, 0.3]])
    sources = np.array([[0.5, 1.0], [1.2, -0.4], [0.0, 0.3]])
    eeg = EEGForwardModel(leadfield).project(sources)
    inv = EEGInverseSolver(leadfield)

    mne = inv.minimum_norm(eeg, lam=1e-4)
    wmne = inv.weighted_minimum_norm(eeg, lam=1e-4, depth=np.array([1.0, 0.8]))

    assert mne.shape == sources.shape
    assert wmne.shape == sources.shape
    assert np.mean(np.abs(mne - sources)) < 0.15


def test_bold_pipeline_shapes():
    neural = np.array([[0.0, 0.2], [0.4, 0.6], [0.1, 0.3]])
    drive = neural_drive_from_activity(neural, baseline=0.1)
    hrf = canonical_hrf(length=10, dt=0.5)
    bold = convolve_with_hrf(drive, hrf)
    assert bold.shape == neural.shape


def test_analysis_metrics_outputs():
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

from brain_core.analysis.benchmark_loader import load_reference_benchmarks
from brain_core.analysis.reports import build_analysis_report
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import run_experiment


def test_reference_benchmark_loader_shapes():
    benchmark = load_reference_benchmarks()
    assert set(benchmark.keys()) == {"eeg", "fmri", "behavior"}
    assert benchmark["eeg"].ndim == 2
    assert benchmark["fmri"].ndim == 2
    assert benchmark["behavior"].ndim == 2


def test_report_structure_and_metric_stability():
    cfg = ExperimentConfig(output={"save_results": False, "label": "test", "output_dir": "outputs"}, seed=11)
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
