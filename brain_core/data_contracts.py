"""Szybkie walidatory kontraktów danych opisanych w ``docs/data_contracts.md``."""

from __future__ import annotations

from typing import Any

import numpy as np

from brain_core.anatomy.connectome import Connectome
from brain_core.anatomy.regions import RegionAtlas

CONTRACT_A_ANATOMY_NETWORKS = "Kontrakt A: `anatomy` → `networks`"
CONTRACT_B_NETWORKS_POPULATIONS = "Kontrakt B: `networks` → `populations`"
CONTRACT_D_POPULATIONS_PHYSIOLOGY = "Kontrakt D: `populations` → `physiology`"


def _contract_error(contract_name: str, message: str) -> ValueError:
    """Buduje błąd zawierający nazwę kontraktu z dokumentacji danych."""
    return ValueError(f"{contract_name}: {message}")


def _as_float_array(value: Any, field_name: str, contract_name: str) -> np.ndarray:
    """Konwertuje wejście na tablicę ``float`` z czytelnym błędem kontraktu."""
    try:
        return np.asarray(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise _contract_error(
            contract_name, f"{field_name} musi być tablicą numeryczną."
        ) from error


def validate_region_atlas_contract(atlas: RegionAtlas) -> None:
    """Waliduje kształty i jednostki atlasu regionów z kontraktu A.

    Parameters
    ----------
    atlas:
        Atlas regionów z nazwami i stałymi czasowymi ``tau`` w sekundach [s].

    Raises:
    ------
    ValueError
        Gdy atlas nie spełnia kontraktu A z ``docs/data_contracts.md``.
    """
    regions = tuple(atlas.regions)
    if not regions:
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS, "atlas.names nie może być pusty."
        )

    names = tuple(region.name for region in regions)
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            "atlas.names musi zawierać wyłącznie niepuste nazwy regionów.",
        )
    if len(set(names)) != len(names):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS, "atlas.names musi być unikalne."
        )

    tau_values = np.asarray([region.tau for region in regions], dtype=float)
    if not np.all(np.isfinite(tau_values)) or np.any(tau_values <= 0.0):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            "region.tau musi zawierać dodatnie skończone wartości w sekundach [s].",
        )


def validate_connectome_contract(
    connectome: Connectome, expected_region_names: tuple[str, ...] | None = None
) -> None:
    """Waliduje kształty macierzy i jednostki konektomu z kontraktu A.

    Parameters
    ----------
    connectome:
        Konektom z nazwami regionów, macierzą wag i długościami włókien [mm].
    expected_region_names:
        Opcjonalna kolejność regionów wymagana przez atlas wejściowy.

    Raises:
    ------
    ValueError
        Gdy konektom nie spełnia kontraktu A z ``docs/data_contracts.md``.
    """
    region_names = tuple(connectome.region_names)
    if expected_region_names is not None and region_names != tuple(
        expected_region_names
    ):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            "connectome.region_names musi być identyczne z atlas.names.",
        )
    if not region_names:
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS, "connectome.region_names nie może być puste."
        )
    if len(set(region_names)) != len(region_names):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS, "connectome.region_names musi być unikalne."
        )

    weights = _as_float_array(
        connectome.weights, "connectome.weights", CONTRACT_A_ANATOMY_NETWORKS
    )
    fiber_lengths = _as_float_array(
        connectome.fiber_lengths,
        "connectome.fiber_lengths",
        CONTRACT_A_ANATOMY_NETWORKS,
    )
    expected_shape = (len(region_names), len(region_names))
    if weights.shape != expected_shape:
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            f"connectome.weights musi mieć kształt {expected_shape}.",
        )
    if fiber_lengths.shape != weights.shape:
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            "connectome.fiber_lengths musi mieć kształt zgodny z connectome.weights.",
        )
    if not np.all(np.isfinite(weights)):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            "connectome.weights musi zawierać wartości skończone.",
        )
    if not np.all(np.isfinite(fiber_lengths)) or np.any(fiber_lengths < 0.0):
        raise _contract_error(
            CONTRACT_A_ANATOMY_NETWORKS,
            "connectome.fiber_lengths musi zawierać skończone wartości nieujemne [mm].",
        )


