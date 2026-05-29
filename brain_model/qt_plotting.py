"""Panel Qt do osadzania niezależnych funkcji rysujących Matplotlib."""

from __future__ import annotations

from typing import Any, Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout, QWidget

from .plotting import _attach_line_tooltips


class QtPlotPanel(QTabWidget):
    """Panel zakładek zawierający figury Matplotlib osadzone w Qt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Utwórz pusty panel zakładek z wykresami."""
        super().__init__(parent)
        self.setDocumentMode(True)
        self._figures: list[Figure] = []
        self._canvases: list[FigureCanvasQTAgg] = []

    def clear(self) -> None:
        """Usuń wszystkie aktualnie widoczne zakładki wykresów."""
        while self.count() > 0:
            widget = self.widget(0)
            self.removeTab(0)
            widget.deleteLater()
        self._figures.clear()
        self._canvases.clear()

    def add_plot(
        self,
        title: str,
        draw_func: Callable[..., Any],
        *args: Any,
        figsize: tuple[float, float] = (11, 6),
        **kwargs: Any,
    ) -> None:
        """Dodaj zakładkę z figurą utworzoną przez niezależną funkcję rysującą."""
        fig = Figure(figsize=figsize, dpi=100)
        axis = fig.add_subplot(111)
        axes = draw_func(axis, *args, **kwargs) or [axis]
        fig.tight_layout()

        container = QWidget()
        layout = QVBoxLayout(container)
        canvas = FigureCanvasQTAgg(fig)
        _attach_line_tooltips(fig, axes)
        toolbar = NavigationToolbar2QT(canvas, container)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        canvas.draw()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.addTab(scroll, title)
        self._figures.append(fig)
        self._canvases.append(canvas)
