"""Ujednolicone raportowanie analizy i benchmarków."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json

import numpy as np

from .signal_metrics import band_powers, comparative_report, connectivity_matrix, phase_locking_value


@dataclass
class AnalysisReport:
    payload: dict

    def to_json(self) -> str:
        return json.dumps(self.payload, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        metrics = self.payload.get("metrics", {})
        compare = self.payload.get("comparison", {})
        lines = ["# Raport analizy", "", "## Metryki"]
        for name, value in metrics.items():
            lines.append(f"- **{name}**: {value}")
        lines.append("")
        lines.append("## Porównanie z benchmarkiem")
        for name, value in compare.items():
            lines.append(f"- **{name}**: {value}")
        return "\n".join(lines)

    def to_csv_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for section in ("metrics", "comparison"):
            for key, value in self.payload.get(section, {}).items():
                rows.append({"section": section, "metric": key, "value": str(value)})
        return rows


def write_report_files(report: AnalysisReport, output_dir: Path, stem: str = "analysis_report") -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    md_path = output_dir / f"{stem}.md"

    json_path.write_text(report.to_json(), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["section", "metric", "value"])
        writer.writeheader()
        writer.writerows(report.to_csv_rows())
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def build_analysis_report(
    eeg: np.ndarray,
    fmri: np.ndarray,
    behavior: np.ndarray,
    benchmark: dict[str, np.ndarray] | None = None,
    fs: float = 100.0,
) -> AnalysisReport:
    eeg = np.asarray(eeg, dtype=float)
    fmri = np.asarray(fmri, dtype=float)
    behavior = np.asarray(behavior, dtype=float)

    if eeg.size == 0 or fmri.size == 0 or behavior.size == 0:
        raise ValueError("Sygnały wejściowe do raportu analizy nie mogą być puste.")

    primary = eeg[:, 0] if eeg.ndim == 2 else eeg
    secondary = eeg[:, 1] if eeg.ndim == 2 and eeg.shape[1] > 1 else primary

    bands = band_powers(primary, fs)
    erp_proxy = float(np.max(primary) - np.min(primary))
    plv = phase_locking_value(primary, secondary)
    conn = connectivity_matrix(eeg if eeg.ndim == 2 else np.column_stack([primary, secondary]))

    beh_mean = float(np.mean(behavior))
    beh_std = float(np.std(behavior))

    metrics = {
        "band_power_alpha": float(bands.get("alpha", 0.0)),
        "band_power_beta": float(bands.get("beta", 0.0)),
        "erp_proxy_peak_to_peak": erp_proxy,
        "phase_locking_value": float(plv),
        "connectivity_mean": float(np.mean(conn)),
        "connectivity_abs_mean": float(np.mean(np.abs(conn))),
        "behavior_mean": beh_mean,
        "behavior_std": beh_std,
        "fmri_mean": float(np.mean(fmri)),
    }

    comparison: dict[str, float] = {}
    if benchmark:
        if "eeg" in benchmark:
            comparison.update({f"eeg_{k}": v for k, v in comparative_report(eeg, benchmark["eeg"]).items()})
        if "fmri" in benchmark:
            comparison.update({f"fmri_{k}": v for k, v in comparative_report(fmri, benchmark["fmri"]).items()})
        if "behavior" in benchmark:
            comparison.update({f"behavior_{k}": v for k, v in comparative_report(behavior, benchmark["behavior"]).items()})

    return AnalysisReport(payload={"metrics": metrics, "comparison": comparison})