def validate_square_matrix_contract(
    matrix: Any, n_regions: int, field_name: str, contract_name: str
) -> np.ndarray:
    """Waliduje skończoną macierz kwadratową ``[n_regions, n_regions]``.

    Parameters
    ----------
    matrix:
        Dane macierzy do konwersji na ``numpy.ndarray``.
    n_regions:
        Liczba regionów oczekiwana w obu wymiarach macierzy.
    field_name:
        Nazwa pola używana w raporcie błędu.
    contract_name:
        Nazwa kontraktu z ``docs/data_contracts.md``.

    Returns:
    -------
    np.ndarray
        Macierz ``float`` spełniająca kontrakt kształtu i skończoności.

    Raises:
    ------
    ValueError
        Gdy macierz ma zły kształt lub wartości nienumeryczne/nieskończone.
    """
    if n_regions <= 0:
        raise _contract_error(contract_name, "n_regions musi być > 0.")
    arr = _as_float_array(matrix, field_name, contract_name)
    expected_shape = (n_regions, n_regions)
    if arr.shape != expected_shape:
        raise _contract_error(
            contract_name, f"{field_name} musi mieć kształt {expected_shape}."
        )
    if not np.all(np.isfinite(arr)):
        raise _contract_error(
            contract_name, f"{field_name} musi zawierać wartości skończone."
        )
    return arr


def validate_delay_steps_contract(delays_steps: Any, n_regions: int) -> np.ndarray:
    """Waliduje macierz opóźnień przewodzenia z kontraktu B.

    Parameters
    ----------
    delays_steps:
        Macierz opóźnień w krokach integratora ``[n_regions, n_regions]``.
    n_regions:
        Liczba regionów w sieci.

    Returns:
    -------
    np.ndarray
        Macierz opóźnień typu ``int``.

    Raises:
    ------
    ValueError
        Gdy opóźnienia mają zły kształt albo nieujemną całkowitość.
    """
    delays = validate_square_matrix_contract(
        delays_steps, n_regions, "delays_steps", CONTRACT_B_NETWORKS_POPULATIONS
    )
    if not np.all(np.equal(delays, np.floor(delays))):
        raise _contract_error(
            CONTRACT_B_NETWORKS_POPULATIONS,
            "delays_steps musi zawierać całkowite liczby kroków integratora.",
        )
    if np.any(delays < 0.0):
        raise _contract_error(
            CONTRACT_B_NETWORKS_POPULATIONS,
            "delays_steps musi zawierać wartości nieujemne.",
        )
    return delays.astype(int)


def validate_regional_vector_contract(
    signal: Any, n_regions: int, field_name: str = "delayed_activity"
) -> np.ndarray:
    """Waliduje regionalny wektor aktywności proxy z kontraktu B.

    Parameters
    ----------
    signal:
        Wektor aktywności regionów ``[n_regions]``.
    n_regions:
        Liczba regionów w sieci.
    field_name:
        Nazwa pola raportowana w błędzie.

    Returns:
    -------
    np.ndarray
        Wektor ``float`` spełniający kontrakt.

    Raises:
    ------
    ValueError
        Gdy wektor ma zły kształt lub wartości nieskończone.
    """
    if n_regions <= 0:
        raise _contract_error(
            CONTRACT_B_NETWORKS_POPULATIONS, "n_regions musi być > 0."
        )
    arr = _as_float_array(signal, field_name, CONTRACT_B_NETWORKS_POPULATIONS)
    expected_shape = (n_regions,)
    if arr.shape != expected_shape:
        raise _contract_error(
            CONTRACT_B_NETWORKS_POPULATIONS,
            f"{field_name} musi mieć kształt {expected_shape}.",
        )
    if not np.all(np.isfinite(arr)):
        raise _contract_error(
            CONTRACT_B_NETWORKS_POPULATIONS,
            f"{field_name} musi zawierać wartości skończone.",
        )
    return arr


def validate_leadfield_contract(leadfield: Any) -> np.ndarray:
    """Waliduje macierz leadfield EEG z kontraktu D.

    Parameters
    ----------
    leadfield:
        Macierz operatora forward EEG ``[n_sensors, n_sources]``.

    Returns:
    -------
    np.ndarray
        Macierz ``float`` spełniająca kontrakt.

    Raises:
    ------
    ValueError
        Gdy macierz jest pusta, nie-2D albo nieskończona.
    """
    arr = _as_float_array(leadfield, "leadfield", CONTRACT_D_POPULATIONS_PHYSIOLOGY)
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] == 0:
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "leadfield musi być niepustą macierzą 2D [n_sensors, n_sources].",
        )
    if not np.all(np.isfinite(arr)):
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "leadfield musi zawierać wartości skończone.",
        )
    return arr


