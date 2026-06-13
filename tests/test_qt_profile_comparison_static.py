"""Statyczne testy GUI dla trybu porównania profili."""

from __future__ import annotations

from pathlib import Path

import yaml

from brain_model.qt_config import comparison_profile_rows_for_label

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_SECTIONS_PATH = REPO_ROOT / "brain_model" / "qt_sections.py"
QT_APP_PATH = REPO_ROOT / "brain_model" / "qt_app.py"
QT_RESULTS_PATH = REPO_ROOT / "brain_model" / "qt_results.py"
QT_CONFIG_PATH = REPO_ROOT / "brain_model" / "qt_config.py"


def test_quick_start_has_explicit_single_and_comparison_switch() -> None:
    """Sekcja szybkiego startu ma jawny polski przełącznik dwóch trybów pracy."""
    source = QT_SECTIONS_PATH.read_text(encoding="utf-8")

    assert 'QGroupBox("Tryb pracy")' in source
    assert 'QRadioButton("Pojedynczy eksperyment")' in source
    assert 'QRadioButton("Porównaj profile")' in source
    assert (
        'layout.addRow("Pojedynczy eksperyment / Porównaj profile", mode_group)'
        in source
    )
    assert (
        "self.comparison_mode_radio.toggled.connect(self.on_run_mode_changed)" in source
    )
    assert (
        'write_combo_box(self.command_combo, COMMAND_LABELS["compare_profiles"])'
        in source
    )


def test_comparison_profile_list_is_loaded_from_yaml_configs() -> None:
    """Lista profili widoczna w GUI jest powiązana z `configs/comparisons/*.yaml`."""
    sections_source = QT_SECTIONS_PATH.read_text(encoding="utf-8")
    config_source = QT_CONFIG_PATH.read_text(encoding="utf-8")

    assert "comparison_profile_list_text_for_label" in sections_source
    assert (
        'layout.addRow("profile z YAML", self.comparison_profiles_label)'
        in sections_source
    )
    assert 'comparison_payload.get("clinical_profiles", [])' in config_source

    for comparison_path in sorted(
        (REPO_ROOT / "configs" / "comparisons").glob("*.yaml")
    ):
        payload = yaml.safe_load(comparison_path.read_text(encoding="utf-8"))
        label = payload["label_pl"]
        rows = comparison_profile_rows_for_label(label)

        assert rows
        assert len(rows) == len(payload["clinical_profiles"])
        assert {row["path"] for row in rows} == set(payload["clinical_profiles"])
        assert all(row["profile"] for row in rows)
        assert all(row["expected_direction"] for row in rows)


def test_profile_comparison_result_table_has_polish_headers() -> None:
    """Zakładka wynikowa pokazuje wymaganą tabelę porównania profili po polsku."""
    app_source = QT_APP_PATH.read_text(encoding="utf-8")
    results_source = QT_RESULTS_PATH.read_text(encoding="utf-8")

    assert 'self.tabs.addTab(comparison_tab, "Porównanie profili")' in app_source
    assert "self.profile_comparison_panel = ProfileComparisonPanel()" in app_source
    assert "self.profile_comparison_panel.set_report(result[11])" in app_source
    for label in (
        '"profil"',
        '"oczekiwany kierunek"',
        '"obserwowany kierunek"',
        '"próg jakościowy"',
        '"interpretacja"',
    ):
        assert label in results_source
    for key in (
        '"profile"',
        '"expected_direction"',
        '"observed_direction"',
        '"qualitative_threshold"',
        '"interpretation"',
    ):
        assert key in results_source


def test_profile_comparison_export_uses_required_html_and_pdf_names() -> None:
    """GUI eksportuje raport porównania pod wymaganymi nazwami HTML i PDF."""
    source = QT_APP_PATH.read_text(encoding="utf-8")

    assert '"Eksportuj porównanie profili HTML/PDF..."' in source
    assert '"Eksportuj raport porównania HTML/PDF"' in source
    assert 'report_dir / "raport_porownania_profili.html"' in source
    assert 'report_dir / "raport_porownania_profili.pdf"' in source
    assert "export_experiment_report" in source
    assert "export_experiment_pdf" in source
    assert 'title="Raport porównania profili"' in source
