"""Legacy GUI entrypoint kept for compatibility.

Delegates to :mod:`brain_model.gui`.
"""

from brain_model.gui import run_gui


if __name__ == "__main__":
    run_gui()
