"""Kompatybilny punkt wejścia GUI modelu poznawczego delegujący do PySide6."""

from __future__ import annotations

from .qt_app import BrainModelGUI, BrainModelQtWindow, run_gui

__all__ = ["BrainModelGUI", "BrainModelQtWindow", "run_gui"]


if __name__ == "__main__":
    run_gui()
