"""Sekcje formularza PySide6 dla konfiguracji i wyboru wyników."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .gui_forms import COMMAND_LABELS, COMMAND_VALUES, PARAMETER_DESCRIPTIONS
from .qt_state import QtGuiState
from .scenarios import get_scenario, list_scenarios

DEFAULT_PLOTS = {
    "activity": True,
    "simulated_brain_activity": True,
    "brain_region_projections": True,
    "region_activity_2d": True,
    "diagnostics": True,
    "behavior": True,
    "eeg": True,
    "band_power": True,
    "weight_trajectories": True,
    "weight_deltas": True,
    "scenario_channels": True,
    "scenario_timeline": True,
}

PLOT_LABELS = {
    "activity": "aktywacje modułów poznawczych",
    "simulated_brain_activity": "symulowana aktywność mózgu (mapa cieplna)",
    "brain_region_projections": "4 rzuty mózgu: aktywacja regionów SVG",
    "region_activity_2d": "2D: aktywacja regionów mózgu w czasie",
    "diagnostics": "zmienne diagnostyczne i neuromodulacyjne",
    "behavior": "przebiegi decyzyjne + markery decyzji",
    "eeg": "sygnały EEG E-I dla wybranych modułów",
    "band_power": "moc pasm theta/alpha/beta/gamma",
    "weight_trajectories": "trajektorie adaptowanych wag W",
    "weight_deltas": "przyrosty wag ΔW / krok",
    "scenario_channels": "kanały bodźców scenariusza",
    "scenario_timeline": "oś czasu scenariusza (fazy i zdarzenia)",
}


class QtSections:
    """Buduje sekcje formularza i synchronizuje je ze stanem GUI."""

    def __init__(self, state: QtGuiState, callbacks: dict[str, Any]) -> None:
        """Utwórz pomocnik sekcji z referencją do stanu i akcji okna."""
        self.state = state
        self.callbacks = callbacks
        self.plot_checks: dict[str, QCheckBox] = {}
        self.plot_preset_buttons: dict[str, QRadioButton] = {}
        self.plot_preset_description: QLabel | None = None
        self.plot_details_toggle: QToolButton | None = None
        self.plot_details_group: QGroupBox | None = None
        self.advanced_group: QGroupBox | None = None

    def build_quick_start_section(self) -> QGroupBox:
        """Zbuduj sekcję „Szybki start” z minimalnymi decyzjami użytkownika."""
        group = QGroupBox("Szybki start")
        layout = QFormLayout(group)
        hint = QLabel(
            "Minimalny zestaw decyzji potrzebny do uruchomienia powtarzalnej symulacji."
        )
        hint.setObjectName("hintLabel")
        layout.addRow(hint)

        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(list_scenarios())
        self.scenario_combo.setCurrentText(self.state.scenario)
        self.scenario_combo.setToolTip(PARAMETER_DESCRIPTIONS["scenario"])
        self.scenario_combo.currentTextChanged.connect(self.refresh_scenario_details)
        layout.addRow("scenariusz", self.scenario_combo)

        self.T_edit = QLineEdit(self.state.T)
        self.T_edit.setToolTip(PARAMETER_DESCRIPTIONS["T"])
        self.T_edit.textChanged.connect(lambda _text: self.on_duration_changed())
        layout.addRow("czas symulacji [s]", self.T_edit)

        self.save_results_check = QCheckBox("Zapisz wyniki po symulacji")
        self.save_results_check.setChecked(self.state.save_results)
        self.save_results_check.setToolTip(PARAMETER_DESCRIPTIONS["save_results"])
        layout.addRow(self.save_results_check)

        self.scenario_details_label = QLabel("")
        self.scenario_details_label.setWordWrap(True)
        self.scenario_details_label.setToolTip(
            PARAMETER_DESCRIPTIONS["scenario_details"]
        )
        layout.addRow(self.scenario_details_label)
        self.refresh_scenario_details()
        return group

    def build_advanced_options_section(self) -> QWidget:
        """Zbuduj sekcję „Opcje zaawansowane” z parametrami technicznymi."""
        container = QWidget()
        outer = QVBoxLayout(container)
        self.advanced_toggle = QCheckBox("Pokaż opcje zaawansowane")
        self.advanced_toggle.toggled.connect(self.toggle_advanced_options)
        outer.addWidget(self.advanced_toggle)

        self.advanced_group = QGroupBox("Opcje zaawansowane")
        form = QFormLayout(self.advanced_group)
        self.seed_edit = QLineEdit(self.state.seed)
        self.dt_edit = QLineEdit(self.state.dt)
        self.auto_dt_check = QCheckBox("Automatyczny dobór dt")
        self.auto_dt_check.setChecked(self.state.auto_dt)
        self.auto_dt_check.toggled.connect(self.on_auto_dt_toggled)
        self.command_combo = QComboBox()
        self.command_combo.addItems(list(COMMAND_LABELS.values()))
        self.command_combo.setCurrentText(
            COMMAND_LABELS.get(self.state.command, self.state.command)
        )
        self.batch_seeds_edit = QLineEdit(self.state.batch_seeds)
        self.batch_scenarios_edit = QLineEdit(self.state.batch_scenarios)
        self.sensitivity_edit = QLineEdit(self.state.sensitivity_params)
        self.sensitivity_delta_edit = QLineEdit(self.state.sensitivity_delta)

        form.addRow("ziarno losowości", self.seed_edit)
        form.addRow("krok czasowy dt [s]", self.dt_edit)
        form.addRow(self.auto_dt_check)
        form.addRow("tryb uruchomienia", self.command_combo)
        form.addRow("ziarna serii", self.batch_seeds_edit)
        form.addRow("scenariusze serii", self.batch_scenarios_edit)
        form.addRow("parametry wrażliwości", self.sensitivity_edit)
        form.addRow("delta wrażliwości", self.sensitivity_delta_edit)
        outer.addWidget(self.advanced_group)
        self.toggle_advanced_options(False)
        self.on_auto_dt_toggled(self.state.auto_dt)
        return container

    def build_results_and_plots_section(self) -> QGroupBox:
        """Zbuduj sekcję „Wyniki i wykresy” z presetami i zwijanymi szczegółami."""
        group = QGroupBox("Wyniki i wykresy")
        layout = QVBoxLayout(group)
        if not self.state.plots:
            self.state.plots = dict(DEFAULT_PLOTS)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Zestaw wykresów:"))
        self.plot_preset_group = QButtonGroup(group)
        for preset_name in ("Podstawowe", "Diagnostyczne", "Pełne"):
            button = QRadioButton(preset_name)
            button.toggled.connect(lambda _checked: self.apply_plot_preset())
            self.plot_preset_group.addButton(button)
            self.plot_preset_buttons[preset_name] = button
            preset_row.addWidget(button)
        custom_button = QRadioButton("Niestandardowe", group)
        custom_button.setVisible(False)
        self.plot_preset_group.addButton(custom_button)
        self.plot_preset_buttons["Niestandardowe"] = custom_button
        preset_row.addStretch(1)
        layout.addLayout(preset_row)

        self.plot_preset_description = QLabel("")
        self.plot_preset_description.setObjectName("hintLabel")
        self.plot_preset_description.setWordWrap(True)
        layout.addWidget(self.plot_preset_description)

        self.plot_details_toggle = QToolButton()
        self.plot_details_toggle.setText("Dostosuj wykresy")
        self.plot_details_toggle.setCheckable(True)
        self.plot_details_toggle.setChecked(False)
        self.plot_details_toggle.toggled.connect(self.toggle_plot_details)
        layout.addWidget(self.plot_details_toggle)

        self.plot_details_group = QGroupBox("Szczegółowe wybory wykresów")
        details_layout = QHBoxLayout(self.plot_details_group)
        left = QVBoxLayout()
        right = QVBoxLayout()
        for index, (key, label) in enumerate(PLOT_LABELS.items()):
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.state.plots.get(key, DEFAULT_PLOTS[key]))
            checkbox.toggled.connect(self.sync_plot_preset_from_checks)
            self.plot_checks[key] = checkbox
            (left if index % 2 == 0 else right).addWidget(checkbox)
        left.addStretch(1)
        right.addStretch(1)
        details_layout.addLayout(left)
        details_layout.addLayout(right)
        layout.addWidget(self.plot_details_group)
        self.toggle_plot_details(False)
        self.sync_plot_preset_from_checks(mark_custom=False)
        return group

    def sync_state_from_controls(self) -> None:
        """Przepisz wartości widżetów Qt do stanu GUI."""
        self.state.T = self.T_edit.text()
        self.state.dt = self.dt_edit.text()
        self.state.auto_dt = self.auto_dt_check.isChecked()
        self.state.seed = self.seed_edit.text()
        self.state.command = COMMAND_VALUES.get(
            self.command_combo.currentText(), self.command_combo.currentText()
        )
        self.state.batch_seeds = self.batch_seeds_edit.text()
        self.state.batch_scenarios = self.batch_scenarios_edit.text()
        self.state.sensitivity_params = self.sensitivity_edit.text()
        self.state.sensitivity_delta = self.sensitivity_delta_edit.text()
        self.state.scenario = self.scenario_combo.currentText()
        self.state.save_results = self.save_results_check.isChecked()
        self.state.plots = {
            name: check.isChecked() for name, check in self.plot_checks.items()
        }

    def sync_controls_from_state(self) -> None:
        """Przepisz stan GUI do widżetów Qt po wczytaniu konfiguracji."""
        self.T_edit.setText(self.state.T)
        self.dt_edit.setText(self.state.dt)
        self.auto_dt_check.setChecked(self.state.auto_dt)
        self.seed_edit.setText(self.state.seed)
        self.command_combo.setCurrentText(
            COMMAND_LABELS.get(self.state.command, self.state.command)
        )
        self.batch_seeds_edit.setText(self.state.batch_seeds)
        self.batch_scenarios_edit.setText(self.state.batch_scenarios)
        self.sensitivity_edit.setText(self.state.sensitivity_params)
        self.sensitivity_delta_edit.setText(self.state.sensitivity_delta)
        self.scenario_combo.setCurrentText(self.state.scenario)
        self.save_results_check.setChecked(self.state.save_results)
        for name, value in self.state.plots.items():
            if name in self.plot_checks:
                checkbox = self.plot_checks[name]
                checkbox.blockSignals(True)
                checkbox.setChecked(value)
                checkbox.blockSignals(False)
        self.sync_plot_preset_from_checks(mark_custom=False)
        self.refresh_scenario_details()

    def refresh_scenario_details(self) -> None:
        """Odśwież opis aktualnie wybranego scenariusza."""
        scenario = get_scenario(self.scenario_combo.currentText())
        self.scenario_details_label.setText(f"{scenario.name}: {scenario.description}")

    def toggle_advanced_options(self, checked: bool) -> None:
        """Pokaż albo ukryj grupę opcji zaawansowanych."""
        if self.advanced_group is not None:
            self.advanced_group.setVisible(checked)

    def on_duration_changed(self) -> None:
        """Przelicz automatyczny krok dt po zmianie czasu symulacji."""
        if self.auto_dt_check.isChecked():
            self.on_auto_dt_toggled(True)

    def on_auto_dt_toggled(self, checked: bool) -> None:
        """Włącz lub wyłącz edycję kroku dt zależnie od automatycznego doboru."""
        self.dt_edit.setEnabled(not checked)
        if checked:
            try:
                duration = float(self.T_edit.text())
            except ValueError:
                return
            from .qt_runner import auto_dt_for_duration

            self.dt_edit.setText(str(auto_dt_for_duration(duration)))

    def toggle_plot_details(self, checked: bool) -> None:
        """Pokaż albo ukryj szczegółowe checkboxy wyboru wykresów."""
        if self.plot_details_group is not None:
            self.plot_details_group.setVisible(checked)

    def plot_preset_keys(self, preset_name: str) -> set[str]:
        """Zwróć zestaw wykresów aktywnych dla wskazanego presetu."""
        if preset_name == "Podstawowe":
            return {"activity", "behavior", "scenario_timeline"}
        if preset_name == "Diagnostyczne":
            return {
                "activity",
                "diagnostics",
                "behavior",
                "eeg",
                "band_power",
                "scenario_channels",
                "scenario_timeline",
            }
        if preset_name == "Pełne":
            return set(self.plot_checks)
        return {name for name, check in self.plot_checks.items() if check.isChecked()}

    def plot_preset_summary(self, preset_name: str) -> str:
        """Zwróć krótki polski opis aktywnego zestawu wykresów."""
        descriptions = {
            "Podstawowe": (
                "Aktywny zestaw: Podstawowe — pokazuje aktywacje, zachowanie "
                "i oś czasu scenariusza."
            ),
            "Diagnostyczne": (
                "Aktywny zestaw: Diagnostyczne — dodaje sygnały diagnostyczne, "
                "EEG, moc pasm i kanały bodźców."
            ),
            "Pełne": "Aktywny zestaw: Pełne — zapisuje wszystkie dostępne wykresy.",
            "Niestandardowe": (
                "Aktywny zestaw: Niestandardowe — używa ręcznie zaznaczonych wykresów."
            ),
        }
        return descriptions.get(preset_name, descriptions["Niestandardowe"])

    def set_plot_preset_label(self, preset_name: str) -> None:
        """Ustaw tekst opisu aktualnego presetu bez zmiany checkboxów."""
        if self.plot_preset_description is not None:
            self.plot_preset_description.setText(self.plot_preset_summary(preset_name))

    def apply_plot_preset(self) -> None:
        """Ustaw widoczność wykresów zgodnie z zaznaczonym presetem."""
        selected = self.plot_preset_group.checkedButton()
        if selected is None or not selected.isChecked():
            return
        preset_name = selected.text()
        if preset_name == "Niestandardowe":
            self.set_plot_preset_label(preset_name)
            return
        active = self.plot_preset_keys(preset_name)
        for name, checkbox in self.plot_checks.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(name in active)
            checkbox.blockSignals(False)
        self.set_plot_preset_label(preset_name)
        self.sync_state_from_controls()

    def sync_plot_preset_from_checks(
        self, *_signal_args: object, mark_custom: bool = True
    ) -> None:
        """Dopasuj opis presetu po odczycie stanu albo oznacz ręczne wybory jako własne."""
        active = {name for name, check in self.plot_checks.items() if check.isChecked()}
        selected_preset = "Niestandardowe"
        if not mark_custom:
            for preset_name in ("Podstawowe", "Diagnostyczne", "Pełne"):
                if active == self.plot_preset_keys(preset_name):
                    selected_preset = preset_name
                    break

        button = self.plot_preset_buttons[selected_preset]
        button.blockSignals(True)
        button.setChecked(True)
        button.blockSignals(False)
        self.set_plot_preset_label(selected_preset)
        self.sync_state_from_controls()
