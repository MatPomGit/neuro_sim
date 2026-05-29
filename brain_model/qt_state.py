"""Kompatybilny alias stanu GUI używany przez moduły PySide6."""

from __future__ import annotations

from .gui_state import GuiState

QtGuiState = GuiState

__all__ = ["GuiState", "QtGuiState"]
