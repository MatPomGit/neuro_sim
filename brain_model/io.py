from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

import numpy as np

REPRODUCIBILITY_ARTIFACTS = (
    "config.json",
    "metrics.json",
    "environment.json",
    "git_info.json",
    "run.log",
    "metadata.json",
    "run_data.npz",
    "event_timeline.json",
)
KEY_DEPENDENCIES = ("numpy", "matplotlib", "PyYAML", "PySide6")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _to_jsonable(value: Any) -> Any:
    """Przekształć wartości projektu do struktur możliwych do zapisu w JSON.

    Parameters
    ----------
    value:
        Dowolna wartość metadanych, konfiguracji albo wyniku symulacji.

    Returns
    -------
    Any
        Wartość złożona wyłącznie z typów obsługiwanych przez ``json.dumps``.
    """
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def _run_git_command(args: list[str], *, repo_path: Path | None = None) -> str | None:
    """Uruchamia bezpieczne polecenie Git i zwraca tekst wyniku.

    Parameters
    ----------
    args:
        Argumenty polecenia `git` bez nazwy programu.
    repo_path:
        Opcjonalna ścieżka katalogu repozytorium.

    Returns
    -------
    str | None
        Przycięty wynik standardowego wyjścia albo `None`, gdy Git nie jest
        dostępny lub katalog nie jest repozytorium.
    """
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_path,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _git_commit_hash() -> str | None:
    """Zwróć hash bieżącego commita repozytorium projektu.

    Returns
    -------
    str | None
        Pełny hash commita Git albo ``None``, gdy katalog projektu nie jest
        dostępny jako repozytorium Git.
    """
    return _run_git_command(["rev-parse", "HEAD"], repo_path=REPO_ROOT)


def collect_git_info(
    repo_path: str | Path | None = None,
) -> dict[str, str | bool | None]:
    """Zbiera minimalne informacje Git wymagane do reprodukcji wyniku.

    Parameters
    ----------
    repo_path:
        Opcjonalna ścieżka katalogu repozytorium. Gdy nie podano, używany jest
        bieżący katalog procesu.

    Returns
    -------
    dict[str, str | bool | None]
        Słownik z hashem commita, nazwą gałęzi i informacją, czy repozytorium
        miało niezacommitowane zmiany.
    """
    path = Path(repo_path) if repo_path is not None else None
    status = _run_git_command(["status", "--porcelain"], repo_path=path)
    return {
        "commit": _run_git_command(["rev-parse", "HEAD"], repo_path=path),
        "branch": _run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"], repo_path=path
        ),
        "is_dirty": None if status is None else bool(status),
    }


def collect_environment_info(
    dependencies: tuple[str, ...] = KEY_DEPENDENCIES,
) -> dict[str, Any]:
    """Zbiera wersję Pythona, platformę i kluczowe zależności.

    Parameters
    ----------
    dependencies:
        Nazwy dystrybucji Pythona, których wersje mają być zapisane w
        artefakcie reprodukcji.

    Returns
    -------
    dict[str, Any]
        Informacje o środowisku uruchomieniowym w formacie gotowym do JSON.
    """
    dependency_versions: dict[str, str | None] = {}
    for dependency_name in dependencies:
        try:
            dependency_versions[dependency_name] = importlib_metadata.version(
                dependency_name
            )
        except importlib_metadata.PackageNotFoundError:
            dependency_versions[dependency_name] = None

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "dependencies": dependency_versions,
    }


