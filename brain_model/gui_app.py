"""Główna klasa okna GUI oraz punkt startowy aplikacji."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk

from .gui_config import GuiConfigMixin
from .gui_layout import GuiLayoutMixin, configure_styles
from .gui_runner import GuiRunnerMixin
from .gui_state import GuiState
from .oscillators import WilsonCowanParams
from .params import BrainParams


class BrainModelGUI(GuiConfigMixin, GuiRunnerMixin, GuiLayoutMixin, tk.Tk):
    """Główne okno konfiguracji i uruchamiania symulacji modelu poznawczego."""

    def __init__(self) -> None:
        """Utwórz stan aplikacji, formularze i elementy okna głównego."""
        super().__init__()
        self.title("konfiguracja symulacji Cognitive Brain Model")
        self.geometry("1180x780")
        self.minsize(940, 660)
        configure_styles(self)

        self.brain_defaults: BrainParams = BrainParams()
        self.osc_defaults: WilsonCowanParams = WilsonCowanParams()

        self.state: GuiState
        self.state = GuiState(
            dt=str(self.brain_defaults.dt),
            brain_params=self.brain_defaults,
            oscillator_params=self.osc_defaults,
        )
        self._build_layout()
        self._build_menu()
        self._worker_thread: threading.Thread | None = None
        self._result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._running: bool = False


def run_gui() -> None:
    """Uruchom aplikację GUI z katalogu głównego projektu."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.chdir("..")
    app = BrainModelGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
