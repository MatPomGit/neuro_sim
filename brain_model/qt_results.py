"""Osadzanie wykresów Matplotlib w interfejsie PySide6."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .gui_state import GuiState
from .plotting import (
    draw_activity,
    draw_band_power,
    draw_behavior,
    draw_brain_region_projections,
    draw_diagnostics,
    draw_eeg_modules,
    draw_region_activity_2d,
    draw_scenario_channels,
    draw_scenario_timeline,
    draw_simulated_brain_activity,
    draw_weight_deltas,
    draw_weight_trajectories,
)
from .qt_plotting import QtPlotPanel
from .scenarios import get_scenario


def apply_run_result(
    plot_panel: QtPlotPanel, state: GuiState, payload: tuple[Any, ...]
) -> bool:
    """Przenieś wynik symulacji do panelu Qt i zwróć informację, czy dodano wykresy."""
    _, _, _, model, time, activity, diagnostics, oscillations, behavior, *_ = payload
    plot_panel.clear()
    return add_selected_plots_to_panel(
        plot_panel, state, model, time, activity, diagnostics, oscillations, behavior
    )


def add_selected_plots_to_panel(
    plot_panel: QtPlotPanel,
    state: GuiState,
    model: Any,
    time: Any,
    activity: Any,
    diagnostics: Any,
    oscillations: Any,
    behavior: Any,
) -> bool:
    """Dodaj do panelu Qt tylko wykresy wybrane przez użytkownika."""
    has_plots = False
    if state.plots.get("activity", False):
        plot_panel.add_plot(
            "Aktywacje",
            draw_activity,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 7),
        )
        has_plots = True
    if state.plots.get("simulated_brain_activity", False):
        plot_panel.add_plot(
            "Aktywność mózgu",
            draw_simulated_brain_activity,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 7),
        )
        has_plots = True
    if state.plots.get("brain_region_projections", False):
        plot_panel.add_plot(
            "Rzuty mózgu SVG",
            draw_brain_region_projections,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 8),
        )
        has_plots = True
    if state.plots.get("region_activity_2d", False):
        plot_panel.add_plot(
            "Regiony 2D w czasie",
            draw_region_activity_2d,
            time,
            activity,
            model.names,
            model.idx,
            figsize=(11, 8),
        )
        has_plots = True
    if state.plots.get("diagnostics", False):
        plot_panel.add_plot(
            "Diagnostyka", draw_diagnostics, time, diagnostics, figsize=(11, 5)
        )
        has_plots = True
    if state.plots.get("behavior", False):
        plot_panel.add_plot(
            "Zachowanie", draw_behavior, time, behavior, figsize=(11, 5)
        )
        has_plots = True
    if state.plots.get("eeg", False):
        plot_panel.add_plot(
            "EEG modułów",
            draw_eeg_modules,
            time,
            oscillations,
            model.names,
            model.idx,
            figsize=(11, 6),
        )
        has_plots = True
    if state.plots.get("band_power", False):
        plot_panel.add_plot(
            "Moc pasm", draw_band_power, time, oscillations, figsize=(11, 8)
        )
        has_plots = True
    if state.plots.get("weight_trajectories", False):
        plot_panel.add_plot(
            "Trajektorie wag",
            draw_weight_trajectories,
            time,
            diagnostics,
            figsize=(11, 5),
        )
        has_plots = True
    if state.plots.get("weight_deltas", False):
        plot_panel.add_plot(
            "Przyrosty wag", draw_weight_deltas, time, diagnostics, figsize=(11, 5)
        )
        has_plots = True
    if state.plots.get("scenario_channels", False):
        plot_panel.add_plot(
            "Kanały scenariusza",
            draw_scenario_channels,
            time,
            get_scenario(state.scenario),
            figsize=(11, 5),
        )
        has_plots = True
    if state.plots.get("scenario_timeline", False):
        plot_panel.add_plot(
            "Oś czasu scenariusza",
            draw_scenario_timeline,
            time,
            get_scenario(state.scenario),
            figsize=(11, 4),
        )
        has_plots = True
    return has_plots


class EventTimelinePanel(QWidget):
    """Panel podglądu osi czasu zdarzeń z filtrem typu zdarzenia."""

    ALL_EVENTS_LABEL = "Wszystkie typy zdarzeń"

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz tabelaryczny panel zdarzeń dla wyników zwróconych przez silnik."""
        super().__init__(parent)
        self.events: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        hint = QLabel(
            "Oś czasu pochodzi z `event_timeline` wygenerowanego przez silnik "
            "brain_core; filtr ogranicza widok do wybranego typu zdarzenia."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.event_type_filter = QComboBox()
        self.event_type_filter.currentTextChanged.connect(self.refresh_table)
        layout.addWidget(self.event_type_filter)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["czas [s]", "typ", "etykieta", "źródło", "opis"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)
        self.set_events([])

    def set_events(self, events: list[dict[str, Any]]) -> None:
        """Zapisz zdarzenia z wyniku silnika i odbuduj listę typów filtrowania."""
        self.events = list(events)
        current_filter = self.event_type_filter.currentText() or self.ALL_EVENTS_LABEL
        self.event_type_filter.blockSignals(True)
        self.event_type_filter.clear()
        self.event_type_filter.addItem(self.ALL_EVENTS_LABEL)
        for event_type in sorted(
            {str(event.get("event_type", "n/a")) for event in self.events}
        ):
            self.event_type_filter.addItem(event_type)
        if current_filter:
            self.event_type_filter.setCurrentText(current_filter)
        self.event_type_filter.blockSignals(False)
        self.refresh_table()

    def refresh_table(self) -> None:
        """Odśwież widoczne wiersze zgodnie z aktualnym filtrem typu zdarzenia."""
        selected_type = self.event_type_filter.currentText()
        visible_events = [
            event
            for event in self.events
            if selected_type in {"", self.ALL_EVENTS_LABEL}
            or str(event.get("event_type", "n/a")) == selected_type
        ]
        self.table.setRowCount(len(visible_events))
        for row, event in enumerate(visible_events):
            values = [
                event.get("time_s", "n/a"),
                event.get("event_type", "n/a"),
                event.get("label_pl", "n/a"),
                event.get("source", "n/a"),
                event.get("description_pl", "n/a"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()


class ClinicalProfilePanel(QWidget):
    """Panel metadanych profilu klinicznego użytego w konfiguracji eksperymentu."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz panel pól mechanism, affected_regions i cognitive_functions."""
        super().__init__(parent)
        self.labels: dict[str, QLabel] = {}
        layout = QVBoxLayout(self)
        group = QGroupBox("Profil kliniczny")
        form = QFormLayout(group)
        for key, label_text in (
            ("display_name", "nazwa"),
            ("mechanism", "mechanizm"),
            ("affected_regions", "regiony objęte zmianą"),
            ("cognitive_functions", "funkcje poznawcze"),
        ):
            value_label = QLabel("n/a")
            value_label.setWordWrap(True)
            self.labels[key] = value_label
            form.addRow(label_text, value_label)
        layout.addWidget(group)
        layout.addStretch(1)
        self.set_profile({})

    def set_profile(self, profile: dict[str, Any]) -> None:
        """Pokaż metadane profilu klinicznego zwrócone przez konfigurację lub silnik."""
        for key, label in self.labels.items():
            value = profile.get(key, "n/a")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value) or "brak"
            label.setText(str(value))
