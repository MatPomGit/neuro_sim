"""Ujednolicone raportowanie analizy i benchmarków."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .connectivity import compute_connectivity
from .information_flow import compute_information_flow
from .phase_locking import compute_phase_locking
from .signal_metrics import comparative_report
from .spectral import compute_band_powers


@dataclass
class AnalysisReport:
    """
    Klasa reprezentująca raport z analizy sygnałów i porównania z benchmarkiem.

    Attributes:
        payload (dict): Słownik z metrykami i porównaniami.
    """

    payload: dict

    def to_json(self) -> str:
        """
        Zwraca raport w formacie JSON.
        Returns:
            str: Raport jako tekst JSON.
        """
        return json.dumps(self.payload, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """
        Zwraca raport w formacie Markdown.
        Returns:
            str: Raport jako tekst Markdown.
        """
        metrics = self.payload.get("metrics", {})
        compare = self.payload.get("comparison", {})
        lines = ["# Raport analizy", "", "## Metryki"]
        for name, value in metrics.items():
            lines.append(f"- **{name}**: {value}")
        lines.append("")
        lines.append("## Porównanie z benchmarkiem")
        for name, value in compare.items():
            lines.append(f"- **{name}**: {value}")

        task_activation = self.payload.get("task_activation")
        if task_activation:
            lines.extend(["", "## Regiony i funkcje pobudzone przez task"])
            lines.append(f"- **task**: {task_activation.get('task_name', 'n/a')}")
            functions = ", ".join(task_activation.get("functions", []))
            regions = ", ".join(task_activation.get("regions", []))
            lines.append(f"- **funkcje**: {functions}")
            lines.append(f"- **regiony**: {regions}")
            for region, value in task_activation.get("mean_regional_input", {}).items():
                lines.append(f"- **średnie wejście {region}**: {value}")

        clinical_differences = self.payload.get("clinical_differences", [])
        if clinical_differences:
            lines.extend(["", "## Raport różnic profili klinicznych"])
            for item in clinical_differences:
                lines.append(f"- **profil**: {item.get('profile_id', 'n/a')}")
                lines.append(f"  - **region**: {item.get('region', 'n/a')}")
                lines.append(f"  - **czas_s**: {item.get('time_s', 'n/a')}")
                lines.append(
                    f"  - **funkcja poznawcza**: "
                    f"{item.get('cognitive_function', 'n/a')}"
                )
                lines.append(f"  - **mechanizm**: {item.get('mechanism', 'n/a')}")
                lines.append(
                    f"  - **średnia różnica bezwzględna**: "
                    f"{item.get('mean_abs_difference', 'n/a')}"
                )
        return "\n".join(lines)

    def to_csv_rows(self) -> list[dict[str, str]]:
        """
        Zwraca raport jako listę wierszy do CSV.
        Returns:
            list[dict[str, str]]: Lista słowników z sekcją, metryką i wartością.
        """
        rows: list[dict[str, str]] = []
        for section in ("metrics", "comparison"):
            for key, value in self.payload.get(section, {}).items():
                rows.append({"section": section, "metric": key, "value": str(value)})
        task_activation = self.payload.get("task_activation")
        if task_activation:
            rows.append(
                {
                    "section": "task_activation",
                    "metric": "functions",
                    "value": ", ".join(task_activation.get("functions", [])),
                }
            )
            rows.append(
                {
                    "section": "task_activation",
                    "metric": "regions",
                    "value": ", ".join(task_activation.get("regions", [])),
                }
            )
            for region, value in task_activation.get("mean_regional_input", {}).items():
                rows.append(
                    {
                        "section": "task_activation",
                        "metric": f"mean_regional_input_{region}",
                        "value": str(value),
                    }
                )

        for item in self.payload.get("clinical_differences", []):
            profile_id = item.get("profile_id", "n/a")
            for metric in (
                "region",
                "time_s",
                "cognitive_function",
                "mechanism",
                "mean_abs_difference",
            ):
                rows.append(
                    {
                        "section": "clinical_differences",
                        "metric": f"{profile_id}_{metric}",
                        "value": str(item.get(metric, "n/a")),
                    }
                )
        return rows


def write_report_files(
    report: AnalysisReport, output_dir: Path, stem: str = "analysis_report"
) -> dict[str, str]:
    """
    Zapisuje raport do plików JSON, CSV i Markdown.

    Args:
        report (AnalysisReport): Raport do zapisania.
        output_dir (Path): Katalog wyjściowy.
        stem (str): Nazwa bazowa plików.

    Returns:
        dict[str, str]: Słownik ze ścieżkami do plików.
    """
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
    analysis_set: list[str] | None = None,
) -> AnalysisReport:
    """
    Buduje raport analizy sygnałów EEG, fMRI i zachowania oraz porównania z benchmarkiem.

    Args:
        eeg (np.ndarray): Sygnały EEG.
        fmri (np.ndarray): Sygnały fMRI.
        behavior (np.ndarray): Dane behawioralne.
        benchmark (dict[str, np.ndarray] | None): Słownik z benchmarkami.
        fs (float): Częstotliwość próbkowania.
        analysis_set (list[str] | None): Lista analiz do wykonania.

    Returns:
        AnalysisReport: Raport z metrykami i porównaniami.

    Raises:
        ValueError: Jeśli sygnały wejściowe są puste.
    """
    eeg = np.asarray(eeg, dtype=float)
    fmri = np.asarray(fmri, dtype=float)
    behavior = np.asarray(behavior, dtype=float)

    if eeg.size == 0 or fmri.size == 0 or behavior.size == 0:
        raise ValueError("Sygnały wejściowe do raportu analizy nie mogą być puste.")

    primary = eeg[:, 0] if eeg.ndim == 2 else eeg
    secondary = eeg[:, 1] if eeg.ndim == 2 and eeg.shape[1] > 1 else primary

    selected = set(
        analysis_set
        if analysis_set is not None
        else ["spectral", "phase_locking", "connectivity", "information_flow"]
    )
    bands = compute_band_powers(primary, fs) if "spectral" in selected else None
    plv = (
        compute_phase_locking(primary, secondary)
        if "phase_locking" in selected
        else None
    )
    net_input = eeg if eeg.ndim == 2 else np.column_stack([primary, secondary])
    conn = compute_connectivity(net_input) if "connectivity" in selected else None
    flow = (
        compute_information_flow(net_input) if "information_flow" in selected else None
    )
    erp_proxy = float(np.max(primary) - np.min(primary))

    beh_mean = float(np.mean(behavior))
    beh_std = float(np.std(behavior))

    metrics = {
        "band_power_alpha": float(bands.summary.get("alpha", 0.0)) if bands else 0.0,
        "band_power_beta": float(bands.summary.get("beta", 0.0)) if bands else 0.0,
        "erp_proxy_peak_to_peak": erp_proxy,
        "phase_locking_value": float(plv.summary["plv"]) if plv else 0.0,
        "connectivity_mean": float(conn.summary["correlation_mean"]) if conn else 0.0,
        "connectivity_abs_mean": (
            float(conn.summary["correlation_abs_mean"]) if conn else 0.0
        ),
        "pli_proxy_mean": float(conn.summary["pli_proxy_mean"]) if conn else 0.0,
        "region_strength_mean": (
            float(conn.summary["region_strength_mean"]) if conn else 0.0
        ),
        "directional_mean": float(flow.summary["directional_mean"]) if flow else 0.0,
        "behavior_mean": beh_mean,
        "behavior_std": beh_std,
        "fmri_mean": float(np.mean(fmri)),
    }

    comparison: dict[str, float] = {}
    if benchmark:
        if "eeg" in benchmark:
            comparison.update(
                {
                    f"eeg_{k}": v
                    for k, v in comparative_report(eeg, benchmark["eeg"]).items()
                }
            )
        if "fmri" in benchmark:
            comparison.update(
                {
                    f"fmri_{k}": v
                    for k, v in comparative_report(fmri, benchmark["fmri"]).items()
                }
            )
        if "behavior" in benchmark:
            comparison.update(
                {
                    f"behavior_{k}": v
                    for k, v in comparative_report(
                        behavior, benchmark["behavior"]
                    ).items()
                }
            )

    return AnalysisReport(payload={"metrics": metrics, "comparison": comparison})


def build_clinical_difference_report(
    reference_result: dict,
    profile_results: dict[str, dict],
) -> AnalysisReport:
    """Buduje raport różnic między profilem referencyjnym i klinicznymi.

    Parameters
    ----------
    reference_result:
        Wynik uruchomienia referencyjnego, zwykle dla profilu `healthy_v1`.
    profile_results:
        Mapa identyfikator profilu→wynik eksperymentu dla porównywanych profili.

    Returns
    -------
    AnalysisReport
        Raport opisujący największą różnicę według regionu, czasu, funkcji
        poznawczej i mechanizmu profilu klinicznego.

    Raises
    ------
    ValueError
        Gdy aktywność referencyjna lub porównywana jest pusta.
    """
    reference_activity = np.asarray(reference_result.get("activity") or [], dtype=float)
    if reference_activity.ndim == 1:
        reference_activity = reference_activity[:, np.newaxis]
    reference_time = np.asarray(reference_result.get("time") or [], dtype=float)
    reference_model = reference_result.get("model")
    reference_names = list(getattr(reference_model, "names", []))
    if reference_activity.size == 0 or reference_time.size == 0:
        raise ValueError("Wynik referencyjny musi zawierać aktywność i czas.")

    differences: list[dict[str, object]] = []
    for profile_id, result in profile_results.items():
        activity = np.asarray(result.get("activity"), dtype=float)
        if activity.size == 0:
            raise ValueError(f"Wynik profilu {profile_id} nie zawiera aktywności.")

        rows = min(reference_activity.shape[0], activity.shape[0])
        cols = min(reference_activity.shape[1], activity.shape[1])
        delta = np.abs(activity[:rows, :cols] - reference_activity[:rows, :cols])
        mean_by_region = np.mean(delta, axis=0)
        region_idx = int(np.argmax(mean_by_region))
        time_idx = int(np.argmax(delta[:, region_idx]))
        profile = result.get("clinical_profile", {})
        functions = profile.get("cognitive_functions") or result.get(
            "task_activation", {}
        ).get("functions", [])
        region = (
            reference_names[region_idx]
            if region_idx < len(reference_names)
            else f"region_{region_idx}"
        )
        differences.append(
            {
                "profile_id": profile.get("id", profile_id),
                "display_name": profile.get("display_name", profile_id),
                "region": region,
                "time_s": round(
                    float(reference_time[min(time_idx, reference_time.size - 1)]), 6
                ),
                "cognitive_function": functions[0] if functions else "n/a",
                "mechanism": profile.get("mechanism", "n/a"),
                "mean_abs_difference": round(float(mean_by_region[region_idx]), 8),
                "max_abs_difference": round(float(delta[time_idx, region_idx]), 8),
            }
        )

    return AnalysisReport(payload={"clinical_differences": differences})
