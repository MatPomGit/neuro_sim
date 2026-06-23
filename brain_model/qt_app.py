"""Główne okno QApplication oraz kompatybilny punkt startowy GUI PySide6."""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, fields, replace
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, QThread, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .gui_labels import PARAMETER_DESCRIPTIONS, PARAMETER_LABELS, RULE_FIELDS
from .gui_state import GuiState
from .lesson_catalog import lesson_by_label
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .qt_config import (
    apply_config_to_state,
    default_config_filename,
    load_config,
    save_config,
    state_to_config,
)
from .qt_results import (
    EDUCATIONAL_LIMITATION_TEXT_PL,
    ClinicalProfilePanel,
    EventTimelinePanel,
    ObservationPanel,
    ProfileComparisonPanel,
    QtPlotPanel,
    RovingOddballQuestionsPanel,
    apply_run_result,
)
from .qt_runner import SimulationWorker
from .qt_sections import QtSections
from .qt_styles import apply_qt_styles
from .report_export import (
    export_experiment_pdf,
    export_experiment_report,
    export_teaching_package,
)

TUTORIAL_COMPLETED_SETTING = "tutorial/completed"
TUTORIAL_SETTING_SCOPE = "NeuroSim"
TUTORIAL_SETTING_APP = "CognitiveBrainModel"

TUTORIAL_STEPS = (
    "lesson_or_yaml",
    "yaml_applied",
    "duration_applied",
    "simulation_started",
    "simulation_finished",
)



