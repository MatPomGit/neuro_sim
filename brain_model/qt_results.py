"""Osadzanie wykresów Matplotlib w interfejsie PySide6."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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

from brain_core.analysis.reports import build_trial_observation_rows

from .gui_labels import EDUCATIONAL_LIMITATION_TEXT_PL
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

GLOSSARY_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "english_polish_glossary.md"
)


class EducationalLimitationLabel(QLabel):
    """Etykieta wspólnego ograniczenia interpretacyjnego wyników."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz zawijaną etykietę z jednolitym komunikatem edukacyjnym."""
        super().__init__(EDUCATIONAL_LIMITATION_TEXT_PL, parent)
        self.setWordWrap(True)


def _load_glossary_terms() -> dict[str, tuple[str, str]]:
    """Wczytaj polskie etykiety i konteksty z dokumentu słownika EN→PL.

    Returns
    -------
    dict[str, tuple[str, str]]
        Mapowanie nazwy technicznej na parę: polska etykieta, kontekst użycia.
    """
    terms: dict[str, tuple[str, str]] = {}
    try:
        lines = GLOSSARY_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return terms
    for line in lines:
        cleaned_line = line.strip()
        if (
            not cleaned_line.startswith("|")
            or "---" in cleaned_line
            or "English" in cleaned_line
        ):
            continue
        cells = [cell.strip() for cell in cleaned_line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        english_name, polish_label, usage_context = cells
        if english_name and polish_label:
            terms[english_name] = (polish_label, usage_context)
    return terms


def _glossary_label(terms: dict[str, tuple[str, str]], key: str) -> str:
    """Zwróć polską etykietę terminu ze słownika albo nazwę techniczną."""
    return terms.get(key, (key, ""))[0]


def _glossary_context(terms: dict[str, tuple[str, str]], key: str) -> str:
    """Zwróć kontekst terminu ze słownika używany jako krótkie objaśnienie."""
    return terms.get(key, (key, "brak opisu w słowniku"))[1]


METRIC_WARNING_GROUPS = {
    "EEG": (
        "band_power_delta",
        "band_power_theta",
        "band_power_alpha",
        "band_power_beta",
        "band_power_gamma",
        "erp_proxy_peak_to_peak",
        "phase_locking_value",
        "connectivity_mean",
        "connectivity_abs_mean",
        "pli_proxy_mean",
        "region_strength_mean",
        "directional_mean",
        "directional_abs_mean",
        "outgoing_mean",
    ),
    "BOLD": ("fmri_mean", "bold_peak_to_peak"),
    "behavior": ("behavior_mean", "behavior_std"),
}
METRIC_WARNING_TEXT_PL = {
    "EEG": (
        "Metryki EEG są opisem symulacji i benchmarku technicznego; nie są "
        "zapisem pacjenta ani podstawą rozpoznania klinicznego."
    ),
    "BOLD": (
        "Metryki BOLD pokazują syntetyczną odpowiedź hemodynamiczną modelu; "
        "nie zastępują analizy fMRI ani interpretacji lekarskiej."
    ),
    "behavior": (
        "Metryki behawioralne mają charakter edukacyjny; nie są normą "
        "psychometryczną ani wynikiem diagnostycznym."
    ),
}


def _metric_educational_warnings(
    analysis_report: dict[str, Any], terms: dict[str, tuple[str, str]]
) -> list[str]:
    """Zbuduj krótkie ostrzeżenia edukacyjne dla widocznych grup metryk.

    Parameters
    ----------
    analysis_report:
        Raport analityczny zwrócony przez silnik symulacji.
    terms:
        Słownik EN→PL używany do spójnych nazw metryk w interfejsie.

    Returns
    -------
    list[str]
        Lista ostrzeżeń po polsku, bez sugestii diagnozy klinicznej.
    """
    metrics = analysis_report.get("metrics", {}) if analysis_report else {}
    if not isinstance(metrics, dict) or not metrics:
        return ["Uruchom analizę, aby zobaczyć ostrzeżenia przy metrykach."]

    warnings: list[str] = []
    for group_name, metric_names in METRIC_WARNING_GROUPS.items():
        present_metrics = [name for name in metric_names if name in metrics]
        if not present_metrics:
            continue
        labels = ", ".join(
            _glossary_label(terms, metric_name) for metric_name in present_metrics[:3]
        )
        if len(present_metrics) > 3:
            labels = f"{labels} i inne"
        warnings.append(
            f"{group_name}: {labels}. {METRIC_WARNING_TEXT_PL.get(group_name, '')}"
        )
    return warnings


def _extract_tones(
    roving_report: dict[str, Any],
    condition: str | None = None,
    is_new_standard: bool | None = None,
) -> str:
    """Wypisz unikalne tony z sygnatury sekwencji raportu roving oddball.

    Parameters
    ----------
    roving_report:
        Sekcja `roving_oddball` raportu analitycznego zwrócona przez silnik.
    condition:
        Opcjonalny warunek triala, np. `standard` albo `deviant`.
    is_new_standard:
        Opcjonalny filtr triali oznaczonych jako nowy standard po dewiancie.

    Returns
    -------
    str
        Lista maksymalnie czterech unikalnych tonów w Hz albo `n/a`, gdy raport
        nie zawiera pasujących danych.
    """

    signature = roving_report.get("sequence_signature", [])
    if not isinstance(signature, list):
        return "n/a"

    tones: list[Any] = []
    for item in signature:
        if not isinstance(item, dict):
            continue
        if condition is not None and item.get("condition") != condition:
            continue
        if (
            is_new_standard is not None
            and item.get("is_new_standard") is not is_new_standard
        ):
            continue
        tone_hz = item.get("tone_hz")
        if tone_hz is not None and tone_hz != "n/a" and tone_hz not in tones:
            tones.append(tone_hz)

    if not tones:
        return "n/a"
    return ", ".join(f"{tone} Hz" for tone in tones[:4])


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
    """Utwórz polskie kontrolki widoczności, zoomu i skali Y dla aktywacji."""
    activity_axis = axes[0]
    stimulus_axis = axes[1] if len(axes) > 1 else None
    controls = QWidget()
    layout = QHBoxLayout(controls)
    layout.setContentsMargins(6, 4, 6, 4)

    zoom_in_button = QPushButton("Przybliż")
    zoom_out_button = QPushButton("Oddal")
    autoscale_button = QPushButton("Autoskaluj Y aktywacji")
    full_autoscale_button = QPushButton("Autoskaluj wykres")
    scale_button = QPushButton("Skala Y: liniowa")

    def apply_activity_xlim(left: float, right: float) -> None:
        """Ustaw ten sam zakres czasu dla aktywacji i kanałów bodźców."""
        activity_axis.set_xlim(left, right)
        if stimulus_axis is not None:
            stimulus_axis.set_xlim(left, right)

    def zoom_activity_time(scale_factor: float) -> None:
        """Przybliż lub oddal oś czasu względem środka aktualnego widoku."""
        data_left, data_right = activity_axis.dataLim.intervalx
        left, right = activity_axis.get_xlim()
        width = right - left
        data_width = data_right - data_left
        if width <= 0 or data_width <= 0:
            return

        new_width = min(data_width, max(width * scale_factor, 1e-9))
        center = (left + right) / 2.0
        new_left = center - new_width / 2.0
        new_right = center + new_width / 2.0
        if new_left < data_left:
            new_left = data_left
            new_right = data_left + new_width
        if new_right > data_right:
            new_right = data_right
            new_left = data_right - new_width
        apply_activity_xlim(float(new_left), float(new_right))
        canvas.draw_idle()

    def autoscale_activity_y() -> None:
        current_xlim = activity_axis.get_xlim()
        activity_axis.relim(visible_only=True)
        activity_axis.autoscale_view(scalex=False, scaley=True)
        activity_axis.set_xlim(current_xlim)
        canvas.draw_idle()

    def autoscale_activity_plot() -> None:
        activity_axis.set_yscale("linear")
        scale_button.setText("Skala Y: liniowa")
        activity_axis.relim(visible_only=True)
        activity_axis.autoscale_view(scalex=True, scaley=True)
        if stimulus_axis is not None:
            stimulus_axis.relim()
            stimulus_axis.autoscale_view(scalex=False, scaley=True)
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
            activity_axis.relim(visible_only=True)
            activity_axis.autoscale_view(scalex=False, scaley=True)
        activity_axis.set_xlim(current_xlim)
        canvas.draw_idle()

    def set_signal_visibility(signal_line: Any, is_visible: bool) -> None:
        """Włącz lub wyłącz pojedynczy sygnał aktywacji na wykresie."""
        signal_line.set_visible(is_visible)
        autoscale_activity_y()

    zoom_in_button.clicked.connect(lambda: zoom_activity_time(0.75))
    zoom_out_button.clicked.connect(lambda: zoom_activity_time(1.25))
    autoscale_button.clicked.connect(autoscale_activity_y)
    full_autoscale_button.clicked.connect(autoscale_activity_plot)
    scale_button.clicked.connect(toggle_activity_y_scale)

    layout.addWidget(zoom_in_button)
    layout.addWidget(zoom_out_button)
    layout.addWidget(autoscale_button)
    layout.addWidget(full_autoscale_button)
    layout.addWidget(scale_button)

    for signal_line in activity_axis.get_lines():
        signal_label = signal_line.get_label()
        if not signal_label or signal_label.startswith("_"):
            continue
        checkbox = QCheckBox(signal_label)
        checkbox.setChecked(signal_line.get_visible())
        checkbox.toggled.connect(
            lambda is_visible, line=signal_line: set_signal_visibility(line, is_visible)
        )
        layout.addWidget(checkbox)

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
            figsize=(13, 9.5),
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
            "Zachowanie", draw_behavior, time, behavior, figsize=(11, 7)
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
    """Panel nauczyciela z obserwacjami i znaczeniem pojęć ze słownika EN→PL."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz panel syntetyzujący artefakty silnika oraz opisy słownikowe."""
        super().__init__(parent)
        self.glossary_terms = _load_glossary_terms()
        layout = QVBoxLayout(self)
        observation_group = QGroupBox("Co obserwujesz?")
        observation_group.setToolTip(
            "Co obserwujesz? Zobacz bieżące artefakty silnika."
        )
        observation_layout = QVBoxLayout(observation_group)
        hint = QLabel(
            "Wskazówki są budowane z `event_timeline`, `clinical_profile` oraz "
            "sekcji `roving_oddball` raportu zwróconego przez run_experiment()."
        )
        hint.setWordWrap(True)
        observation_layout.addWidget(hint)
        self.summary_label = QLabel("Uruchom symulację, aby zobaczyć obserwacje.")
        self.summary_label.setWordWrap(True)
        observation_layout.addWidget(self.summary_label)

        importance_group = QGroupBox("Dlaczego to ważne?")
        importance_layout = QVBoxLayout(importance_group)
        self.importance_label = QLabel(
            "Panel używa polskich nazw i kontekstów z `docs/english_polish_glossary.md`."
        )
        self.importance_label.setWordWrap(True)
        importance_layout.addWidget(self.importance_label)

        warnings_group = QGroupBox("Ostrzeżenia edukacyjne przy metrykach")
        warnings_layout = QVBoxLayout(warnings_group)
        self.metric_warnings_label = QLabel(
            "Uruchom analizę, aby zobaczyć ostrzeżenia przy metrykach."
        )
        self.metric_warnings_label.setWordWrap(True)
        warnings_layout.addWidget(self.metric_warnings_label)
        warnings_layout.addWidget(EducationalLimitationLabel())

        layout.addWidget(observation_group)
        layout.addWidget(importance_group)
        layout.addWidget(warnings_group)
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
        trial_rows = build_trial_observation_rows(
            events,
            clinical_profile=clinical_profile,
            max_trials=3,
        )
        observations = self._build_observations(
            events,
            clinical_profile,
            roving_report,
            trial_rows,
        )
        self.summary_label.setText("\n".join(f"• {item}" for item in observations))
        importance = self._build_importance_points(
            events, clinical_profile, roving_report
        )
        self.importance_label.setText("\n".join(f"• {item}" for item in importance))
        metric_warnings = _metric_educational_warnings(
            analysis_report,
            self.glossary_terms,
        )
        self.metric_warnings_label.setText(
            "\n".join(f"• {item}" for item in metric_warnings)
        )

    def _build_importance_points(
        self,
        events: list[dict[str, Any]],
        clinical_profile: dict[str, Any],
        roving_report: dict[str, Any],
    ) -> list[str]:
        """Zbuduj znaczenie obserwacji z polskich opisów w słowniku projektu."""
        terms = self.glossary_terms
        points = [
            (
                f"{_glossary_label(terms, 'event_timeline').capitalize()} "
                f"porządkuje bodźce i odpowiedzi w czasie; "
                f"kontekst słownika: {_glossary_context(terms, 'event_timeline')}."
            ),
            (
                f"{_glossary_label(terms, 'prediction_error').capitalize()} oraz "
                f"{_glossary_label(terms, 'confidence')} pomagają powiązać wykresy "
                "z decyzjami modelu zamiast oceniać tylko kształt krzywych."
            ),
        ]
        event_types = {str(event.get("event_type", "")) for event in events}
        for key in (
            "stimulus_onset",
            "response",
            "error",
            "neuromodulation_change",
            "significant_region_activity_change",
        ):
            if key in event_types:
                points.append(
                    f"{_glossary_label(terms, key).capitalize()} — "
                    f"{_glossary_context(terms, key)}."
                )
        functions = clinical_profile.get("cognitive_functions", [])
        if isinstance(functions, list):
            for function_name in functions[:3]:
                glossary_key = str(function_name).replace("-", "_")
                points.append(
                    f"{_glossary_label(terms, glossary_key).capitalize()} — "
                    f"{_glossary_context(terms, glossary_key)}."
                )
        if roving_report:
            points.append(
                "Standard, dewiant, habituacja i readaptacja pokazują, czy model "
                "odróżnia przewidywalny bodziec od zmiany reguły w tym samym przebiegu."
            )
        return points

    def _build_observations(
        self,
        events: list[dict[str, Any]],
        clinical_profile: dict[str, Any],
        roving_report: dict[str, Any],
        trial_rows: list[dict[str, str]],
    ) -> list[str]:
        """Zbuduj obserwacje z tych samych pól triali co eksport raportu."""
        observations: list[str] = []
        if events:
            event_types = sorted(
                {str(event.get("event_type", "n/a")) for event in events}
            )
            first_event = events[0]
            observations.append(
                f"Oś czasu zawiera {len(events)} zdarzeń: {', '.join(event_types)}."
            )
            observations.append(
                "Pierwsze zdarzenie: {label} około {time} s — {description}".format(
                    label=first_event.get("label_pl", "n/a"),
                    time=first_event.get("time_s", "n/a"),
                    description=first_event.get("description_pl", "brak opisu"),
                )
            )
            if trial_rows:
                first_trial = trial_rows[0]
                observations.append(
                    "Pierwszy trial: czas={time_s} s, warunek={condition}, "
                    "aktywne regiony={active_regions}.".format(**first_trial)
                )
                observations.append(
                    "Wynik behawioralny: {behavioral_outcome}; "
                    "najważniejsze metryki: {key_metrics}.".format(**first_trial)
                )
                observations.append(
                    "Komentarz raportowy: {comment_pl}".format(**first_trial)
                )
        else:
            observations.append("Oś czasu zdarzeń jest pusta dla bieżącego wyniku.")

        profile_name = clinical_profile.get("display_name") or clinical_profile.get(
            "id"
        )
        if profile_name:
            mechanism = clinical_profile.get("mechanism", "brak opisu mechanizmu")
            functions = clinical_profile.get("cognitive_functions", [])
            if isinstance(functions, list):
                functions_text = ", ".join(str(item) for item in functions) or "brak"
            else:
                functions_text = str(functions)
            observations.append(
                f"Profil kliniczny: {profile_name}; mechanizm: {mechanism}"
            )
            observations.append(f"Powiązane funkcje poznawcze: {functions_text}.")

        if roving_report:
            standard_tones = _extract_tones(roving_report, condition="standard")
            deviant_tones = _extract_tones(roving_report, condition="deviant")
            observations.append(
                "Roving oddball: standardy={standard}, dewianty={deviant}, "
                "nowe standardy={new_standard}.".format(
                    standard=roving_report.get("standard_count", "n/a"),
                    deviant=roving_report.get("deviant_count", "n/a"),
                    new_standard=roving_report.get("new_standard_count", "n/a"),
                )
            )
            observations.append(
                (
                    "W raporcie standardy mają tony {standard_tones}, "
                    "a dewianty {deviant_tones}."
                ).format(
                    standard_tones=standard_tones,
                    deviant_tones=deviant_tones,
                )
            )
            observations.append(
                "Habituacja={habituation}, średnia latencja readaptacji={latency}.".format(
                    habituation=roving_report.get("habituation_rate", "n/a"),
                    latency=roving_report.get("mean_readaptation_latency", "n/a"),
                )
            )
        return observations


class TeacherLessonPanel(QWidget):
    """Panel lekcji nauczyciela budowany z metadanych YAML i artefaktów GUI."""

    SECTION_TITLES = (
        "Checklista lekcji",
        "Hipoteza przed uruchomieniem",
        "Co uruchomiono",
        "Co obserwujesz",
        "Oczekiwany raport",
        "Jak interpretować wynik",
        "Ograniczenia interpretacyjne",
        "Pytania kontrolne",
        "Kryteria oceny odpowiedzi",
        "Raport porównawczy",
        "Co zmienić w kolejnym uruchomieniu",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz panel dydaktyczny bez importowania protokołów zadań."""
        super().__init__(parent)
        self.section_labels: dict[str, QLabel] = {}
        layout = QVBoxLayout(self)
        hint = QLabel(
            "Panel korzysta wyłącznie z GuiState, event_timeline, profilu "
            "klinicznego, raportu analizy oraz metadanych lekcji YAML."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(EducationalLimitationLabel())

        for title in self.SECTION_TITLES:
            group = QGroupBox(title)
            group_layout = QVBoxLayout(group)
            label = QLabel("Uruchom lekcję, aby wypełnić tę sekcję.")
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.section_labels[title] = label
            group_layout.addWidget(label)
            layout.addWidget(group)
        layout.addStretch(1)

    def set_context(
        self,
        lesson: dict[str, Any],
        state: GuiState,
        events: list[dict[str, Any]],
        clinical_profile: dict[str, Any],
        analysis_report: dict[str, Any],
    ) -> None:
        """Wypełnij lekcję z gotowych artefaktów GUI i wyników silnika.

        Parameters
        ----------
        lesson:
            Metadane lekcji wczytane z pliku ``configs/lessons/*.yaml``.
        state:
            Aktualny stan GUI z wybranym scenariuszem, konfiguracją i ziarnem.
        events:
            Oś czasu zdarzeń zwrócona przez silnik w polu ``event_timeline``.
        clinical_profile:
            Profil kliniczny z konfiguracji albo wyniku silnika.
        analysis_report:
            Raport analityczny zwrócony przez silnik po uruchomieniu scenariusza.
        """
        self.section_labels["Checklista lekcji"].setText(
            self._format_checklist(lesson.get("lesson_steps_pl"))
        )
        self.section_labels["Hipoteza przed uruchomieniem"].setText(
            self._bullet_list(lesson.get("pre_run_questions_pl"))
            or str(lesson.get("learning_goal_pl", "Brak celu lekcji w metadanych."))
        )
        self.section_labels["Co uruchomiono"].setText(
            "\n".join(
                (
                    f"• Cel lekcji: {lesson.get('learning_goal_pl', 'n/a')}",
                    f"• Scenariusz GUI: {state.scenario}",
                    f"• Konfiguracja scenariusza: "
                    f"{lesson.get('scenario_config') or state.scenario_config_path}",
                    f"• Konfiguracja porównania: "
                    f"{lesson.get('comparison_config') or state.comparison_config_path}",
                    f"• Task: {lesson.get('task_pl', 'n/a')}",
                    f"• Profil lekcji: {lesson.get('profile_pl', 'n/a')}",
                    f"• Ziarno losowości z GUI: {state.seed}",
                )
            )
        )
        self.section_labels["Co obserwujesz"].setText(
            self._build_observation_text(
                lesson=lesson,
                events=events,
                clinical_profile=clinical_profile,
                analysis_report=analysis_report,
            )
        )
        self.section_labels["Oczekiwany raport"].setText(
            self._bullet_list(lesson.get("expected_report_pl"))
            or "• Brak opisu oczekiwanego raportu."
        )
        self.section_labels["Jak interpretować wynik"].setText(
            self._build_interpretation_text(lesson, clinical_profile, analysis_report)
        )
        self.section_labels["Ograniczenia interpretacyjne"].setText(
            "\n".join(
                (
                    f"• {EDUCATIONAL_LIMITATION_TEXT_PL}",
                    "• Wnioski należy opierać na artefaktach bieżącego uruchomienia, "
                    "nie na ukrytej logice protokołu zadania.",
                )
            )
        )
        self.section_labels["Pytania kontrolne"].setText(
            self._bullet_list(lesson.get("post_run_questions_pl"))
            or "• Brak pytań kontrolnych w metadanych lekcji."
        )
        self.section_labels["Kryteria oceny odpowiedzi"].setText(
            self._bullet_list(lesson.get("assessment_criteria_pl"))
            or "• Brak kryteriów oceny w metadanych lekcji."
        )
        comparison_path = (
            lesson.get("comparison_config") or state.comparison_config_path
        )
        self.section_labels["Raport porównawczy"].setText(
            (
                "• Otwórz zakładkę „Porównanie profili” i użyj konfiguracji: "
                f"{comparison_path}."
            )
            if comparison_path
            else "• Ta lekcja nie definiuje raportu porównawczego."
        )
        self.section_labels["Co zmienić w kolejnym uruchomieniu"].setText(
            self._format_next_run_changes(lesson.get("next_run_changes"))
        )

    def _build_observation_text(
        self,
        lesson: dict[str, Any],
        events: list[dict[str, Any]],
        clinical_profile: dict[str, Any],
        analysis_report: dict[str, Any],
    ) -> str:
        """Zbuduj opis obserwacji z oczekiwań lekcji i artefaktów silnika."""
        lines = self._bullet_list(lesson.get("expected_observations_pl")).splitlines()
        lines.append(f"• Liczba zdarzeń na osi czasu: {len(events)}.")
        if events:
            event_types = sorted(
                {str(event.get("event_type", "n/a")) for event in events}
            )
            lines.append(f"• Typy zdarzeń: {', '.join(event_types)}.")
        profile_name = clinical_profile.get("display_name") or clinical_profile.get(
            "id"
        )
        if profile_name:
            lines.append(f"• Profil kliniczny w wyniku: {profile_name}.")
        metrics = analysis_report.get("metrics", {}) if analysis_report else {}
        if isinstance(metrics, dict) and metrics:
            metric_names = ", ".join(str(name) for name in list(metrics)[:5])
            lines.append(f"• Widoczne metryki raportu: {metric_names}.")
        return "\n".join(lines) if lines else "• Brak obserwacji do pokazania."

    @staticmethod
    def _format_checklist(steps: Any) -> str:
        """Sformatuj kroki lekcji jako checklistę do prowadzenia zajęć."""
        if not isinstance(steps, list) or not steps:
            return "☐ Brak kroków lekcji w metadanych."
        return "\n".join(f"☐ {step}" for step in steps)

    def _build_interpretation_text(
        self,
        lesson: dict[str, Any],
        clinical_profile: dict[str, Any],
        analysis_report: dict[str, Any],
    ) -> str:
        """Zbuduj ostrożną interpretację z celu lekcji, profilu i raportu."""
        lines = [f"• Odnieś wynik do celu: {lesson.get('learning_goal_pl', 'n/a')}."]
        mechanism = clinical_profile.get("mechanism")
        if mechanism:
            lines.append(f"• Mechanizm profilu wskazuje, czego oczekiwać: {mechanism}.")
        roving_report = (
            analysis_report.get("roving_oddball", {}) if analysis_report else {}
        )
        if isinstance(roving_report, dict) and roving_report:
            lines.append(
                "• W roving oddball porównaj standardy, dewianty, habituację "
                "i readaptację opisane w raporcie."
            )
        return "\n".join(lines)

    def _bullet_list(self, value: Any) -> str:
        """Sformatuj wartość YAML jako polską listę punktowaną."""
        if isinstance(value, list):
            return "\n".join(f"• {item}" for item in value)
        if value:
            return f"• {value}"
        return ""

    def _format_next_run_changes(self, value: Any) -> str:
        """Sformatuj sugestie zmian kolejnego uruchomienia z metadanych lekcji."""
        if not isinstance(value, list) or not value:
            return "• Brak sugestii zmian w metadanych lekcji."
        lines: list[str] = []
        for change in value:
            if isinstance(change, dict):
                lines.append(
                    "• {element}: {current} → {next_value}. Uzasadnienie: {reason}".format(
                        element=(
                            el
                            if (el := change.get("element")) is not None
                            else "parametr"
                        ),
                        current=(
                            cur
                            if (cur := change.get("current_value")) is not None
                            else "n/a"
                        ),
                        next_value=(
                            nxt
                            if (nxt := change.get("next_value")) is not None
                            else "n/a"
                        ),
                        reason=(
                            reas
                            if (reas := change.get("reason")) is not None
                            else "brak uzasadnienia"
                        ),
                    )
                )
            else:
                lines.append(f"• {change}")
        return "\n".join(lines)


class ProfileComparisonPanel(QWidget):
    """Panel tabeli porównawczej profili klinicznych zwróconej przez silnik."""

    HEADERS = [
        "profil",
        "oczekiwany kierunek",
        "obserwowany kierunek",
        "próg jakościowy",
        "interpretacja",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz tabelę dla trybu „Porównaj profile” z polskimi nagłówkami."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        hint = QLabel(
            "Tabela jest wypełniana z `profile_comparison_table` raportu silnika: "
            "profil, oczekiwany kierunek, obserwowany kierunek, próg jakościowy "
            "i interpretacja."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(EducationalLimitationLabel())

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.set_report({})

    def set_report(self, analysis_report: dict[str, Any] | None) -> None:
        """Odśwież tabelę porównania na podstawie raportu analitycznego.

        Parameters
        ----------
        analysis_report:
            Słownik zwrócony przez silnik z opcjonalnym kluczem
            ``profile_comparison_table``.
        """
        safe_report = analysis_report or {}
        rows = safe_report.get("profile_comparison_table", [])
        if not isinstance(rows, list):
            rows = []
        self.table.setRowCount(len(rows))
        keys = (
            "profile",
            "expected_direction",
            "observed_direction",
            "qualitative_threshold",
            "interpretation",
        )
        for row_index, row_payload in enumerate(rows):
            row = row_payload if isinstance(row_payload, dict) else {}
            for column_index, key in enumerate(keys):
                val = row.get(key)
                item = QTableWidgetItem(str(val) if val is not None else "n/a")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeColumnsToContents()


class LessonQuestionsPanel(QWidget):
    """Panel pytań kontrolnych wczytanych z metadanych wybranej lekcji."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz osobne tabele pytań przed uruchomieniem i po uruchomieniu."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.empty_label = QLabel(
            "Wybierz lekcję w sekcji Szybki start, aby zobaczyć pytania kontrolne."
        )
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)
        layout.addWidget(EducationalLimitationLabel())

        self.pre_run_table = self._create_questions_table(
            layout,
            "Pytania przed uruchomieniem",
        )
        self.post_run_table = self._create_questions_table(
            layout,
            "Pytania po uruchomieniu",
        )
        self.set_lesson(None)

    def set_lesson(self, lesson: dict[str, Any] | None) -> None:
        """Wyświetl pytania kontrolne zapisane w metadanych lekcji.

        Parameters
        ----------
        lesson:
            Metadane lekcji albo ``None``, gdy użytkownik nie wybrał lekcji.
        """
        has_lesson = lesson is not None
        self.empty_label.setVisible(not has_lesson)
        self.pre_run_table.parentWidget().setVisible(has_lesson)
        self.post_run_table.parentWidget().setVisible(has_lesson)
        safe_lesson = lesson or {}
        self._set_questions(
            self.pre_run_table,
            safe_lesson.get("pre_run_questions_pl"),
        )
        self._set_questions(
            self.post_run_table,
            safe_lesson.get("post_run_questions_pl"),
        )

    def _create_questions_table(
        self,
        parent_layout: QVBoxLayout,
        title: str,
    ) -> QTableWidget:
        """Utwórz nieedytowalną tabelę dla jednej grupy pytań."""
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        table = QTableWidget(0, 1)
        table.setHorizontalHeaderLabels(["pytanie"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        group_layout.addWidget(table)
        parent_layout.addWidget(group, 1)
        return table

    def _set_questions(self, table: QTableWidget, questions: Any) -> None:
        """Wypełnij tabelę pytaniami z listy lub pojedynczej wartości YAML."""
        if isinstance(questions, list):
            rows = questions
        elif questions:
            rows = [questions]
        else:
            rows = []
        table.setRowCount(len(rows))
        for row, question in enumerate(rows):
            item = QTableWidgetItem(str(question))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, item)
        table.resizeColumnsToContents()


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
        questions_group = QGroupBox("Panel pytań kontrolnych: roving oddball")
        questions_layout = QVBoxLayout(questions_group)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["pytanie", "odpowiedź z raportu"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        questions_layout.addWidget(self.table, 1)
        layout.addWidget(questions_group, 1)
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
        if not isinstance(roving_report, dict):
            roving_report = {}
        self.setVisible(bool(roving_report))
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
        standard_tones = _extract_tones(roving_report, condition="standard")
        deviant_tones = _extract_tones(roving_report, condition="deviant")
        new_standard_tones = _extract_tones(roving_report, is_new_standard=True)
        return [
            (
                "Który bodziec pełni rolę standardu?",
                (
                    "Standard to powtarzany ton raportowany jako {tones}; "
                    "liczba triali: {count}."
                ).format(
                    tones=standard_tones,
                    count=roving_report.get("standard_count", "n/a"),
                ),
            ),
            (
                "Który bodziec jest dewiantem?",
                (
                    "Dewiant to ton oznaczony warunkiem deviant: {tones}; "
                    "liczba triali: {count}."
                ).format(
                    tones=deviant_tones,
                    count=roving_report.get("deviant_count", "n/a"),
                ),
            ),
            (
                "Po czym rozpoznasz habituację?",
                "Po dodatnim tempie narastania habituation_level; raport: {rate}.".format(
                    rate=roving_report.get("habituation_rate", "n/a")
                ),
            ),
            (
                "Po czym rozpoznasz readaptację po zmianie standardu?",
                "Nowe standardy={new_standard}; tony={tones}; średnia latencja={latency}.".format(
                    new_standard=roving_report.get("new_standard_count", "n/a"),
                    tones=new_standard_tones,
                    latency=roving_report.get("mean_readaptation_latency", "n/a"),
                ),
            ),
        ]
