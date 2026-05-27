from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


def _to_jsonable(value: Any) -> Any:
    """Opis funkcji _to_jsonable."""
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def _git_commit_hash() -> str | None:
    """Opis funkcji _git_commit_hash."""
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL)
            .strip()
        )
    except Exception:
        return None


def build_output_dir(scenario: str, label: str | None = None, root: str | Path = "outputs") -> Path:
    """Opis funkcji build_output_dir."""
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
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
) -> dict[str, Any]:
    """Zapisuje wyniki symulacji i metadane do plików NPZ oraz JSON."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    npz_path = out / "run_data.npz"
    meta_path = out / "metadata.json"

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
        "saved_utc": datetime.utcnow().isoformat() + "Z",
        "seed": seed,
        "duration_s": duration_s,
        "git_commit": _git_commit_hash(),
        "model_params": _to_jsonable(model_params),
        "oscillator_params": _to_jsonable(oscillator_params),
        "scenario": _to_jsonable(scenario),
        "oscillator_config": {
            "module_bands": _to_jsonable(oscillations.get("module_bands")),
            "frequency": _to_jsonable(np.asarray(oscillations.get("frequency", [])).tolist()),
        },
    }
    if diagnostics_nested:
        metadata["diagnostics_nested"] = diagnostics_nested
    if model_params:
        for attr in ("semantic_rule", "value_rule", "connectivity_adaptation"):
            if hasattr(model_params, attr):
                metadata["model_params"][attr] = _to_jsonable(getattr(model_params, attr))
    if extra_metadata:
        metadata["extra"] = _to_jsonable(extra_metadata)

    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output_dir": str(out), "npz": str(npz_path), "metadata": str(meta_path)}


def load_run(output_dir: str | Path) -> dict:
    """Opis funkcji load_run."""
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
    oscillations["module_bands"] = metadata.get("oscillator_config", {}).get("module_bands", [])
    oscillations["frequency"] = np.asarray(metadata.get("oscillator_config", {}).get("frequency", []), dtype=float)

    return {
        "time": time,
        "activity": activity,
        "diagnostics": diagnostics,
        "oscillations": oscillations,
        "metadata": metadata,
        "path": str(out),
    }
