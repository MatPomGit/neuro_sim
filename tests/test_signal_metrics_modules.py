"""Testy jednostkowe metryk sygnałowych na danych syntetycznych."""

from __future__ import annotations

import numpy as np

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
