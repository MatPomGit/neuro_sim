"""Główne okno QApplication oraz kompatybilny punkt startowy GUI PySide6."""

from __future__ import annotations

import os
import sys
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

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

from .gui_forms import PARAMETER_DESCRIPTIONS, PARAMETER_LABELS, RULE_FIELDS
from .gui_state import GuiState
from .oscillators import WilsonCowanParams
from .params import BrainParams
from .qt_config import (
    apply_config_to_state,
    default_config_filename,
    load_config,
    save_config,
)
from .qt_results import QtPlotPanel, apply_run_result
from .qt_runner import SimulationWorker
from .qt_sections import QtSections
from .qt_styles import apply_qt_styles


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
        self.worker: SimulationWorker | None = None
        self.sections = QtSections(
            self.state,
            {
                "start_simulation": self.start_simulation,
                "show_status": self.show_status,
            },
        )
        self._build_menu()
        self._build_layout()

    def _build_menu(self) -> None:
        """Zbuduj menu aplikacji z akcjami konfiguracji i pomocy."""
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("Plik")
        save_action = file_menu.addAction("Zapisz konfigurację...")
        save_action.triggered.connect(self.save_current_config)
        load_action = file_menu.addAction("Wczytaj konfigurację...")
        load_action.triggered.connect(self.load_existing_config)
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
        self.tabs.addTab(config_tab, "Konfiguracja")
        self.tabs.addTab(plots_tab, "Wykresy")

        root = QVBoxLayout(config_tab)
        header = QLabel("Laboratorium symulacji modelu poznawczego")
        header.setObjectName("headerTitle")
        root.addWidget(header)
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
        run_button = QPushButton("Uruchom symulację")
        run_button.setObjectName("primaryButton")
        run_button.clicked.connect(self.start_simulation)
        close_button = QPushButton("Zamknij")
        close_button.clicked.connect(self.close)
        actions.addWidget(reset_button)
        actions.addStretch(1)
        actions.addWidget(run_button)
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
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_status(self, message: str) -> None:
        """Pokaż neutralny komunikat statusu użytkownika w głównym oknie."""
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText(message)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def start_simulation(self) -> None:
        """Uruchom symulację w workerze QThread i zablokuj ponowne uruchomienie."""
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Informacja", "Symulacja już trwa.")
            return
        self.sections.sync_state_from_controls()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText("Symulacja w toku...")
        self.summary_label.setText("")
        self.progress.setValue(0)
        import copy

        self.worker = SimulationWorker(copy.deepcopy(self.state))
        self.worker.progress_changed.connect(self.on_progress_changed)
        self.worker.warning_reported.connect(self.show_warning)
        self.worker.error_reported.connect(self.on_simulation_error)
        self.worker.result_ready.connect(self.on_simulation_result)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_progress_changed(self, value: float) -> None:
        """Zaktualizuj pasek postępu na podstawie sygnału workera."""
        self.progress.setValue(int(value))

    def on_simulation_result(self, payload: object) -> None:
        """Przenieś wynik symulacji do etykiet statusu i panelu wykresów."""
        if not isinstance(payload, tuple) or len(payload) != 9:
            self.on_simulation_error("Worker zwrócił niepoprawny wynik symulacji.")
            return
        result = payload
        has_plots = apply_run_result(self.plot_panel, self.state, result)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setText(str(result[0]))
        self.summary_label.setText(str(result[1]))
        self.progress.setValue(100)
        self.tabs.setCurrentIndex(1 if has_plots else 0)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def on_simulation_error(self, message: str) -> None:
        """Pokaż błąd walidacji lub wykonania symulacji w GUI."""
        self.status_label.setObjectName("warningStatusLabel")
        self.status_label.setText("Błąd konfiguracji.")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        QMessageBox.critical(self, "Błąd", message)

    def on_worker_finished(self) -> None:
        """Odłącz zakończony worker Qt od okna głównego."""
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

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

    def show_usage_help(self) -> None:
        """Pokaż krótką instrukcję obsługi aplikacji PySide6."""
        QMessageBox.information(
            self,
            "Jak używać",
            "1. Wybierz scenariusz i czas symulacji.\n"
            "2. Opcjonalnie rozwiń opcje zaawansowane.\n"
            "3. Uruchom symulację i przejdź do zakładki Wykresy.",
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
