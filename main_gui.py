"""Thin GUI entrypoint.

UI implementation lives in :mod:`brain_model.gui`.
This file intentionally only starts the app.
"""

from brain_model.gui import run_gui


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    run_gui()
