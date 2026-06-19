from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .io import load_run


def _run_metrics(run: dict) -> dict:
    """Policz zagregowane metryki pojedynczego uruchomienia.

    Parameters
    ----------
    run:
        Słownik uruchomienia zwrócony przez ``load_run``. Musi zawierać
        ``diagnostics`` oraz ``oscillations.band_power`` z seriami liczbowymi
        długości liczby kroków symulacji.

    Returns
    -------
    dict[str, float]
        Płaski słownik średnich lub maksimów diagnostycznych. Metryki mocy pasm
        są bezwymiarowymi średnimi sum kwadratów, a serie czasowe są agregowane
        po całym horyzoncie symulacji w sekundach.

    Raises
    ------
    KeyError
        Gdy brakuje wymaganych sekcji ``diagnostics`` albo ``oscillations``.
    TypeError
        Gdy serie nie mogą zostać zagregowane przez NumPy.
    """
    d = run["diagnostics"]
    o = run["oscillations"]["band_power"]
    return {
        "prediction_error_mean": float(np.mean(d.get("prediction_error", 0.0))),
        "gw_ignition_peak": float(np.max(d.get("gw_ignition", 0.0))),
        "dopamine_delta_mean": float(np.mean(d.get("dopamine_delta", 0.0))),
        "theta_mean": float(np.mean(o.get("theta", 0.0))),
        "alpha_mean": float(np.mean(o.get("alpha", 0.0))),
        "beta_mean": float(np.mean(o.get("beta", 0.0))),
        "gamma_mean": float(np.mean(o.get("gamma", 0.0))),
    }


def generate_comparison_report(
    run_dirs: Any, output_path: str | Path = "outputs/report_comparison.png"
) -> Any:
    """Wygeneruj obraz PNG porównujący wiele uruchomień symulacji.

    Parameters
    ----------
    run_dirs:
        Niepusta kolekcja katalogów wyników zapisanych przez symulację. Każdy
        katalog musi być czytelny przez ``load_run`` i zawierać serie czasu,
        aktywacji, diagnostyki oraz oscylacji.
    output_path:
        Ścieżka pliku PNG raportu. Katalog nadrzędny zostanie utworzony, jeśli
        nie istnieje.

    Returns
    -------
    Path
        Ścieżka zapisanego pliku raportu.

    Raises
    ------
    ValueError
        Gdy ``run_dirs`` jest puste.
    OSError
        Gdy nie można odczytać danych wejściowych albo zapisać pliku PNG.

    Notes
    -----
    Raport jest użytkowym artefaktem porównawczym: zestawia przebiegi aktywacji,
    uproszczoną moc pasm EEG i tabelę zagregowanych metryk bez zmiany danych
    źródłowych uruchomień.
    """
    if not run_dirs:
        raise ValueError("run_dirs cannot be empty")
    runs = [load_run(path) for path in run_dirs]
    labels = [Path(run["path"]).name for run in runs]
    metrics = [_run_metrics(run) for run in runs]

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    for run, label in zip(runs, labels):
        axes[0, 0].plot(
            run["time"], run["diagnostics"]["prediction_error"], label=label
        )
    axes[0, 0].set_title("Prediction error")
    axes[0, 0].set_xlabel("Time [s]")
    axes[0, 0].legend(fontsize=8)

    for run, label in zip(runs, labels):
        axes[0, 1].plot(run["time"], run["diagnostics"]["gw_ignition"], label=label)
    axes[0, 1].set_title("Global workspace ignition")
    axes[0, 1].set_xlabel("Time [s]")

    x = np.arange(len(labels))
    width = 0.18
    for i, band in enumerate(["theta_mean", "alpha_mean", "beta_mean", "gamma_mean"]):
        axes[1, 0].bar(
            x + (i - 1.5) * width,
            [m[band] for m in metrics],
            width=width,
            label=band.replace("_mean", ""),
        )
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(labels, rotation=30, ha="right")
    axes[1, 0].set_title("Mean band power")
    axes[1, 0].legend()

    table_data = [
        [
            f"{m['prediction_error_mean']:.3f}",
            f"{m['gw_ignition_peak']:.3f}",
            f"{m['dopamine_delta_mean']:.3f}",
        ]
        for m in metrics
    ]
    axes[1, 1].axis("off")
    axes[1, 1].table(
        cellText=table_data,
        rowLabels=labels,
        colLabels=["PE mean", "GW peak", "DA mean"],
        loc="center",
    )
    axes[1, 1].set_title("Aggregated metrics")

    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return str(out)
