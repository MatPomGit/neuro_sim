"""Testy jednostkowe metryk sygnałowych na danych syntetycznych."""

from __future__ import annotations

import numpy as np
import pytest

from brain_core.analysis.connectivity import compute_connectivity
from brain_core.analysis.information_flow import compute_information_flow
from brain_core.analysis.phase_locking import compute_phase_locking
from brain_core.analysis.spectral import compute_band_powers


def test_compute_band_powers_prefers_alpha_for_10hz_signal() -> None:
    """Sygnał 10 Hz powinien mieć dominację pasma alpha."""
    fs = 200.0
    t = np.arange(0, 2.0, 1.0 / fs)
    signal = np.sin(2 * np.pi * 10 * t)

    result = compute_band_powers(signal, fs)

    assert result.summary["alpha"] > result.summary["delta"]
    assert "frequencies" in result.series


def test_compute_phase_locking_detects_locked_phases() -> None:
    """Dwa sygnały o stałym przesunięciu fazowym dają wysokie PLV."""
    fs = 200.0
    t = np.arange(0, 2.0, 1.0 / fs)
    s1 = np.sin(2 * np.pi * 10 * t)
    s2 = np.sin(2 * np.pi * 10 * t + np.pi / 4)

    result = compute_phase_locking(s1, s2)

    assert 0.5 <= result.summary["plv"] <= 1.0
    assert result.series["phase_diff"].shape == s1.shape


def test_compute_connectivity_returns_region_and_pair_metrics() -> None:
    """Metryki konektywności zwracają korelacje, PLI-proxy i siłę regionów."""
    fs = 200.0
    t = np.arange(0, 2.0, 1.0 / fs)
    r1 = np.sin(2 * np.pi * 10 * t)
    r2 = np.sin(2 * np.pi * 10 * t + np.pi / 6)
    r3 = np.random.default_rng(1).normal(0.0, 0.1, size=t.shape)
    data = np.column_stack([r1, r2, r3])

    result = compute_connectivity(data)

    assert result.series["correlation"].shape == (3, 3)
    assert result.series["pli_proxy"].shape == (3, 3)
    assert result.series["region_strength"].shape == (3,)


def test_compute_information_flow_prefers_known_direction() -> None:
    """Przepływ informacji powinien preferować kierunek sygnału prowadzącego."""
    rng = np.random.default_rng(2)
    n = 300
    source = rng.normal(size=n)
    target = np.roll(source, 1)
    target[0] = 0.0
    target += rng.normal(scale=0.05, size=n)
    data = np.column_stack([source, target])

    result = compute_information_flow(data)

    directional = result.series["directional_matrix"]
    assert directional[0, 1] > directional[1, 0]


def test_reportable_signal_metrics_cover_profiles_and_polish_descriptions() -> None:
    """Katalog raportowy zawiera metryki dla healthy/disorder/lesion po polsku."""
    from brain_core.analysis.signal_metrics import reportable_signal_metrics

    catalog = reportable_signal_metrics()
    names = {str(item["name"]) for item in catalog}
    required_names = {
        "band_power_alpha",
        "band_power_beta",
        "erp_proxy_peak_to_peak",
        "phase_locking_value",
        "connectivity_abs_mean",
        "pli_proxy_mean",
        "directional_abs_mean",
        "outgoing_mean",
    }

    assert required_names <= names
    for item in catalog:
        assert {"healthy", "disorder", "lesion"} <= set(item["profile_groups"])
        assert "interpretation_pl" in item
        assert "limitations_pl" in item
        assert len(str(item["interpretation_pl"]).split()) >= 5
        assert str(item["limitations_pl"]).strip()
        assert str(item["unit"]).strip()


def test_physiology_docstrings_describe_units_and_methodology() -> None:
    """Modele EEG/BOLD opisują jednostki proxy i założenia metodologiczne."""
    from brain_core.physiology.bold_hrf import canonical_hrf, convolve_with_hrf
    from brain_core.physiology.eeg_forward_model import EEGForwardModel
    from brain_core.physiology.neurovascular_coupling import neural_drive_from_activity

    docstrings = "\n".join(
        str(obj.__doc__ or "")
        for obj in (
            EEGForwardModel,
            EEGForwardModel.project,
            canonical_hrf,
            convolve_with_hrf,
            neural_drive_from_activity,
        )
    ).lower()

    assert "jednost" in docstrings
    assert "proxy" in docstrings
    assert "sekund" in docstrings
    assert "hrf" in docstrings
    assert "bold" in docstrings


