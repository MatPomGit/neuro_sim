"""Kompatybilnościowy import raportu końcowego eksperymentu.

Nowy kod powinien importować ``final_experiment_report`` z
``brain_core.analysis.reports``. Ten moduł pozostaje cienką fasadą dla starszych
skryptów, które używały ścieżki ``analysis.reports``.
"""

from __future__ import annotations

from brain_core.analysis.reports import final_experiment_report

__all__ = ["final_experiment_report"]