def _write_json(path: Path, payload: Any) -> None:
    """Zapisuje obiekt do pliku JSON w czytelnym i deterministycznym formacie."""
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_run_log(
    path: Path,
    *,
    seed: int | None,
    duration_s: float | None,
    artifact_paths: dict[str, str],
) -> None:
    """Zapisuje krótki dziennik uruchomienia do katalogu wynikowego."""
    lines = [
        f"Zapis wyników neuro-sim: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"Ziarno losowości: {seed if seed is not None else 'n/a'}",
        f"Czas wykonania symulacji [s]: {duration_s if duration_s is not None else 'n/a'}",
        "Artefakty:",
    ]
    lines.extend(
        f"- {name}: {artifact_path}" for name, artifact_path in artifact_paths.items()
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_output_dir(
    scenario: str, label: str | None = None, root: str | Path = "outputs"
) -> Path:
    """Utwórz jednoznaczny katalog wyników dla uruchomienia symulacji.

    Parameters
    ----------
    scenario:
        Techniczna nazwa scenariusza, używana w nazwie katalogu.
    label:
        Opcjonalna etykieta uruchomienia odróżniająca powtórzenia scenariusza.
    root:
        Katalog bazowy, w którym zostanie utworzony katalog wynikowy.

    Returns
    -------
    Path
        Ścieżka istniejącego katalogu wynikowego z prefiksem czasu UTC.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_scenario = (scenario or "scenario").replace("/", "-").replace(" ", "-")
    safe_label = (label or "run").replace("/", "-").replace(" ", "-")
    out_dir = Path(root) / f"{stamp}_{safe_scenario}_{safe_label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def save_run(
    output_dir: str | Path,
    time: np.ndarray,
    activity: np.ndarray,
    diagnostics: dict[str, Any],
    oscillations: dict[str, Any],
    *,
    model_params: Any = None,
    oscillator_params: Any = None,
    scenario: dict[str, Any] | None = None,
    seed: int | None = None,
    duration_s: float | None = None,
    extra_metadata: dict[str, Any] | None = None,
    config: Any = None,
    metrics: dict[str, Any] | None = None,
    event_timeline: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Zapisz wyniki symulacji i artefakty reprodukowalności.

    Parameters
    ----------
    output_dir:
        Katalog docelowy dla plików uruchomienia.
    time:
        Wektor czasu symulacji.
    activity:
        Macierz aktywności modułów modelu.
    diagnostics:
        Diagnostyki numeryczne lub zagnieżdżone metadane diagnostyczne.
    oscillations:
        Sygnały oscylacyjne i konfiguracja pasm.
    model_params:
        Parametry modelu zapisywane w metadanych.
    oscillator_params:
        Parametry oscylatorów zapisywane w metadanych.
    scenario:
        Metadane scenariusza symulacji.
    seed:
        Ziarno losowości użyte w uruchomieniu.
    duration_s:
        Czas wykonania symulacji w sekundach.
    extra_metadata:
        Dodatkowe metadane specyficzne dla wywołującego kodu.
    config:
        Konfiguracja uruchomienia zapisywana jako ``config.json``.
    metrics:
        Metryki uruchomienia zapisywane jako ``metrics.json``.
    event_timeline:
        Oś czasu zdarzeń. Gdy ``None``, zapisywana jest pusta lista.

    Returns
    -------
    dict[str, Any]
        Ścieżki do zapisanych artefaktów reprodukowalności.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    npz_path = out / "run_data.npz"
    meta_path = out / "metadata.json"
    config_path = out / "config.json"
    metrics_path = out / "metrics.json"
    environment_path = out / "environment.json"
    git_info_path = out / "git_info.json"
    run_log_path = out / "run.log"
    event_timeline_path = out / "event_timeline.json"

    arrays = {
        "time": np.asarray(time),
        "activity": np.asarray(activity),
        "osc_eeg": np.asarray(oscillations.get("eeg", [])),
        "osc_exc": np.asarray(oscillations.get("excitatory", [])),
        "osc_inh": np.asarray(oscillations.get("inhibitory", [])),
    }
    diagnostics_nested = {}
    for key, val in diagnostics.items():
        if isinstance(val, dict):
            diagnostics_nested[key] = _to_jsonable(val)
            continue
        arrays[f"diag_{key}"] = np.asarray(val)
    for band, val in oscillations.get("band_power", {}).items():
        arrays[f"band_{band}"] = np.asarray(val)

    np.savez_compressed(npz_path, **arrays)

    metadata = {
        "format": "neuro-sim-run-v1",
        "saved_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "seed": seed,
        "duration_s": duration_s,
        "git_commit": _git_commit_hash(),
        "model_params": _to_jsonable(model_params),
        "oscillator_params": _to_jsonable(oscillator_params),
        "scenario": _to_jsonable(scenario),
        "oscillator_config": {
            "module_bands": _to_jsonable(oscillations.get("module_bands")),
            "frequency": _to_jsonable(
                np.asarray(oscillations.get("frequency", [])).tolist()
            ),
        },
    }
    if diagnostics_nested:
        metadata["diagnostics_nested"] = diagnostics_nested
    if model_params:
        for attr in ("semantic_rule", "value_rule", "connectivity_adaptation"):
            if hasattr(model_params, attr):
                metadata["model_params"][attr] = _to_jsonable(
                    getattr(model_params, attr)
                )
    if extra_metadata:
        metadata["extra"] = _to_jsonable(extra_metadata)

    artifact_paths = {
        "run_data.npz": str(npz_path),
        "metadata.json": str(meta_path),
        "config.json": str(config_path),
        "metrics.json": str(metrics_path),
        "environment.json": str(environment_path),
        "git_info.json": str(git_info_path),
        "run.log": str(run_log_path),
        "event_timeline.json": str(event_timeline_path),
    }
    _write_json(meta_path, metadata)
    _write_json(config_path, config if config is not None else {})
    _write_json(metrics_path, metrics if metrics is not None else {})
    _write_json(environment_path, collect_environment_info())
    _write_json(git_info_path, collect_git_info(REPO_ROOT))
    _write_json(
        event_timeline_path, event_timeline if event_timeline is not None else []
    )
    _write_run_log(
        run_log_path,
        seed=seed,
        duration_s=duration_s,
        artifact_paths=artifact_paths,
    )

    return {
        "output_dir": str(out),
        "npz": str(npz_path),
        "metadata": str(meta_path),
        "config": str(config_path),
        "metrics": str(metrics_path),
        "environment": str(environment_path),
        "git_info": str(git_info_path),
        "run_log": str(run_log_path),
        "event_timeline": str(event_timeline_path),
    }


def load_run(output_dir: str | Path) -> dict[str, Any]:
    """Wczytaj zapisane wyniki symulacji z katalogu artefaktów.

    Parameters
    ----------
    output_dir:
        Katalog zawierający ``run_data.npz`` i ``metadata.json`` utworzone przez
        ``save_run``.

    Returns
    -------
    dict[str, Any]
        Dane czasu, aktywności, diagnostyk, oscylacji, metadanych oraz ścieżka
        katalogu uruchomienia.

    Raises
    ------
    FileNotFoundError
        Gdy wymagane artefakty nie istnieją w katalogu wynikowym.
    """
    out = Path(output_dir)
    npz_path = out / "run_data.npz"
    meta_path = out / "metadata.json"

    with np.load(npz_path, allow_pickle=False) as data:
        time = data["time"]
        activity = data["activity"]

        diagnostics = {
            key.removeprefix("diag_"): data[key]
            for key in data.files
            if key.startswith("diag_")
        }
        band_power = {
            key.removeprefix("band_"): data[key]
            for key in data.files
            if key.startswith("band_")
        }

        oscillations = {
            "eeg": data["osc_eeg"] if "osc_eeg" in data else np.array([]),
            "excitatory": data["osc_exc"] if "osc_exc" in data else np.array([]),
            "inhibitory": data["osc_inh"] if "osc_inh" in data else np.array([]),
            "band_power": band_power,
        }

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    diagnostics.update(metadata.get("diagnostics_nested", {}))
    oscillations["module_bands"] = metadata.get("oscillator_config", {}).get(
        "module_bands", []
    )
    oscillations["frequency"] = np.asarray(
        metadata.get("oscillator_config", {}).get("frequency", []), dtype=float
    )

    return {
        "time": time,
        "activity": activity,
        "diagnostics": diagnostics,
        "oscillations": oscillations,
        "metadata": metadata,
        "path": str(out),
    }