def test_signal_metric_contract_shapes_and_value_ranges() -> None:
    """Sprawdza kontrakt kształtów i zakresów metryk EEG/sieciowych."""
    fs = 128.0
    time = np.arange(0.0, 2.0, 1.0 / fs)
    signals = np.column_stack(
        [
            np.sin(2 * np.pi * 10.0 * time),
            np.sin(2 * np.pi * 10.0 * time + np.pi / 4.0),
            np.cos(2 * np.pi * 6.0 * time),
        ]
    )

    spectral = compute_band_powers(signals[:, 0], fs)
    phase = compute_phase_locking(signals[:, 0], signals[:, 1])
    connectivity = compute_connectivity(signals)
    flow = compute_information_flow(signals)

    expected_rfft_shape = (signals.shape[0] // 2 + 1,)
    assert spectral.series["frequencies"].shape == expected_rfft_shape
    assert spectral.series["power_spectrum"].shape == expected_rfft_shape
    assert all(value >= 0.0 for value in spectral.summary.values())
    assert phase.series["phase_diff"].shape == (signals.shape[0],)
    assert 0.0 <= phase.summary["plv"] <= 1.0
    assert connectivity.series["correlation"].shape == (3, 3)
    assert connectivity.series["pli_proxy"].shape == (3, 3)
    assert connectivity.series["region_strength"].shape == (3,)
    assert np.all(np.abs(connectivity.series["correlation"]) <= 1.0)
    assert np.all(connectivity.series["pli_proxy"] >= 0.0)
    assert np.all(connectivity.series["pli_proxy"] <= 1.0)
    assert flow.series["directional_matrix"].shape == (3, 3)
    assert flow.series["outgoing_strength"].shape == (3,)
    assert np.allclose(np.diag(flow.series["directional_matrix"]), 0.0)
    assert np.all(flow.series["outgoing_strength"] >= 0.0)


def test_physiology_contract_shapes_ranges_and_deterministic_noise() -> None:
    """Sprawdza kontrakt fizjologii EEG/BOLD oraz deterministyczny szum EEG."""
    from brain_core.physiology.bold_hrf import canonical_hrf, convolve_with_hrf
    from brain_core.physiology.eeg_forward_model import (
        EEGForwardModel,
        ForwardModelConfig,
    )
    from brain_core.physiology.neurovascular_coupling import neural_drive_from_activity

    source_activity = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.2, 0.3, 0.4],
            [0.3, 0.2, 0.1],
            [0.4, 0.1, 0.2],
        ]
    )
    leadfield = np.array([[1.0, 0.5, 0.2], [0.1, 0.7, 1.0]])
    model = EEGForwardModel(
        leadfield,
        config=ForwardModelConfig(sensor_noise_std=0.01, reference="average"),
    )

    first_eeg = model.project(source_activity, rng=np.random.default_rng(77))
    second_eeg = model.project(source_activity, rng=np.random.default_rng(77))
    neural_drive = neural_drive_from_activity(source_activity, baseline=0.2)
    hrf = canonical_hrf(length=8, dt=0.5)
    bold = convolve_with_hrf(neural_drive, hrf)

    assert first_eeg.shape == (source_activity.shape[0], leadfield.shape[0])
    assert np.allclose(first_eeg, second_eeg)
    assert np.allclose(np.mean(first_eeg, axis=1), 0.0)
    assert neural_drive.shape == source_activity.shape
    assert np.all(neural_drive >= 0.0)
    assert hrf.shape == (8,)
    assert np.isclose(np.sum(np.abs(hrf)), 1.0)
    with pytest.raises(ValueError, match="hrf.ratio"):
        canonical_hrf(length=8, dt=0.5, ratio=-0.1)
    assert bold.shape == source_activity.shape
    assert np.all(np.isfinite(bold))


def test_eeg_bold_validators_report_contract_names_for_edge_shapes() -> None:
    """Walidatory wejść EEG/BOLD mają wskazywać nazwę kontraktu D."""
    from brain_core.physiology.bold_hrf import convolve_with_hrf
    from brain_core.physiology.eeg_forward_model import EEGForwardModel

    model = EEGForwardModel(np.ones((2, 3)))

    with pytest.raises(ValueError, match="Kontrakt D"):
        model.project(np.ones((4, 2)))
    with pytest.raises(ValueError, match="Kontrakt D"):
        convolve_with_hrf(np.array([-0.1, 0.2]), np.ones(2))