def validate_source_activity_contract(
    source_activity: Any, n_sources: int
) -> np.ndarray:
    """Waliduje aktywność źródłową EEG z kontraktu D.

    Parameters
    ----------
    source_activity:
        Aktywność ``[n_sources]`` albo ``[n_samples, n_sources]`` w jednostkach proxy.
    n_sources:
        Liczba źródeł wymagana przez leadfield.

    Returns:
    -------
    np.ndarray
        Tablica aktywności źródłowej ``float``.

    Raises:
    ------
    ValueError
        Gdy kształt nie odpowiada liczbie źródeł albo wartości nie są skończone.
    """
    arr = _as_float_array(
        source_activity, "source_activity", CONTRACT_D_POPULATIONS_PHYSIOLOGY
    )
    if arr.ndim == 1:
        valid_shape = arr.shape == (n_sources,)
    elif arr.ndim == 2:
        valid_shape = arr.shape[0] > 0 and arr.shape[1] == n_sources
    else:
        valid_shape = False
    if not valid_shape:
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "source_activity musi mieć kształt [n_sources] albo [n_samples, n_sources].",
        )
    if not np.all(np.isfinite(arr)):
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "source_activity musi zawierać wartości skończone.",
        )
    return arr


def validate_eeg_signal_contract(eeg: Any, n_sensors: int) -> np.ndarray:
    """Waliduje syntetyczny sygnał EEG proxy z kontraktu D.

    Parameters
    ----------
    eeg:
        Sygnał ``[n_sensors]`` albo ``[n_samples, n_sensors]``.
    n_sensors:
        Liczba sensorów oczekiwana przez operator odwrotny.

    Returns:
    -------
    np.ndarray
        Sygnał ``float`` spełniający kontrakt.

    Raises:
    ------
    ValueError
        Gdy kształt nie odpowiada liczbie sensorów albo wartości nie są skończone.
    """
    arr = _as_float_array(eeg, "eeg", CONTRACT_D_POPULATIONS_PHYSIOLOGY)
    if arr.ndim == 1:
        valid_shape = arr.shape == (n_sensors,)
    elif arr.ndim == 2:
        valid_shape = arr.shape[0] > 0 and arr.shape[1] == n_sensors
    else:
        valid_shape = False
    if not valid_shape:
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "eeg musi mieć kształt [n_sensors] albo [n_samples, n_sensors].",
        )
    if not np.all(np.isfinite(arr)):
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY, "eeg musi być skończone."
        )
    return arr


def validate_hrf_contract(hrf: Any) -> np.ndarray:
    """Waliduje wektor HRF z kontraktu D.

    Parameters
    ----------
    hrf:
        Bezwymiarowy wektor odpowiedzi hemodynamicznej ``[length]``.

    Returns:
    -------
    np.ndarray
        Wektor HRF ``float``.

    Raises:
    ------
    ValueError
        Gdy HRF nie jest niepustym, skończonym wektorem 1D.
    """
    arr = _as_float_array(hrf, "hrf", CONTRACT_D_POPULATIONS_PHYSIOLOGY)
    if arr.ndim != 1 or arr.shape[0] == 0:
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "hrf musi być niepustym wektorem [length].",
        )
    if not np.all(np.isfinite(arr)):
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY, "hrf musi być skończone."
        )
    return arr


def validate_bold_drive_contract(neural_drive: Any) -> np.ndarray:
    """Waliduje nieujemny napęd BOLD proxy z kontraktu D.

    Parameters
    ----------
    neural_drive:
        Napęd ``[n_samples]`` albo ``[n_samples, n_regions]``.

    Returns:
    -------
    np.ndarray
        Tablica napędu BOLD ``float``.

    Raises:
    ------
    ValueError
        Gdy napęd ma zły kształt, wartości nieskończone lub ujemne.
    """
    arr = _as_float_array(
        neural_drive, "neural_drive", CONTRACT_D_POPULATIONS_PHYSIOLOGY
    )
    valid_shape = (arr.ndim == 1 and arr.shape[0] > 0) or (
        arr.ndim == 2 and arr.shape[0] > 0 and arr.shape[1] > 0
    )
    if not valid_shape:
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "neural_drive musi mieć kształt [n_samples] albo [n_samples, n_regions].",
        )
    if not np.all(np.isfinite(arr)) or np.any(arr < 0.0):
        raise _contract_error(
            CONTRACT_D_POPULATIONS_PHYSIOLOGY,
            "neural_drive musi zawierać skończone wartości nieujemne.",
        )
    return arr
