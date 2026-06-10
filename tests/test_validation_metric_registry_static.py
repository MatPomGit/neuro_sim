"""Statyczne testy rejestru metryk raportowych i ostrzeżeń GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain_core.analysis.reports import (
    build_analysis_report,
    load_validation_metric_registry,
)


def _glossary_labels() -> dict[str, str]:
    """Wczytaj techniczne nazwy metryk i polskie etykiety ze słownika projektu."""
    labels: dict[str, str] = {}
    for line in (
        Path("docs/english_polish_glossary.md").read_text(encoding="utf-8").splitlines()
    ):
        stripped_line = line.strip()
        if (
            not stripped_line.startswith("|")
            or "---" in stripped_line
            or "English" in stripped_line
        ):
            continue
        cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
        if len(cells) == 3:
            labels[cells[0]] = cells[1]
    return labels


def test_reported_metrics_have_polish_labels_and_validation_registry_entries() -> Any:
    """Każda metryka raportu ma polską etykietę i opis walidacyjny."""
    import numpy as np

    time = np.linspace(0.0, 1.0, 64)
    eeg = np.column_stack([np.sin(2 * np.pi * time), np.cos(2 * np.pi * time)])
    fmri = np.column_stack([0.1 * time, 0.2 * time])
    behavior = np.linspace(0.0, 1.0, time.size)

    report = build_analysis_report(eeg=eeg, fmri=fmri, behavior=behavior, fs=64.0)
    metric_names = set(report.payload["metrics"])
    registry = load_validation_metric_registry()
    glossary = _glossary_labels()

    assert metric_names <= set(registry)
    assert metric_names <= set(glossary)
    for metric_name in metric_names:
        assert registry[metric_name]["polish_label"] == glossary[metric_name]
        assert registry[metric_name]["validation_data_source"].strip()
        assert registry[metric_name]["interpretation_range"].strip()
        assert registry[metric_name]["limitations"].strip()


def test_analysis_report_renders_interpretation_limitations_section() -> Any:
    """Markdown i CSV raportu pokazują ograniczenia interpretacji metryk."""
    import numpy as np

    time = np.linspace(0.0, 1.0, 64)
    report = build_analysis_report(
        eeg=np.column_stack([time, time[::-1]]),
        fmri=np.column_stack([time * 0.1, time * 0.2]),
        behavior=time,
        fs=64.0,
    )

    markdown = report.to_markdown()
    csv_rows = report.to_csv_rows()

    assert "## Ograniczenia interpretacji" in markdown
    assert "moc pasma alfa" in markdown
    assert "nie jest" in markdown.lower()
    assert any(row["section"] == "interpretation_limitations" for row in csv_rows)


def test_qt_results_contains_non_diagnostic_metric_warnings() -> Any:
    """GUI ma krótkie ostrzeżenia edukacyjne dla EEG, BOLD i zachowania."""
    source = Path("brain_model/qt_results.py").read_text(encoding="utf-8")

    assert "Ostrzeżenia edukacyjne przy metrykach" in source
    assert "METRIC_WARNING_GROUPS" in source
    assert "EEG" in source
    assert "BOLD" in source
    assert "behavior" in source
    assert "normą " in source and "psychometryczną" in source
    assert "nie zastępują" in source and "fMRI" in source
    assert "podstawą rozpoznania klinicznego" in source
