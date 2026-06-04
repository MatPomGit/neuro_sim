"""Osadzanie wykresów Matplotlib w interfejsie PySide6."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .gui_state import GuiState
from .plotting import (
    draw_activity_with_stimulus_channels,
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


def _get_min_positive_activity_value(activity_axis: Any) -> float | None:
    """Zwróć minimalną dodatnią wartość spośród widocznych sygnałów aktywacji."""
    import numpy as np

    min_val = None
    for line in activity_axis.get_lines():
        if not line.get_visible():
            continue
        ydata = np.asarray(line.get_ydata())
        pos_ydata = ydata[ydata > 0]
        if pos_ydata.size > 0:
            local_min = float(pos_ydata.min())
            if min_val is None or local_min < min_val:
                min_val = local_min
    return min_val


def _create_activity_controls(canvas: Any, axes: list[Any]) -> QWidget:
    """Utwórz polskie kontrolki autoskalowania i skali Y dla wykresu aktywacji."""
    activity_axis = axes[0]
    controls = QWidget()
    layout = QHBoxLayout(controls)
    layout.setContentsMargins(6, 4, 6, 4)

    autoscale_button = QPushButton("Autoskaluj Y aktywacji")
    scale_button = QPushButton("Skala Y: liniowa")

    def autoscale_activity_y() -> None:
        current_xlim = activity_axis.get_xlim()
        activity_axis.relim()
        activity_axis.autoscale_view(scalex=False, scaley=True)
        activity_axis.set_xlim(current_xlim)
        canvas.draw_idle()

    def toggle_activity_y_scale() -> None:
        current_xlim = activity_axis.get_xlim()
        if activity_axis.get_yscale() == "linear":
            min_positive = _get_min_positive_activity_value(activity_axis)
            if min_positive is None:
                QMessageBox.warning(
                    controls,
                    "Skala logarytmiczna",
                    "Nie można włączyć skali logarytmicznej: "
                    "brak dodatnich wartości aktywacji.",
                )
                return
            activity_axis.set_ylim(bottom=min_positive * 0.5)
            activity_axis.set_yscale("log")
            scale_button.setText("Skala Y: logarytmiczna")
        else:
            activity_axis.set_yscale("linear")
            scale_button.setText("Skala Y: liniowa")
            activity_axis.relim()
            activity_axis.autoscale_view(scalex=False, scaley=True)
        activity_axis.set_xlim(current_xlim)
        canvas.draw_idle()

    autoscale_button.clicked.connect(autoscale_activity_y)
    scale_button.clicked.connect(toggle_activity_y_scale)
    layout.addWidget(autoscale_button)
    layout.addWidget(scale_button)
    layout.addStretch(1)
    return controls


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
            draw_activity_with_stimulus_channels,
            time,
            activity,
            model.names,
            model.idx,
            get_scenario(state.scenario),
            figsize=(11, 7),
            controls_factory=_create_activity_controls,
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
            "Diagnostyka", draw_diagnostics, time, diagnostics, figsize=(11, 7)
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


class ObservationPanel(QWidget):
    """Panel nauczyciela „Co obserwujesz?” oparty wyłącznie na wynikach silnika."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz panel syntetyzujący oś czasu, profil kliniczny i raport roving oddball."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = QGroupBox("Co obserwujesz?")
        group_layout = QVBoxLayout(group)
        hint = QLabel(
            "Wskazówki są budowane z `event_timeline`, `clinical_profile` oraz "
            "sekcji `roving_oddball` raportu zwróconego przez run_experiment()."
        )
        hint.setWordWrap(True)
        group_layout.addWidget(hint)
        self.summary_label = QLabel("Uruchom symulację, aby zobaczyć obserwacje.")
        self.summary_label.setWordWrap(True)
        group_layout.addWidget(self.summary_label)
        layout.addWidget(group)
        layout.addStretch(1)

    def set_context(
        self,
        events: list[dict[str, Any]],
        clinical_profile: dict[str, Any],
        analysis_report: dict[str, Any],
    ) -> None:
        """Zaktualizuj obserwacje nauczyciela na podstawie gotowych artefaktów.

        Parameters
        ----------
        events:
            Oś czasu zdarzeń zwrócona przez silnik w polu `event_timeline`.
        clinical_profile:
            Profil kliniczny odczytany z YAML albo wyniku `run_experiment()`.
        analysis_report:
            Raport analityczny zwrócony przez silnik, bez odtwarzania logiki tasków.
        """
        roving_report = analysis_report.get("roving_oddball", {})
        observations = self._build_observations(events, clinical_profile, roving_report)
        self.summary_label.setText("\n".join(f"• {item}" for item in observations))

    def _build_observations(
        self,
        events: list[dict[str, Any]],
        clinical_profile: dict[str, Any],
        roving_report: dict[str, Any],
    ) -> list[str]:
        """Zbuduj krótkie polskie obserwacje z gotowych wyników eksperymentu."""
        observations: list[str] = []
        if events:
            event_types = sorted(
                {str(event.get("event_type", "n/a")) for event in events}
            )
            observations.append(
                f"Oś czasu zawiera {len(events)} zdarzeń: {', '.join(event_types)}."
            )
        else:
            observations.append("Oś czasu zdarzeń jest pusta dla bieżącego wyniku.")

        profile_name = clinical_profile.get("display_name") or clinical_profile.get(
            "id"
        )
        if profile_name:
            mechanism = clinical_profile.get("mechanism", "brak opisu mechanizmu")
            observations.append(
                f"Profil kliniczny: {profile_name}; mechanizm: {mechanism}"
            )

        if roving_report:
            observations.append(
                "Roving oddball: standardy={standard}, dewianty={deviant}, "
                "nowe standardy={new_standard}.".format(
                    standard=roving_report.get("standard_count", "n/a"),
                    deviant=roving_report.get("deviant_count", "n/a"),
                    new_standard=roving_report.get("new_standard_count", "n/a"),
                )
            )
            observations.append(
                "Habituacja={habituation}, średnia latencja readaptacji={latency}.".format(
                    habituation=roving_report.get("habituation_rate", "n/a"),
                    latency=roving_report.get("mean_readaptation_latency", "n/a"),
                )
            )
        return observations


