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
