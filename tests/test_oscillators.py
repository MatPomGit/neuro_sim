import numpy as np
import pytest

from brain_model.oscillators import WilsonCowanOscillatorBank


def create_oscillator_bank() -> WilsonCowanOscillatorBank:
    """Utwórz mały bank oscylatorów do testów walidacji."""
    return WilsonCowanOscillatorBank(
        module_names=["VIS", "EXEC"],
        connectivity=np.array([[0.0, 0.2], [0.1, 0.0]]),
    )


def test_oscillator_bank_accepts_valid_inputs() -> None:
    """Poprawne dane powinny umożliwić inicjalizację, krok i obliczenie mocy."""
    bank = create_oscillator_bank()
    rng = np.random.default_rng(42)

    state = bank.initial_state(rng)
    next_state, eeg, band_power = bank.step(
        state=state,
        cognitive_activity=np.array([0.2, 0.4]),
        dt=0.001,
        rng=rng,
    )

    assert next_state.shape == (2, 3)
    assert eeg.shape == (2,)
    assert set(band_power) == {"theta", "alpha", "beta", "gamma"}
    assert bank.compute_band_power(np.array([1.0, 2.0]))["beta"] == pytest.approx(4.0)


class InvalidRandomGenerator:
    """Generator zwracający dane o błędnym kształcie lub wartości nieskończone."""

    def __init__(self, normal_values: np.ndarray) -> None:
        """Zapisz wartości zwracane przez metodę normal."""
        self.normal_values = normal_values

    def normal(self, size: int) -> np.ndarray:
        """Zwróć przygotowane wartości niezależnie od żądanego rozmiaru."""
        return self.normal_values

    def uniform(self, low: float, high: float, size: int) -> np.ndarray:
        """Zwróć poprawny wektor faz."""
        return np.zeros(size)


@pytest.mark.parametrize(
    ("normal_values", "message"),
    [
        (np.zeros((2, 1)), r"oczekiwano \(2,\), otrzymano \(2, 1\)"),
        (np.array([0.0, np.inf]), "muszą zawierać wyłącznie skończone wartości"),
    ],
)
def test_initial_state_rejects_invalid_rng_output(
    normal_values: np.ndarray, message: str
) -> None:
    """Stan początkowy powinien odrzucać wadliwe dane generatora losowego."""
    bank = create_oscillator_bank()

    with pytest.raises(ValueError, match=message):
        bank.initial_state(InvalidRandomGenerator(normal_values))


@pytest.mark.parametrize(
    ("module_names", "connectivity", "band_map", "message"),
    [
        (
            ["VIS", "VIS"],
            np.zeros((2, 2)),
            None,
            "Nazwy modułów muszą być unikalne",
        ),
        (
            ["VIS", "EXEC"],
            np.zeros((2, 3)),
            None,
            r"oczekiwano \(2, 2\), otrzymano \(2, 3\)",
        ),
        (
            ["VIS", "EXEC"],
            np.array([[0.0, np.inf], [0.0, 0.0]]),
            None,
            "skończone wartości",
        ),
        (
            ["VIS", "EXEC"],
            np.zeros((2, 2)),
            {"VIS": "delta", "EXEC": "beta"},
            "Nieznane pasmo 'delta'",
        ),
    ],
)
def test_oscillator_bank_rejects_invalid_configuration(
    module_names: list[str],
    connectivity: np.ndarray,
    band_map: dict[str, str] | None,
    message: str,
) -> None:
    """Konstruktor powinien odrzucać niespójną konfigurację banku."""
    with pytest.raises(ValueError, match=message):
        WilsonCowanOscillatorBank(module_names, connectivity, band_map=band_map)


@pytest.mark.parametrize(
    ("state", "cognitive_activity", "dt", "message"),
    [
        (
            np.zeros((2, 2)),
            np.zeros(2),
            0.001,
            r"oczekiwano \(2, 3\), otrzymano \(2, 2\)",
        ),
        (
            np.full((2, 3), np.nan),
            np.zeros(2),
            0.001,
            "Stan musi zawierać wyłącznie skończone wartości",
        ),
        (
            np.zeros((2, 3)),
            np.zeros((2, 1)),
            0.001,
            r"oczekiwano \(2,\), otrzymano \(2, 1\)",
        ),
        (
            np.zeros((2, 3)),
            np.array([0.0, np.inf]),
            0.001,
            "Aktywność poznawcza musi zawierać wyłącznie skończone wartości",
        ),
        (np.zeros((2, 3)), np.zeros(2), 0.0, "Krok dt"),
    ],
)
def test_step_rejects_invalid_inputs(
    state: np.ndarray,
    cognitive_activity: np.ndarray,
    dt: float,
    message: str,
) -> None:
    """Krok symulacji powinien jawnie odrzucać błędne dane i broadcasting."""
    bank = create_oscillator_bank()

    with pytest.raises(ValueError, match=message):
        bank.step(state, cognitive_activity, dt)


@pytest.mark.parametrize(
    ("eeg_vector", "message"),
    [
        (np.zeros(3), r"oczekiwano \(2,\), otrzymano \(3,\)"),
        (
            np.array([0.0, np.nan]),
            "Wektor EEG musi zawierać wyłącznie skończone wartości",
        ),
    ],
)
def test_compute_band_power_rejects_invalid_vector(
    eeg_vector: np.ndarray, message: str
) -> None:
    """Obliczanie mocy powinno wymagać skończonego wektora długości n."""
    bank = create_oscillator_bank()

    with pytest.raises(ValueError, match=message):
        bank.compute_band_power(eeg_vector)