class RovingOddballQuestionsPanel(QWidget):
    """Panel pytań kontrolnych dla lekcji roving oddball z odpowiedziami z raportu."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz tabelę pytań o standard, dewiant, habituację i readaptację."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        hint = QLabel(
            "Pytania kontrolne korzystają z gotowej sekcji `roving_oddball` raportu; "
            "GUI nie rekonstruuje sekwencji bodźców ani reguł protokołu."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["pytanie", "odpowiedź z raportu"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.set_report({})

    def set_report(self, analysis_report: dict[str, Any] | None) -> None:
        """Odśwież odpowiedzi kontrolne na podstawie raportu run_experiment().

        Parameters
        ----------
        analysis_report:
            Raport analityczny zwrócony przez silnik symulacji.
        """
        safe_report = analysis_report or {}
        roving_report = safe_report.get("roving_oddball", {})
        rows = self._question_rows(roving_report)
        self.table.setRowCount(len(rows))
        for row, (question, answer) in enumerate(rows):
            for column, value in enumerate((question, answer)):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()

    def _question_rows(self, roving_report: dict[str, Any]) -> list[tuple[str, str]]:
        """Zwróć stały zestaw pytań z odpowiedziami wypełnionymi metrykami raportu."""
        if not roving_report:
            return [
                (
                    "Co jest standardem, dewiantem, habituacją i readaptacją?",
                    "Uruchom lekcję roving oddball, aby wypełnić odpowiedzi.",
                )
            ]
        return [
            (
                "Który bodziec pełni rolę standardu?",
                f"Raport zliczył {roving_report.get('standard_count', 'n/a')} standardów.",
            ),
            (
                "Który bodziec jest dewiantem?",
                f"Raport zliczył {roving_report.get('deviant_count', 'n/a')} dewiantów.",
            ),
            (
                "Po czym rozpoznasz habituację?",
                f"Tempo habituacji w raporcie: {roving_report.get('habituation_rate', 'n/a')}.",
            ),
            (
                "Po czym rozpoznasz readaptację po zmianie standardu?",
                "Nowe standardy={new_standard}; średnia latencja readaptacji={latency}.".format(
                    new_standard=roving_report.get("new_standard_count", "n/a"),
                    latency=roving_report.get("mean_readaptation_latency", "n/a"),
                ),
            ),
        ]
