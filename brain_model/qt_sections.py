"""Sekcje formularza PySide6 dla konfiguracji i wyboru wyników."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .gui_forms import COMMAND_LABELS, COMMAND_VALUES, PARAMETER_DESCRIPTIONS
from .gui_state import GuiState
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


ControlKind = Literal["line_edit", "check_box", "combo_box"]


@dataclass(frozen=True)
class ControlBinding:
    """Opisuje jawne powiązanie pola stanu z kontrolką formularza Qt.

    Parameters
    ----------
    state_field:
        Nazwa pola w `GuiState`, które jest synchronizowane z kontrolką.
    control_name:
        Nazwa atrybutu `QtSections` przechowującego kontrolkę Qt.
    control_kind:
        Typ kontrolki obsługiwany przez proste funkcje odczytu i zapisu.
    """

    state_field: str
    control_name: str
    control_kind: ControlKind


def read_line_edit(control: QLineEdit) -> str:
    """Odczytaj tekst z pola `QLineEdit` bez dodatkowej interpretacji.

    Parameters
    ----------
    control:
        Kontrolka tekstowa edytowana przez użytkownika.

    Returns
    -------
    str
        Aktualna wartość tekstowa kontrolki.
    """

    return control.text()


def write_line_edit(control: QLineEdit, value: object) -> None:
    """Zapisz wartość tekstową do pola `QLineEdit`.

    Parameters
    ----------
    control:
        Kontrolka tekstowa aktualizowana ze stanu GUI.
    value:
        Wartość ze stanu GUI zapisywana jako tekst.
    """

    control.setText(str(value))


def read_check_box(control: QCheckBox) -> bool:
    """Odczytaj stan zaznaczenia kontrolki `QCheckBox`.

    Parameters
    ----------
    control:
        Kontrolka przechowująca wybór logiczny użytkownika.

    Returns
    -------
    bool
        `True`, gdy kontrolka jest zaznaczona.
    """

    return control.isChecked()


def write_check_box(control: QCheckBox, value: object) -> None:
    """Zapisz wartość logiczną do kontrolki `QCheckBox`.

    Parameters
    ----------
    control:
        Kontrolka przechowująca wybór logiczny użytkownika.
    value:
        Wartość ze stanu GUI interpretowana jako `bool`.
    """

    control.setChecked(bool(value))


def read_combo_box(control: QComboBox) -> str:
    """Odczytaj aktualny tekst z kontrolki `QComboBox`.

    Parameters
    ----------
    control:
        Lista wyboru prezentowana użytkownikowi.

    Returns
    -------
    str
        Aktualnie wybrany tekst kontrolki.
    """

    return control.currentText()


def write_combo_box(control: QComboBox, value: object) -> None:
    """Ustaw aktualny tekst kontrolki `QComboBox`.

    Parameters
    ----------
    control:
        Lista wyboru aktualizowana ze stanu GUI.
    value:
        Tekst, który powinien stać się aktywnym wyborem.
    """

    control.setCurrentText(str(value))


CONTROL_BINDINGS: dict[str, tuple[ControlBinding, ...]] = {
    "quick_start": (
        ControlBinding("scenario", "scenario_combo", "combo_box"),
        ControlBinding("T", "T_edit", "line_edit"),
        ControlBinding("save_results", "save_results_check", "check_box"),
    ),
    "advanced_options": (
        ControlBinding("seed", "seed_edit", "line_edit"),
        ControlBinding("dt", "dt_edit", "line_edit"),
        ControlBinding("auto_dt", "auto_dt_check", "check_box"),
        ControlBinding("command", "command_combo", "combo_box"),
        ControlBinding("batch_seeds", "batch_seeds_edit", "line_edit"),
        ControlBinding("batch_scenarios", "batch_scenarios_edit", "line_edit"),
        ControlBinding("sensitivity_params", "sensitivity_edit", "line_edit"),
        ControlBinding("sensitivity_delta", "sensitivity_delta_edit", "line_edit"),
    ),
}

GUI_STATE_CONTROL_OMISSIONS = {
    "brain_params": "edytowane w osobnym dialogu parametrów globalnych modelu",
    "oscillator_params": "edytowane w osobnym dialogu parametrów oscylatorów",
    "plots": "dynamiczne checkboxy tworzone na podstawie PLOT_LABELS",
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

    def __init__(self, state: GuiState, callbacks: dict[str, Any]) -> None:
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

        suggested_duration_button = QPushButton("Użyj sugerowanego czasu")
        suggested_duration_button.clicked.connect(self.apply_suggested_duration)
        layout.addRow(suggested_duration_button)

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

    def _read_bound_control(self, binding: ControlBinding) -> object:
        """Odczytaj wartość kontrolki opisanej przez jawne mapowanie.

        Parameters
        ----------
        binding:
            Powiązanie pola `GuiState` z atrybutem kontrolki Qt.

        Returns
        -------
        object
            Wartość gotowa do zapisania w polu stanu GUI.
        """

        control = getattr(self, binding.control_name)
        if binding.control_kind == "line_edit":
            return read_line_edit(control)
        if binding.control_kind == "check_box":
            return read_check_box(control)
        if binding.control_kind == "combo_box":
            value = read_combo_box(control)
            if binding.state_field == "command":
                return COMMAND_VALUES.get(value, value)
            return value
        raise ValueError(f"Nieobsługiwany typ kontrolki: {binding.control_kind}")

    def _write_bound_control(self, binding: ControlBinding) -> None:
        """Zapisz wartość pola `GuiState` do kontrolki z jawnego mapowania.

        Parameters
        ----------
        binding:
            Powiązanie pola `GuiState` z atrybutem kontrolki Qt.
        """

        control = getattr(self, binding.control_name)
        value = getattr(self.state, binding.state_field)
        if binding.state_field == "command":
            value = COMMAND_LABELS.get(value, value)
        if binding.control_kind == "line_edit":
            write_line_edit(control, value)
            return
        if binding.control_kind == "check_box":
            write_check_box(control, value)
            return
        write_combo_box(control, value)

    def _sync_state_from_binding_group(self, group_name: str) -> None:
        """Przepisz wartości jednej grupy kontrolek Qt do stanu GUI.

        Parameters
        ----------
        group_name:
            Nazwa sekcji w `CONTROL_BINDINGS`.
        """

        for binding in CONTROL_BINDINGS[group_name]:
            setattr(self.state, binding.state_field, self._read_bound_control(binding))

    def _sync_controls_from_binding_group(self, group_name: str) -> None:
        """Przepisz wartości jednej grupy pól stanu GUI do kontrolek Qt.

        Parameters
        ----------
        group_name:
            Nazwa sekcji w `CONTROL_BINDINGS`.
        """

        for binding in CONTROL_BINDINGS[group_name]:
            self._write_bound_control(binding)

    def sync_quick_start_state_from_controls(self) -> None:
        """Zsynchronizuj podstawowe pola szybkiego startu do `GuiState`."""

        self._sync_state_from_binding_group("quick_start")

    def sync_quick_start_controls_from_state(self) -> None:
        """Zsynchronizuj podstawowe pola szybkiego startu ze stanu GUI."""

        self._sync_controls_from_binding_group("quick_start")

    def sync_advanced_options_state_from_controls(self) -> None:
        """Zsynchronizuj opcje zaawansowane do `GuiState`."""

        self._sync_state_from_binding_group("advanced_options")

    def sync_advanced_options_controls_from_state(self) -> None:
        """Zsynchronizuj opcje zaawansowane ze stanu GUI."""

        self._sync_controls_from_binding_group("advanced_options")

    def sync_plot_selection_state_from_controls(self) -> None:
        """Zsynchronizuj wybór wykresów z checkboxów do `GuiState`."""

        self.state.plots = {
            name: read_check_box(check) for name, check in self.plot_checks.items()
        }

    def sync_plot_selection_controls_from_state(self) -> None:
        """Zsynchronizuj checkboxy wyboru wykresów ze stanu GUI."""

        for name, value in self.state.plots.items():
            if name in self.plot_checks:
                checkbox = self.plot_checks[name]
                checkbox.blockSignals(True)
                write_check_box(checkbox, value)
                checkbox.blockSignals(False)

    def sync_state_from_controls(self) -> None:
        """Przepisz wartości widżetów Qt do stanu GUI."""

        self.sync_quick_start_state_from_controls()
        self.sync_advanced_options_state_from_controls()
        self.sync_plot_selection_state_from_controls()

    def sync_controls_from_state(self) -> None:
        """Przepisz stan GUI do widżetów Qt po wczytaniu konfiguracji."""

        self.sync_quick_start_controls_from_state()
        self.sync_advanced_options_controls_from_state()
        self.sync_plot_selection_controls_from_state()
        self.sync_plot_preset_from_checks(mark_custom=False)
        self.refresh_scenario_details()

    def refresh_scenario_details(self) -> None:
        """Odśwież opis aktualnie wybranego scenariusza."""
        scenario = get_scenario(self.scenario_combo.currentText())
        self.scenario_details_label.setText(f"{scenario.name}: {scenario.description}")

    def apply_suggested_duration(self) -> None:
        """Ustaw czas symulacji zgodnie z podpowiedzią wybranego scenariusza."""
        current_scenario_id = self.scenario_combo.currentText()
        scenario = get_scenario(current_scenario_id)
        if scenario.duration_hint is None:
            status_callback = self.callbacks.get("show_status")
            if status_callback is not None:
                status_callback("Wybrany scenariusz nie ma sugerowanego czasu.")
            return
        write_line_edit(self.T_edit, scenario.duration_hint)
        if read_check_box(self.auto_dt_check):
            self.on_auto_dt_toggled(True)
        self.state.T = read_line_edit(self.T_edit)
        self.state.dt = read_line_edit(self.dt_edit)
        status_callback = self.callbacks.get("show_status")
        if status_callback is not None:
            status_callback("Ustawiono sugerowany czas scenariusza.")

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
            return {
                "activity",
                "behavior",
                "simulated_brain_activity",
                "scenario_timeline",
            }
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
                "Aktywny zestaw: Podstawowe — Najważniejsze wykresy do pierwszej "
                "interpretacji wyniku."
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
