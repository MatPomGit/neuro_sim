from dataclasses import dataclass

import numpy as np

from .activations import sigmoid


@dataclass
class WilsonCowanParams:
    """
    Parametry banku oscylatorów Wilsona-Cowana.

    Każdy moduł poznawczy ma parę populacji: pobudzającą E i hamującą I.
    Częstotliwości pasm są modelowane przez różne stałe czasowe oraz dodatkowy
    słaby generator fazy, który stabilizuje rytm w paśmie EEG.

    To jest model fenomenologiczny: dobrze nadaje się do symulacji relacji
    między aktywacją poznawczą a rytmami EEG, ale nie zastępuje modelu
    biofizycznego kolumn korowych.
    """

    w_ee: float = 10.5
    w_ei: float = 9.5
    w_ie: float = 10.0
    w_ii: float = 1.0
    baseline_e: float = -2.4
    baseline_i: float = -3.0
    cognitive_drive_gain: float = 2.8
    coupling_gain: float = 0.35
    oscillator_noise: float = 0.01
    phase_drive_gain: float = 0.10


BAND_FREQUENCIES = {
    "theta": 6.0,
    "alpha": 10.0,
    "beta": 20.0,
    "gamma": 40.0,
}


BAND_TIME_CONSTANTS = {
    # Krótsze stałe czasowe pozwalają na szybsze oscylacje.
    # Wartości są dobrane fenomenologicznie dla kroku dt=0.001-0.01.
    "theta": (0.040, 0.070),
    "alpha": (0.025, 0.045),
    "beta": (0.014, 0.026),
    "gamma": (0.007, 0.013),
}


DEFAULT_MODULE_BANDS = {
    # Theta: hipokamp, bufor epizodyczny i pamięć robocza.
    "HIP": "theta",
    "EPIS": "theta",
    "PHON": "theta",
    "VSWM": "theta",
    # Alfa: hamowanie i bramkowanie sensoryczne.
    "VIS": "alpha",
    "AUD": "alpha",
    "INT": "alpha",
    "DMN": "alpha",
    # Beta: kontrola wykonawcza, utrzymanie nastawienia zadaniowego.
    "EXEC": "beta",
    "ATT": "beta",
    "SAL": "beta",
    "MOT": "beta",
    "LANG": "beta",
    # Gamma: lokalne wiązanie cech i reprezentacji.
    "SEM": "gamma",
    "VAL": "gamma",
    "GW": "gamma",
}


