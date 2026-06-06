"""Metryki spektralne sygnałów neuro."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BAND_LIMITS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "beta": (12.0, 30.0),
    "gamma": (30.0, 80.0),
}

REPORTABLE_SPECTRAL_METRICS = (
    {
        "name": "band_power_delta",
        "scope": "pasmo delta",
        "unit": "moc widmowa proxy [amplituda²]",
        "profile_groups": ("healthy", "disorder", "lesion"),
        "interpretation_pl": (
            "Moc pasma delta gotowa do porównań profili jako opis wolnej "
            "aktywności oscylacyjnej."
        ),
        "limitations_pl": (
            "Metryka pochodzi z uproszczonego widma FFT i nie zastępuje "
            "walidowanej analizy klinicznej EEG."
        ),
    },
    {
        "name": "band_power_theta",
        "scope": "pasmo theta",
        "unit": "moc widmowa proxy [amplituda²]",
        "profile_groups": ("healthy", "disorder", "lesion"),
        "interpretation_pl": (
            "Moc theta wspiera raportowanie rytmów związanych z pamięcią "
            "i kontrolą poznawczą w profilu symulacji."
        ),
        "limitations_pl": (
            "Zakres pasma jest stały, a wynik zależy od długości sygnału "
            "i częstotliwości próbkowania."
        ),
    },
    {
        "name": "band_power_alpha",
        "scope": "pasmo alpha",
        "unit": "moc widmowa proxy [amplituda²]",
        "profile_groups": ("healthy", "disorder", "lesion"),
        "interpretation_pl": (
            "Moc alpha jest gotowa do raportowania jako marker rytmu "
            "hamowania i odniesienia spoczynkowego."
        ),
        "limitations_pl": (
            "To syntetyczna miara mocy, bez korekty artefaktów i bez "
            "wnioskowania diagnostycznego."
        ),
    },
    {
        "name": "band_power_beta",
        "scope": "pasmo beta",
        "unit": "moc widmowa proxy [amplituda²]",
        "profile_groups": ("healthy", "disorder", "lesion"),
        "interpretation_pl": (
            "Moc beta opisuje rytm zadaniowy i może być zestawiana między "
            "profilami healthy/disorder/lesion."
        ),
        "limitations_pl": (
            "Interpretuj trend względny, bo model nie kalibruje amplitudy do "
            "empirycznych jednostek EEG."
        ),
    },
    {
        "name": "band_power_gamma",
        "scope": "pasmo gamma",
        "unit": "moc widmowa proxy [amplituda²]",
        "profile_groups": ("healthy", "disorder", "lesion"),
        "interpretation_pl": (
            "Moc gamma raportuje lokalną synchronizację szybkich rytmów "
            "wygenerowanych przez model."
        ),
        "limitations_pl": (
            "Brak modelowania artefaktów mięśniowych, dlatego wynik jest "
            "metryką symulacyjną."
        ),
    },
)


@dataclass(frozen=True)
class SpectralMetricResult:
    """
    Wynik metryk spektralnych z szeregiem i statystykami zbiorczymi.

    Attributes:
        series (dict[str, np.ndarray]): Słownik z seriami spektralnymi.
        summary (dict[str, float]): Słownik z podsumowaniem energii w pasmach.
    """

    series: dict[str, np.ndarray]
    summary: dict[str, float]


def _validate_signal(signal: np.ndarray) -> np.ndarray:
    """
    Waliduje i normalizuje wejście do postaci sygnału 1D.

    Args:
        signal (np.ndarray): Sygnał wejściowy.

    Returns:
        np.ndarray: Sygnał 1D.

    Raises:
        ValueError: Jeśli sygnał nie jest 1D lub jest pusty.
    """
    x = np.asarray(signal, dtype=float)
    if x.ndim != 1:
        raise ValueError("signal must be 1D")
    if x.size == 0:
        raise ValueError("signal cannot be empty")
    return x


def compute_band_powers(
    signal: np.ndarray,
    fs: float,
    bands: dict[str, tuple[float, float]] | None = None,
) -> SpectralMetricResult:
    """
    Liczy energię pasm i zwraca pełne series + podsumowanie.

    Args:
        signal (np.ndarray): Sygnał wejściowy (1D), w jednostkach amplitudy
            syntetycznego EEG modelu.
        fs (float): Częstotliwość próbkowania w hercach [Hz].
        bands (dict[str, tuple[float, float]] | None): Zakresy pasm w hercach [Hz].

    Returns:
        SpectralMetricResult: Wynik z seriami częstotliwości [Hz], widmem mocy
        proxy [amplituda²] i podsumowaniem energii w pasmach.
    """
    x = _validate_signal(signal)
    n = x.shape[0]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    spectrum = np.abs(np.fft.rfft(x)) ** 2 / (n**2)

    selected = bands or BAND_LIMITS
    band_series: dict[str, np.ndarray] = {}
    summary: dict[str, float] = {}
    for name, (f_lo, f_hi) in selected.items():
        mask = (freqs >= f_lo) & (freqs < f_hi)
        values = spectrum[mask]
        band_series[name] = values
        summary[name] = float(np.sum(values))

    return SpectralMetricResult(
        series={
            "frequencies": freqs,
            "power_spectrum": spectrum,
            "band_values": band_series,
        },
        summary=summary,
    )