class QtDataclassParameterDialog(QDialog):
    """Okno edycji pól dataclass używanych przez parametry modelu Qt."""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        dataclass_type: type[Any],
        current_values: Any,
        include_fields: set[str] | None = None,
    ) -> None:
        """Zbuduj przewijalny formularz z polskimi etykietami parametrów."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.dataclass_type = dataclass_type
        self.current_values = current_values
        self.include_fields = include_fields
        self.controls: dict[str, QCheckBox | QLineEdit] = {}
        self.resize(520, 520)

        root = QVBoxLayout(self)
        hint = QLabel(
            "Zmień wartości i kliknij „Zapisz”, aby użyć ich w kolejnej symulacji."
        )
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_container = QWidget()
        form = QFormLayout(form_container)
        for field in fields(dataclass_type):
            if include_fields is not None and field.name not in include_fields:
                continue
            value = getattr(current_values, field.name)
            label_text = PARAMETER_LABELS.get(field.name, field.name)
            if isinstance(value, bool):
                control = QCheckBox()
                control.setChecked(value)
            else:
                control = QLineEdit(str(value))
            control.setToolTip(PARAMETER_DESCRIPTIONS.get(field.name, ""))
            self.controls[field.name] = control
            form.addRow(label_text, control)
        scroll.setWidget(form_container)
        root.addWidget(scroll, 1)

        button_row = QHBoxLayout()
        reset_button = QPushButton("Cofnij zmiany")
        reset_button.clicked.connect(self.reset_to_current_values)
        cancel_button = QPushButton("Anuluj")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Zapisz")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.accept)
        button_row.addWidget(reset_button)
        button_row.addStretch(1)
        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)
        root.addLayout(button_row)

    def reset_to_current_values(self) -> None:
        """Przywróć wartości formularza do stanu z chwili otwarcia okna."""
        for field_name, control in self.controls.items():
            value = getattr(self.current_values, field_name)
            if isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            else:
                control.setText(str(value))

    def accept(self) -> None:
        """Zatwierdź okno dopiero po poprawnej walidacji pól formularza."""
        try:
            self.values()
        except ValueError as exc:
            QMessageBox.critical(self, "Niepoprawne parametry", str(exc))
            return
        super().accept()

    def values(self) -> Any:
        """Zwróć instancję dataclass z wartościami wpisanymi w formularzu."""
        updates: dict[str, Any] = {}
        for field in fields(self.dataclass_type):
            current_value = getattr(self.current_values, field.name)
            control = self.controls.get(field.name)
            if control is None:
                updates[field.name] = current_value
                continue
            try:
                if isinstance(current_value, bool):
                    updates[field.name] = control.isChecked()
                elif isinstance(current_value, int) and not isinstance(
                    current_value, bool
                ):
                    updates[field.name] = int(control.text())
                else:
                    updates[field.name] = float(control.text())
            except ValueError as exc:
                raise ValueError(
                    f"Niepoprawna wartość parametru '{field.name}': {control.text()}"
                ) from exc
        return self.dataclass_type(**updates)


class BrainModelQtWindow(QMainWindow):
    """Główne okno konfiguracji i uruchamiania symulacji w PySide6."""

    def __init__(self) -> None:
        """Utwórz stan aplikacji, formularz Qt, menu, status i panel wykresów."""
        super().__init__()
        self.setWindowTitle("konfiguracja symulacji Cognitive Brain Model")
        self.resize(1180, 780)
        self.setMinimumSize(940, 660)
        self.brain_defaults = BrainParams()
        self.osc_defaults = WilsonCowanParams()
        self.state = GuiState(
            dt=str(self.brain_defaults.dt),
            brain_params=self.brain_defaults,
            oscillator_params=self.osc_defaults,
        )
        self.worker_thread: QThread | None = None
        self.worker: SimulationWorker | None = None
        self.last_result_payload: tuple[Any, ...] | None = None
        self.last_run_state_config: dict[str, Any] | None = None
        self.tutorial_active = False
        self.tutorial_step_index = 0
        self.tutorial_mark_completed = False
        self.sections = QtSections(
            self.state,
            {
                "start_simulation": self.start_simulation,
                "show_status": self.show_status,
                "show_clinical_profile": self.show_clinical_profile,
                "show_tutorial": self.show_tutorial,
                "tutorial_yaml_selected": self.on_tutorial_yaml_selected,
                "tutorial_yaml_applied": self.on_tutorial_yaml_applied,
                "tutorial_duration_applied": self.on_tutorial_duration_applied,
            },
        )
        self._build_menu()
        self._build_layout()
        QTimer.singleShot(0, self.show_tutorial_on_first_run)

    def _build_menu(self) -> None:
        """Zbuduj menu aplikacji z akcjami konfiguracji i pomocy."""
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("Plik")
        save_action = file_menu.addAction("Zapisz konfigurację...")
        save_action.triggered.connect(self.save_current_config)
        load_action = file_menu.addAction("Wczytaj konfigurację...")
        load_action.triggered.connect(self.load_existing_config)
        self.export_pdf_action = file_menu.addAction("Eksportuj raport PDF...")
        self.export_pdf_action.setEnabled(False)
        self.export_pdf_action.triggered.connect(self.export_current_pdf_report)
        self.export_comparison_report_action = file_menu.addAction(
            "Eksportuj porównanie profili HTML/PDF..."
        )
        self.export_comparison_report_action.setEnabled(False)
        self.export_comparison_report_action.triggered.connect(
            self.export_current_profile_comparison_report
        )
        self.export_teaching_package_action = file_menu.addAction(
            "Eksportuj pakiet lekcji..."
        )
        self.export_teaching_package_action.setEnabled(False)
        self.export_teaching_package_action.triggered.connect(
            self.export_current_teaching_package
        )
        file_menu.addSeparator()
        close_action = file_menu.addAction("Zamknij")
        close_action.triggered.connect(self.close)

        settings_menu = menu_bar.addMenu("Ustawienia")
        brain_params_action = settings_menu.addAction("Parametry globalne modelu...")
        brain_params_action.triggered.connect(self.open_brain_params_dialog)
        oscillator_params_action = settings_menu.addAction("Parametry oscylatorów...")
        oscillator_params_action.triggered.connect(self.open_oscillator_params_dialog)
        settings_menu.addSeparator()
        reset_defaults_action = settings_menu.addAction("Przywróć domyślne")
        reset_defaults_action.triggered.connect(self.reset_defaults)

        help_menu = menu_bar.addMenu("Pomoc")
        tutorial_action = help_menu.addAction("Samouczek pierwszej symulacji")
        tutorial_action.triggered.connect(self.show_tutorial)
        usage_action = help_menu.addAction("Jak używać")
        usage_action.triggered.connect(self.show_usage_help)
        about_action = help_menu.addAction("O programie")
        about_action.triggered.connect(self.show_about)
        self.setMenuBar(menu_bar)

    def _build_layout(self) -> None:
        """Zbuduj zakładki, sekcje konfiguracji, pasek akcji i status."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        config_tab = QWidget()
        plots_tab = QWidget()
        timeline_tab = QWidget()
        clinical_tab = QWidget()
        observation_tab = QWidget()
        comparison_tab = QWidget()
        questions_tab = QWidget()
        self.tabs.addTab(config_tab, "Konfiguracja")
        self.tabs.addTab(plots_tab, "Wykresy")
        self.tabs.addTab(timeline_tab, "Oś czasu zdarzeń")
        self.tabs.addTab(clinical_tab, "Profil kliniczny")
        self.tabs.addTab(observation_tab, "Co obserwujesz?")
        self.tabs.addTab(comparison_tab, "Porównanie profili")
        self.tabs.addTab(questions_tab, "Pytania kontrolne")

        root = QVBoxLayout(config_tab)
        header_row = QHBoxLayout()
        header = QLabel("Laboratorium symulacji modelu poznawczego")
        header.setObjectName("headerTitle")
        bids_help_button = QPushButton("Instrukcja BIDS")
        bids_help_button.setToolTip(
            "Wyjaśnia standard BIDS i podstawowe zasady organizacji danych."
        )
        bids_help_button.clicked.connect(self.show_bids_help)
        header_row.addWidget(header, 1)
        header_row.addWidget(bids_help_button)
        root.addLayout(header_row)
        subtitle = QLabel(
            "Dobierz scenariusz, uruchom obliczenia i porównaj aktywność modułów "
            "oraz oscylatorów Wilsona-Cowana w jednym przepływie pracy."
        )
        subtitle.setObjectName("hintLabel")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        panes = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()
        left.addWidget(self.sections.build_quick_start_section())
        left.addStretch(1)
        right.addWidget(self.sections.build_advanced_options_section())
        right.addWidget(self.sections.build_results_and_plots_section())
        panes.addLayout(left, 1)
        panes.addLayout(right, 1)
        root.addLayout(panes, 1)

        actions = QHBoxLayout()
        reset_button = QPushButton("Przywróć domyślne")
        reset_button.clicked.connect(self.reset_defaults)
        self.run_button = QPushButton("Uruchom symulację")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.start_simulation)
        self.export_pdf_button = QPushButton("Eksportuj raport PDF")
        self.export_pdf_button.setEnabled(False)
        self.export_pdf_button.setToolTip(
            "Zapisuje gotowy PDF z opisem wyników i aktualnymi wykresami."
        )
        self.export_pdf_button.clicked.connect(self.export_current_pdf_report)
        self.export_comparison_report_button = QPushButton(
            "Eksportuj raport porównania HTML/PDF"
        )
        self.export_comparison_report_button.setEnabled(False)
        self.export_comparison_report_button.setToolTip(
            "Zapisuje raport_porownania_profili.html i raport_porownania_profili.pdf."
        )
        self.export_comparison_report_button.clicked.connect(
            self.export_current_profile_comparison_report
        )
        self.export_teaching_package_button = QPushButton("Eksportuj pakiet lekcji")
        self.export_teaching_package_button.setEnabled(False)
        self.export_teaching_package_button.setToolTip(
            "Zapisuje HTML/PDF, konfigurację, seed, metadane i pytania kontrolne."
        )
        self.export_teaching_package_button.clicked.connect(
            self.export_current_teaching_package
        )
        close_button = QPushButton("Zamknij")
        close_button.clicked.connect(self.close)
        actions.addWidget(reset_button)
        actions.addStretch(1)
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_pdf_button)
        actions.addWidget(self.export_comparison_report_button)
        actions.addWidget(self.export_teaching_package_button)
        actions.addWidget(close_button)
        root.addLayout(actions)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Gotowe.")
        self.status_label.setObjectName("statusLabel")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.progress)
        root.addLayout(status_row)
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        plots_layout = QVBoxLayout(plots_tab)
        self.plot_panel = QtPlotPanel()
        plots_layout.addWidget(self.plot_panel)

        timeline_layout = QVBoxLayout(timeline_tab)
        self.event_timeline_panel = EventTimelinePanel()
        timeline_layout.addWidget(self.event_timeline_panel)

        clinical_layout = QVBoxLayout(clinical_tab)
        self.clinical_profile_panel = ClinicalProfilePanel()
        clinical_layout.addWidget(self.clinical_profile_panel)

        observation_layout = QVBoxLayout(observation_tab)
        self.observation_panel = ObservationPanel()
        observation_layout.addWidget(self.observation_panel)

        comparison_layout = QVBoxLayout(comparison_tab)
        self.profile_comparison_panel = ProfileComparisonPanel()
        comparison_layout.addWidget(self.profile_comparison_panel)

        questions_layout = QVBoxLayout(questions_tab)
        self.roving_questions_panel = RovingOddballQuestionsPanel()
        questions_layout.addWidget(self.roving_questions_panel)

    def open_brain_params_dialog(self) -> None:
        """Otwórz okno ustawień globalnych parametrów modelu poznawczego."""
        self.sections.sync_state_from_controls()
        editable_fields = {
            field.name
            for field in fields(BrainParams)
            if field.name not in RULE_FIELDS and field.name != "dt"
        }
        dialog = QtDataclassParameterDialog(
            self,
            "Parametry globalne modelu",
            BrainParams,
            self.state.brain_params,
            include_fields=editable_fields,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            edited_params = dialog.values()
            current_dt = float(self.state.dt)
        except ValueError as exc:
            QMessageBox.critical(self, "Niepoprawne parametry", str(exc))
            return
        self.state.brain_params = replace(edited_params, dt=current_dt)
        self.status_label.setText("Zapisano parametry globalne modelu.")

    def open_oscillator_params_dialog(self) -> None:
        """Otwórz okno ustawień parametrów oscylatorów Wilsona-Cowana."""
        self.sections.sync_state_from_controls()
        dialog = QtDataclassParameterDialog(
            self,
            "Parametry oscylatorów Wilsona-Cowana",
            WilsonCowanParams,
            self.state.oscillator_params,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.state.oscillator_params = dialog.values()
        except ValueError as exc:
            QMessageBox.critical(self, "Niepoprawne parametry", str(exc))
            return
        self.status_label.setText("Zapisano parametry oscylatorów.")

    def reset_defaults(self) -> None:
        """Przywróć wartości domyślne formularza GUI PySide6."""
        self.state = GuiState(
            dt=str(self.brain_defaults.dt),
            brain_params=self.brain_defaults,
            oscillator_params=self.osc_defaults,
        )
        self.sections.state = self.state
        self.sections.sync_controls_from_state()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText("Przywrócono wartości domyślne.")
        self.progress.setValue(0)
        self.summary_label.setText("")
        self.event_timeline_panel.set_events([])
        self.clinical_profile_panel.set_profile({})
        self.observation_panel.set_context([], {}, {})
        self.roving_questions_panel.set_report({})
        self.last_result_payload = None
        self.last_run_state_config = None
        self.export_pdf_action.setEnabled(False)
        self.export_pdf_button.setEnabled(False)
        self.export_comparison_report_action.setEnabled(False)
        self.export_comparison_report_button.setEnabled(False)
        self.export_teaching_package_action.setEnabled(False)
        self.export_teaching_package_button.setEnabled(False)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_clinical_profile(self, profile: dict[str, Any]) -> None:
        """Pokaż podgląd profilu klinicznego odczytanego z konfiguracji YAML."""
        self.clinical_profile_panel.set_profile(profile)

    def show_status(self, message: str) -> None:
        """Pokaż neutralny komunikat statusu użytkownika w głównym oknie."""
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText(message)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def start_simulation(self) -> None:
        """Uruchom worker QObject w QThread i zablokuj ponowne uruchomienie."""
        if self._simulation_in_progress():
            QMessageBox.information(self, "Informacja", "Symulacja już trwa.")
            return
        self.sections.sync_state_from_controls()
        QTimer.singleShot(0, self.on_tutorial_simulation_started)
        self.last_result_payload = None
        self.last_run_state_config = state_to_config(self.state)
        self.export_pdf_action.setEnabled(False)
        self.export_pdf_button.setEnabled(False)
        self.export_comparison_report_action.setEnabled(False)
        self.export_comparison_report_button.setEnabled(False)
        self.export_teaching_package_action.setEnabled(False)
        self.export_teaching_package_button.setEnabled(False)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText("Symulacja w toku...")
        self.summary_label.setText("")
        self.progress.setValue(0)
        import copy

        self.worker_thread = QThread(self)
        self.worker = SimulationWorker(copy.deepcopy(self.state))
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress_changed)
        self.worker.warning.connect(self.show_warning)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.done.connect(self.on_simulation_result)
        self.worker.done.connect(self.worker.deleteLater)
        self.worker.done.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.on_worker_finished)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_progress_changed(self, value: float) -> None:
        """Zaktualizuj pasek postępu na podstawie sygnału workera."""
        self.progress.setValue(int(value))

    def on_simulation_result(self, payload: object) -> None:
        """Przenieś wynik symulacji do etykiet statusu i panelu wykresów."""
        if not isinstance(payload, tuple) or len(payload) < 9:
            self.on_simulation_error("Worker zwrócił niepoprawny wynik symulacji.")
            return
        result = payload
        self.last_result_payload = result
        has_plots = apply_run_result(self.plot_panel, self.state, result)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText(str(result[0]))
        self.summary_label.setText(str(result[1]))
        self.progress.setValue(100)
        if len(result) >= 11:
            self.event_timeline_panel.set_events(result[9])
            self.clinical_profile_panel.set_profile(result[10])
        if len(result) >= 12:
            self.observation_panel.set_context(result[9], result[10], result[11])
            self.profile_comparison_panel.set_report(result[11])
            self.roving_questions_panel.set_report(result[11])
        has_comparison_table = bool(
            len(result) >= 12
            and isinstance(result[11], dict)
            and result[11].get("profile_comparison_table")
        )
        self.export_pdf_action.setEnabled(True)
        self.export_pdf_button.setEnabled(True)
        self.export_comparison_report_action.setEnabled(has_comparison_table)
        self.export_comparison_report_button.setEnabled(has_comparison_table)
        self.export_teaching_package_action.setEnabled(True)
        self.export_teaching_package_button.setEnabled(True)
        self.tabs.setCurrentIndex(1 if has_plots else 0)
        self.on_tutorial_simulation_finished()
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def on_simulation_error(self, message: str) -> None:
        """Pokaż błąd walidacji lub wykonania symulacji w GUI."""
        self.status_label.setObjectName("warningStatusLabel")
        self.status_label.setText("Błąd konfiguracji.")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        QMessageBox.critical(self, "Błąd", message)

    def export_current_pdf_report(self) -> None:
        """Zapisz opisany raport PDF dla ostatniego zakończonego eksperymentu."""
        result = self.last_result_payload
        if result is None or len(result) < 12:
            QMessageBox.information(
                self,
                "Brak wyników",
                "Najpierw uruchom symulację, aby wygenerować raport PDF.",
            )
            return

        save_info = result[2] if isinstance(result[2], dict) else None
        output_dir = save_info.get("output_dir") if save_info else None
        default_dir = Path(output_dir) if output_dir else Path.cwd()
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Eksportuj raport PDF",
            str(default_dir / "raport_eksperymentu.pdf"),
            "Pliki PDF (*.pdf);;Wszystkie pliki (*)",
        )
        if not target:
            return

        try:
            report_path = export_experiment_pdf(
                target,
                status_message=str(result[0]),
                summary_text=str(result[1]),
                state_config=self.last_run_state_config or state_to_config(self.state),
                event_timeline=list(result[9]),
                clinical_profile=dict(result[10]),
                analysis_report=dict(result[11]),
                plots=self.plot_panel.plots_for_export(),
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać raportu PDF: {exc}"
            )
            return

        self.status_label.setText(f"Zapisano raport PDF: {report_path}")

    def export_current_teaching_package(self) -> None:
        """Zapisz kompletny pakiet zajęciowy dla ostatniej symulacji."""
        result = self.last_result_payload
        if result is None or len(result) < 12:
            QMessageBox.information(
                self,
                "Brak wyników",
                "Najpierw uruchom symulację, aby wygenerować pakiet lekcji.",
            )
            return

        save_info = result[2] if isinstance(result[2], dict) else None
        output_dir = save_info.get("output_dir") if save_info else None
        default_dir = Path(output_dir) if output_dir else Path.cwd()
        target = QFileDialog.getExistingDirectory(
            self,
            "Eksportuj pakiet lekcji",
            str(default_dir),
        )
        if not target:
            return

        lesson = lesson_by_label(self.sections.ready_lesson_combo.currentText())
        lesson_metadata = asdict(lesson) if lesson is not None else None
        try:
            package_path = export_teaching_package(
                Path(target) / "pakiet_lekcji_neuro_sim",
                status_message=str(result[0]),
                summary_text=str(result[1]),
                state_config=self.last_run_state_config or state_to_config(self.state),
                gui_state=self.state,
                scenario_config_path=self.state.scenario_config_path,
                comparison_config_path=self.state.comparison_config_path or None,
                event_timeline=list(result[9]),
                clinical_profile=dict(result[10]),
                analysis_report=dict(result[11]),
                lesson_metadata=lesson_metadata,
                seed=self.state.seed,
                plots=self.plot_panel.plots_for_export(),
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać pakietu lekcji: {exc}"
            )
            return

        QMessageBox.information(
            self,
            "Eksport zakończony",
            f"Pakiet lekcji zapisano w katalogu: {package_path}\n\n"
            f"{EDUCATIONAL_LIMITATION_TEXT_PL}",
        )
        self.status_label.setText(f"Pakiet lekcji zapisano w katalogu: {package_path}")

    def export_current_profile_comparison_report(self) -> None:
        """Zapisz HTML i PDF z tabelą porównania profili klinicznych."""
        result = self.last_result_payload
        if result is None or len(result) < 12 or not isinstance(result[11], dict):
            QMessageBox.information(
                self,
                "Brak porównania",
                "Najpierw uruchom tryb „Porównaj profile”, aby wygenerować raport.",
            )
            return
        analysis_report = dict(result[11])
        if not analysis_report.get("profile_comparison_table"):
            QMessageBox.information(
                self,
                "Brak tabeli",
                "Bieżący wynik nie zawiera tabeli porównania profili.",
            )
            return

        save_info = result[2] if isinstance(result[2], dict) else None
        output_dir = save_info.get("output_dir") if save_info else None
        default_dir = Path(output_dir) if output_dir else Path.cwd()
        target = QFileDialog.getExistingDirectory(
            self,
            "Eksportuj raport porównania profili",
            str(default_dir),
        )
        if not target:
            return

        report_dir = Path(target)
        try:
            html_path = export_experiment_report(
                report_dir / "raport_porownania_profili.html",
                status_message=str(result[0]),
                summary_text=str(result[1]),
                state_config=self.last_run_state_config or state_to_config(self.state),
                event_timeline=list(result[9]),
                clinical_profile=dict(result[10]),
                analysis_report=analysis_report,
                title="Raport porównania profili",
                full_trial_table=False,
            )
            pdf_path = export_experiment_pdf(
                report_dir / "raport_porownania_profili.pdf",
                status_message=str(result[0]),
                summary_text=str(result[1]),
                state_config=self.last_run_state_config or state_to_config(self.state),
                event_timeline=list(result[9]),
                clinical_profile=dict(result[10]),
                analysis_report=analysis_report,
                plots=[],
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać raportu porównania: {exc}"
            )
            return

        self.status_label.setText(
            f"Zapisano raport porównania profili: {html_path}, {pdf_path}"
        )

    def on_worker_finished(self) -> None:
        """Odłącz zakończony worker Qt i jego wątek od okna głównego."""
        self.worker = None
        self.worker_thread = None

    def _simulation_in_progress(self) -> bool:
        """Sprawdź, czy wątek symulacji nadal wykonuje obliczenia."""
        return self.worker_thread is not None and self.worker_thread.isRunning()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Zablokuj zamknięcie okna do czasu zakończenia aktywnej symulacji."""
        if self._simulation_in_progress():
            QMessageBox.warning(
                self,
                "Symulacja w toku",
                "Zamknięcie okna będzie możliwe po zakończeniu obliczeń.",
            )
            event.ignore()
            return
        super().closeEvent(event)

    def show_warning(self, message: str) -> None:
        """Wyświetl ostrzeżenie użytkowe bez zamykania aplikacji."""
        QMessageBox.warning(self, "Ostrzeżenie", message)

    def save_current_config(self) -> None:
        """Zapisz aktualną konfigurację GUI do pliku wybranego przez użytkownika."""
        self.sections.sync_state_from_controls()
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz konfigurację",
            default_config_filename(),
            "Pliki JSON (*.json);;Wszystkie pliki (*)",
        )
        if not target:
            return
        try:
            save_config(Path(target), self.state)
        except Exception as exc:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać konfiguracji: {exc}"
            )
            return
        self.status_label.setText(f"Zapisano konfigurację: {target}")

    def load_existing_config(self) -> None:
        """Wczytaj konfigurację GUI z pliku JSON wybranego przez użytkownika."""
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Wczytaj konfigurację",
            "",
            "Pliki JSON (*.json);;Wszystkie pliki (*)",
        )
        if not source:
            return
        try:
            config = load_config(Path(source))
            apply_config_to_state(self.state, config)
            self.sections.sync_controls_from_state()
        except Exception as exc:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się wczytać konfiguracji: {exc}"
            )
            return
        self.status_label.setText(f"Wczytano konfigurację: {source}")

    def tutorial_settings(self) -> QSettings:
        """Zwróć ustawienia aplikacji przechowujące status samouczka."""
        return QSettings(TUTORIAL_SETTING_SCOPE, TUTORIAL_SETTING_APP)

    def show_tutorial_on_first_run(self) -> None:
        """Automatycznie pokaż samouczek, jeśli użytkownik nie zakończył go wcześniej."""
        settings = self.tutorial_settings()
        if settings.value(TUTORIAL_COMPLETED_SETTING, False, bool):
            return
        self.show_tutorial(mark_completed=True)

    def show_tutorial(self, mark_completed: bool = False) -> None:
        """Rozpocznij monitorowany samouczek pierwszej symulacji.

        Parameters
        ----------
        mark_completed:
            Gdy `True`, zakończenie samouczka zapisuje, że automatyczny start
            nie powinien wracać przy kolejnym uruchomieniu.
        """
        self.tutorial_active = True
        self.tutorial_step_index = 0
        self.tutorial_mark_completed = mark_completed
        self.tabs.setCurrentIndex(0)
        self.sections.ready_lesson_combo.setFocus()
        self.show_tutorial_step(
            "Krok 1 z 5 — wybierz lekcję albo konfigurację YAML",
            "Co nacisnąć: w sekcji „Szybki start” wybierz pozycję w polu "
            "„Lekcja” albo „konfiguracja YAML”.\n\n"
            "Dlaczego: wybór wskazuje zwalidowany plik YAML, czyli źródło "
            "parametrów pierwszej powtarzalnej symulacji.\n\n"
            "Co się stanie: po wyborze samouczek automatycznie pokaże następne "
            "polecenie i poprosi o zastosowanie konfiguracji.",
        )

    def show_tutorial_step(self, title: str, body: str) -> None:
        """Pokaż użytkownikowi aktualne polecenie monitorowanego samouczka.

        Parameters
        ----------
        title:
            Tytuł okna opisujący numer i cel kroku.
        body:
            Instrukcja wyjaśniająca co nacisnąć, dlaczego i jaki będzie skutek.
        """
        QTimer.singleShot(0, lambda: QMessageBox.information(self, title, body))

    def on_tutorial_yaml_selected(self) -> None:
        """Przejdź do instrukcji zastosowania YAML po wyborze lekcji lub presetu."""
        if not self._advance_tutorial_from("lesson_or_yaml"):
            return
        self.sections.apply_yaml_button.setFocus()
        self.show_tutorial_step(
            "Krok 2 z 5 — zastosuj konfigurację YAML",
            "Co nacisnąć: kliknij „Zastosuj konfigurację YAML”.\n\n"
            "Dlaczego: formularz GUI przepisze z YAML scenariusz, czas, dt, seed "
            "i ustawienie zapisu wyników bez kopiowania logiki silnika.\n\n"
            "Co się stanie: zobaczysz podgląd profilu oraz następne polecenie "
            "dotyczące czasu pierwszej symulacji.",
        )

    def on_tutorial_yaml_applied(self) -> None:
        """Przejdź do instrukcji ustawienia sugerowanego czasu po aplikacji YAML."""
        if not self._advance_tutorial_from("yaml_applied"):
            return
        self.sections.suggested_duration_button.setFocus()
        self.show_tutorial_step(
            "Krok 3 z 5 — ustaw sugerowany czas",
            "Co nacisnąć: kliknij „Użyj sugerowanego czasu”.\n\n"
            "Dlaczego: pierwszy przebieg powinien używać czasu dobranego do "
            "scenariusza, aby wynik był czytelny i łatwy do odtworzenia.\n\n"
            "Co się stanie: pole czasu zostanie zaktualizowane, a samouczek "
            "przejdzie do uruchomienia symulacji.",
        )

    def on_tutorial_duration_applied(self) -> None:
        """Przejdź do instrukcji uruchomienia symulacji po ustawieniu czasu."""
        if not self._advance_tutorial_from("duration_applied"):
            return
        self.run_button.setFocus()
        self.show_tutorial_step(
            "Krok 4 z 5 — uruchom symulację",
            "Co nacisnąć: kliknij „Uruchom symulację”.\n\n"
            "Dlaczego: aplikacja przekaże aktualny stan formularza do workera Qt "
            "i zapisze migawkę konfiguracji użytej w przebiegu.\n\n"
            "Co się stanie: pasek postępu pokaże obliczenia, a po ich zakończeniu "
            "samouczek wyświetli ostatnie okno z miejscem odczytu wyników.",
        )

    def on_tutorial_simulation_started(self) -> None:
        """Zarejestruj kliknięcie uruchomienia jako kolejny postęp samouczka."""
        if not self._advance_tutorial_from("simulation_started"):
            return
        self.show_tutorial_step(
            "Symulacja została uruchomiona",
            "Teraz niczego nie klikaj. Poczekaj na zakończenie obliczeń.\n\n"
            "Samouczek monitoruje postęp i pokaże ostatnie polecenie, gdy wyniki "
            "będą dostępne w panelach GUI.",
        )

    def on_tutorial_simulation_finished(self) -> None:
        """Zakończ samouczek po otrzymaniu wyników pierwszej symulacji."""
        if not self._advance_tutorial_from("simulation_finished"):
            return
        self.tabs.setCurrentIndex(1)
        self.show_tutorial_step(
            "Krok 5 z 5 — odczytaj wynik",
            "Co nacisnąć: przejrzyj zakładki „Wykresy”, „Oś czasu zdarzeń” "
            "i „Co obserwujesz?”.\n\n"
            "Dlaczego: te panele pokazują wynik obliczeń, przebieg zdarzeń i "
            "interpretację dydaktyczną bez traktowania wyniku jako diagnozy.\n\n"
            "Co się stało: pierwsza symulacja została wykonana, a samouczek "
            "oznaczono jako zakończony.",
        )
        self.finish_tutorial()

    def finish_tutorial(self) -> None:
        """Zapisz zakończenie samouczka i wyłącz monitorowanie kolejnych akcji."""
        if self.tutorial_mark_completed:
            self.tutorial_settings().setValue(TUTORIAL_COMPLETED_SETTING, True)
        self.tutorial_active = False
        self.tutorial_step_index = 0
        self.tutorial_mark_completed = False

    def _advance_tutorial_from(self, expected_step: str) -> bool:
        """Sprawdź oczekiwany etap i przesuń wskaźnik postępu samouczka.

        Parameters
        ----------
        expected_step:
            Nazwa kroku, który powinien zostać właśnie wykonany.

        Returns
        -------
        bool
            `True`, gdy monitorowany krok pasuje do aktualnego stanu samouczka.
        """
        if not self.tutorial_active:
            return False
        if self.tutorial_step_index >= len(TUTORIAL_STEPS):
            return False
        if TUTORIAL_STEPS[self.tutorial_step_index] != expected_step:
            return False
        self.tutorial_step_index += 1
        return True

    def show_usage_help(self) -> None:
        """Pokaż krótką instrukcję obsługi aplikacji PySide6."""
        QMessageBox.information(
            self,
            "Jak używać",
            "1. Wybierz scenariusz i czas symulacji.\n"
            "2. Opcjonalnie rozwiń opcje zaawansowane.\n"
            "3. Uruchom symulację i przejdź do zakładki Wykresy.",
        )

    def show_bids_help(self) -> None:
        """Pokaż instrukcję standardu BIDS dla danych mózgowych i EEG."""
        QMessageBox.information(
            self,
            "Instrukcja BIDS",
            "BIDS (Brain Imaging Data Structure) to standard organizacji danych "
            "neuroobrazowych, EEG i danych behawioralnych powiązanych z badaniem.\n\n"
            "Po co go używać:\n"
            "• ułatwia odtworzenie eksperymentu i audyt wyników;\n"
            "• porządkuje katalogi, nazwy plików i metadane;\n"
            "• oddziela dane surowe od wyników w katalogu derivatives/;\n"
            "• pozwala sprawdzać zbiory narzędziem BIDS Validator.\n\n"
            "Minimalnie sprawdź, czy zbiór ma dataset_description.json, "
            "pliki zaczynają się od encji sub-, a metadane EEG lub obrazowania "
            "opisują parametry potrzebne do interpretacji danych.",
        )

    def show_about(self) -> None:
        """Pokaż informację o aplikacji GUI modelu poznawczego."""
        QMessageBox.information(
            self,
            "O programie",
            "Neuro Sim — GUI PySide6 dla modelu poznawczego z oscylatorami Wilsona-Cowana.",
        )


def create_application(argv: list[str] | None = None) -> QApplication:
    """Utwórz albo zwróć istniejącą instancję QApplication."""
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication(argv if argv is not None else sys.argv)


def run_gui() -> None:
    """Uruchom aplikację GUI PySide6 z katalogu głównego projektu."""
    os.chdir(Path(__file__).resolve().parent.parent)
    app = create_application(sys.argv)
    apply_qt_styles(app)
    window = BrainModelQtWindow()
    window.show()
    sys.exit(app.exec())


BrainModelGUI = BrainModelQtWindow