class WilsonCowanOscillatorBank:
    """
    Bank oscylatorów Wilsona-Cowana przypisanych do modułów poznawczych.

    Stan ma wymiar (n_modules, 3):
        E     aktywność populacji pobudzającej,
        I     aktywność populacji hamującej,
        phi   faza rytmu pomocniczego stabilizującego pasmo EEG.

    Sygnał EEG modułu jest aproksymowany jako E - I.
    """

    def __init__(
        self,
        module_names: list[str],
        connectivity: np.ndarray,
        band_map: dict[str, str] | None = None,
        params: WilsonCowanParams | None = None,
    ) -> None:
        """Inicjalizuje bank oscylatorów Wilsona-Cowana dla podanych modułów."""
        self.module_names: list[str] = list(module_names)
        if len(set(self.module_names)) != len(self.module_names):
            raise ValueError("Nazwy modułów muszą być unikalne.")

        self.idx: dict[str, int] = {name: i for i, name in enumerate(self.module_names)}
        self.n: int = len(self.module_names)
        self.connectivity: np.ndarray = np.asarray(connectivity, dtype=float)
        expected_connectivity_shape = (self.n, self.n)
        if self.connectivity.shape != expected_connectivity_shape:
            raise ValueError(
                "Macierz connectivity ma niepoprawny kształt: "
                f"oczekiwano {expected_connectivity_shape}, "
                f"otrzymano {self.connectivity.shape}."
            )
        if not np.all(np.isfinite(self.connectivity)):
            raise ValueError(
                "Macierz connectivity musi zawierać wyłącznie skończone wartości."
            )

        self.band_map: dict[str, str] = band_map or DEFAULT_MODULE_BANDS
        self.params: WilsonCowanParams = params or WilsonCowanParams()

        self.module_bands: list[str] = [
            self.band_map.get(name, "beta") for name in self.module_names
        ]

        for band in self.module_bands:
            if band not in BAND_FREQUENCIES or band not in BAND_TIME_CONSTANTS:
                raise ValueError(
                    f"Nieznane pasmo {band!r}; nazwa musi występować w "
                    "BAND_FREQUENCIES i BAND_TIME_CONSTANTS."
                )

        self.frequency: np.ndarray = np.array(
            [BAND_FREQUENCIES[b] for b in self.module_bands], dtype=float
        )
        self.tau_e: np.ndarray = np.array(
            [BAND_TIME_CONSTANTS[b][0] for b in self.module_bands], dtype=float
        )
        self.tau_i: np.ndarray = np.array(
            [BAND_TIME_CONSTANTS[b][1] for b in self.module_bands], dtype=float
        )

    def initial_state(self, rng: np.random.Generator) -> np.ndarray:
        """Utwórz stan początkowy, używając jawnie przekazanego generatora RNG."""
        excitatory_noise = np.asarray(rng.normal(size=self.n), dtype=float)
        inhibitory_noise = np.asarray(rng.normal(size=self.n), dtype=float)
        phase = np.asarray(rng.uniform(0.0, 2.0 * np.pi, size=self.n), dtype=float)
        expected_shape = (self.n,)
        for name, values in (
            ("szum pobudzający", excitatory_noise),
            ("szum hamujący", inhibitory_noise),
            ("faza początkowa", phase),
        ):
            if values.shape != expected_shape:
                raise ValueError(
                    f"Dane „{name}” mają niepoprawny kształt: "
                    f"oczekiwano {expected_shape}, otrzymano {values.shape}."
                )
            if not np.all(np.isfinite(values)):
                raise ValueError(
                    f"Dane „{name}” muszą zawierać wyłącznie skończone wartości."
                )

        state = np.zeros((self.n, 3), dtype=float)
        state[:, 0] = 0.10 + 0.02 * excitatory_noise  # E
        state[:, 1] = 0.08 + 0.02 * inhibitory_noise  # I
        state[:, 2] = phase  # phi
        state[:, :2] = np.clip(state[:, :2], 0.0, 1.0)
        return state

    def step(
        self,
        state: np.ndarray,
        cognitive_activity: np.ndarray,
        dt: float,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
        """Wykonaj krok oscylatorów, używając jawnie przekazanego generatora RNG."""
        if not np.isscalar(dt) or not np.isfinite(dt) or dt <= 0:
            raise ValueError("Krok dt musi być skończoną liczbą większą od zera.")

        state = np.asarray(state, dtype=float)
        expected_state_shape = (self.n, 3)
        if state.shape != expected_state_shape:
            raise ValueError(
                f"Stan ma niepoprawny kształt: oczekiwano {expected_state_shape}, "
                f"otrzymano {state.shape}."
            )
        if not np.all(np.isfinite(state)):
            raise ValueError("Stan musi zawierać wyłącznie skończone wartości.")

        cognitive_activity = np.asarray(cognitive_activity, dtype=float)
        expected_activity_shape = (self.n,)
        if cognitive_activity.shape != expected_activity_shape:
            raise ValueError(
                "Aktywność poznawcza ma niepoprawny kształt: "
                f"oczekiwano {expected_activity_shape}, "
                f"otrzymano {cognitive_activity.shape}."
            )
        if not np.all(np.isfinite(cognitive_activity)):
            raise ValueError(
                "Aktywność poznawcza musi zawierać wyłącznie skończone wartości."
            )
        p = self.params

        excitatory_activity = state[:, 0]
        inhibitory_activity = state[:, 1]
        phi = state[:, 2]

        # Międzymodułowe sprzężenie oscylatorów wynika z macierzy funkcjonalnej W.
        # Używamy dodatniej części macierzy, aby uniknąć niestabilnego wzmacniania hamowania.
        positive_coupling = np.maximum(self.connectivity, 0.0)
        network_drive = positive_coupling @ excitatory_activity

        rhythmic_drive = p.phase_drive_gain * np.sin(phi)
        cognitive_drive = p.cognitive_drive_gain * cognitive_activity
        coupled_drive = p.coupling_gain * network_drive

        input_e = (
            p.w_ee * excitatory_activity
            - p.w_ei * inhibitory_activity
            + cognitive_drive
            + coupled_drive
            + rhythmic_drive
            + p.baseline_e
        )
        input_i = (
            p.w_ie * excitatory_activity
            - p.w_ii * inhibitory_activity
            + 0.45 * cognitive_drive
            + p.baseline_i
        )

        dE = (-excitatory_activity + sigmoid(input_e, beta=1.0)) / self.tau_e
        dI = (-inhibitory_activity + sigmoid(input_i, beta=1.0)) / self.tau_i

        E_next = (
            excitatory_activity
            + dt * dE
            + np.sqrt(dt) * p.oscillator_noise * rng.normal(size=self.n)
        )
        I_next = (
            inhibitory_activity
            + dt * dI
            + np.sqrt(dt) * p.oscillator_noise * rng.normal(size=self.n)
        )
        phi_next = phi + 2.0 * np.pi * self.frequency * dt

        next_state = np.empty_like(state)
        next_state[:, 0] = np.clip(E_next, 0.0, 1.0)
        next_state[:, 1] = np.clip(I_next, 0.0, 1.0)
        next_state[:, 2] = np.mod(phi_next, 2.0 * np.pi)

        eeg = next_state[:, 0] - next_state[:, 1]
        band_power = self.compute_band_power(eeg)

        return next_state, eeg, band_power

    def compute_band_power(self, eeg_vector: np.ndarray) -> dict[str, float]:
        """
        Chwilowa, uproszczona moc pasmowa: suma kwadratów sygnałów E-I
        w modułach przypisanych do danego pasma.
        """
        eeg_vector = np.asarray(eeg_vector, dtype=float)
        expected_shape = (self.n,)
        if eeg_vector.shape != expected_shape:
            raise ValueError(
                f"Wektor EEG ma niepoprawny kształt: oczekiwano {expected_shape}, "
                f"otrzymano {eeg_vector.shape}."
            )
        if not np.all(np.isfinite(eeg_vector)):
            raise ValueError("Wektor EEG musi zawierać wyłącznie skończone wartości.")

        out = {band: 0.0 for band in BAND_FREQUENCIES}
        for value, band in zip(eeg_vector, self.module_bands):
            out[band] += float(value * value)
        return out
