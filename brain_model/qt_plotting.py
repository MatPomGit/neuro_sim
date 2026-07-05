"""Panel Qt do osadzania niezależnych funkcji rysujących Matplotlib."""

from __future__ import annotations

from typing import Any, Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout, QWidget

from .plotting import (
    _add_interpretation_box,
    _apply_interpretation_layout,
    _attach_line_tooltips,
)


def draw_report_metric_bars(
    axis: Any, eeg_bold_sections: list[dict[str, Any]]
) -> list[Any]:
    """Narysuj gotowe metryki EEG/BOLD z raportu jako warstwę prezentacji.

    Parameters
    ----------
    axis:
        Oś Matplotlib utworzona przez panel Qt.
    eeg_bold_sections:
        Wiersze ``eeg_bold_sections`` przygotowane w ``brain_core``. Funkcja
        nie liczy metryk analitycznych; tylko prezentuje przekazane wartości.

    Returns:
    -------
    list[Any]
        Lista osi Matplotlib użytych do prezentacji.
    """

    rows = [row for row in eeg_bold_sections if isinstance(row, dict)]
    numeric_rows: list[dict[str, Any]] = []
    for row in rows:
        try:
            float(row.get("value", 0.0))
        except (TypeError, ValueError):
            continue
        numeric_rows.append(row)

    if not numeric_rows:
        axis.text(
            0.5,
            0.5,
            "Brak gotowych metryk EEG/BOLD do pokazania.",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
        axis.set_axis_off()
        return [axis]

    labels = [
        f"{row.get('modality', 'n/a')}\n{row.get('metric', 'metryka')}"
        for row in numeric_rows
    ]
    values = [float(row.get("value", 0.0)) for row in numeric_rows]
    colors = [
        "#2563eb" if str(row.get("modality", "")) == "EEG" else "#7c3aed"
        for row in numeric_rows
    ]
    axis.bar(range(len(values)), values, color=colors, alpha=0.82)
    axis.set_xticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axis.set_ylabel("Wartość metryki")
    axis.set_title("Gotowe metryki EEG/BOLD z raportu brain_core")
    axis.grid(axis="y", alpha=0.25)
    _add_interpretation_box(
        axis.figure,
        "Co widzisz: słupki pokazują wartości już policzone w brain_core. "
        "Ten wykres jest wyłącznie warstwą prezentacji Qt/PDF; interpretację "
        "i ograniczenia metryk czytaj w sekcji EEG/BOLD raportu.",
    )
    return [axis]


class QtPlotPanel(QTabWidget):
    """Panel zakładek zawierający figury Matplotlib osadzone w Qt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz pusty panel zakładek z wykresami."""
        super().__init__(parent)
        self.setDocumentMode(True)
        self._figures: list[Figure] = []
        self._figure_titles: list[str] = []
        self._canvases: list[FigureCanvasQTAgg] = []

    def clear(self) -> None:
        """Usuń wszystkie aktualnie widoczne zakładki wykresów."""
        for i in range(self.count()):
            widget = self.widget(i)
            if widget is not None:
                widget.deleteLater()
        super().clear()
        self._figures.clear()
        self._figure_titles.clear()
        self._canvases.clear()

    def add_plot(
        self,
        title: str,
        draw_func: Callable[..., Any],
        *args: Any,
        figsize: tuple[float, float] = (11, 6),
        controls_factory: (
            Callable[[FigureCanvasQTAgg, list[Any]], QWidget | None] | None
        ) = None,
        **kwargs: Any,
    ) -> None:
        """Dodaj zakładkę z figurą utworzoną przez niezależną funkcję rysującą."""
        fig = Figure(figsize=figsize, dpi=100)
        axis = fig.add_subplot(111)
        axes = draw_func(axis, *args, **kwargs) or [axis]
        _apply_interpretation_layout(fig)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        canvas = FigureCanvasQTAgg(fig)
        _attach_line_tooltips(fig, axes)
        toolbar = NavigationToolbar2QT(canvas, container)
        layout.addWidget(toolbar)
        if controls_factory is not None:
            controls_widget = controls_factory(canvas, list(axes))
            if controls_widget is not None:
                layout.addWidget(controls_widget)
        layout.addWidget(canvas)
        canvas.draw()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.addTab(scroll, title)
        self._figures.append(fig)
        self._figure_titles.append(title)
        self._canvases.append(canvas)

    def add_report_metrics_plot(
        self, eeg_bold_sections: list[dict[str, Any]], title: str = "Metryki EEG/BOLD"
    ) -> None:
        """Dodaj prezentacyjny wykres metryk EEG/BOLD bez logiki analitycznej.

        Parameters
        ----------
        eeg_bold_sections:
            Gotowe wiersze raportowe wyliczone przez ``brain_core``.
        title:
            Polski tytuł zakładki w panelu Qt.
        """

        self.add_plot(
            title, draw_report_metric_bars, eeg_bold_sections, figsize=(11, 6)
        )

    def plots_for_export(self) -> list[tuple[str, Figure]]:
        """Zwróć aktualne figury z tytułami zakładek do eksportu PDF.

        Returns:
        -------
        list[tuple[str, Figure]]
            Lista par zawierających polski tytuł zakładki i figurę Matplotlib.
        """

        return list(zip(self._figure_titles, self._figures))
