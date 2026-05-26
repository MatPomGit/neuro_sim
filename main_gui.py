"""Thin GUI entrypoint.

UI implementation lives in :mod:`brain_model.gui`.
This file intentionally only starts the app.
"""

from brain_model.gui import run_gui


if __name__ == "__main__":
    run_gui()
