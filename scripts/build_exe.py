"""Skrypt budujący samodzielny plik wykonywalny aplikacji NeuroSim GUI.

Uruchomienie:
    python scripts/build_exe.py

Wymagania wstępne:
    pip install pyinstaller pyinstaller-hooks-contrib

Wyniki trafią do katalogu dist/NeuroSim/ (tryb --onedir).
Plik wykonywalny to dist/NeuroSim/NeuroSim.exe (Windows)
lub dist/NeuroSim/NeuroSim (Linux/macOS).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = REPO_ROOT / "neuro_sim_gui.spec"


def check_pyinstaller() -> None:
    """Sprawdź, czy PyInstaller jest zainstalowany; zgłoś błąd, jeśli nie.

    Raises
    ------
    SystemExit
        Gdy PyInstaller nie jest zainstalowany w bieżącym środowisku.
    """
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "Błąd: PyInstaller nie jest zainstalowany.\n"
            "Zainstaluj go poleceniem:\n"
            "  pip install pyinstaller pyinstaller-hooks-contrib",
            file=sys.stderr,
        )
        sys.exit(1)


def build() -> None:
    """Uruchom PyInstaller z plikiem specyfikacji neuro_sim_gui.spec.

    Raises
    ------
    SystemExit
        Gdy PyInstaller zakończy działanie z kodem błędu różnym od zera.
    """
    check_pyinstaller()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ]
    print(f"Uruchamiam: {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    except (FileNotFoundError, OSError) as exc:
        print(
            f"Błąd: nie można uruchomić PyInstaller ({exc}).\n"
            "Upewnij się, że PyInstaller jest zainstalowany i dostępny w PATH.",
            file=sys.stderr,
        )
        sys.exit(1)
    if result.returncode != 0:
        print("Błąd: budowanie EXE nie powiodło się.", file=sys.stderr)
        sys.exit(result.returncode)

    exe_suffix = ".exe" if sys.platform == "win32" else ""
    exe_path = REPO_ROOT / "dist" / "NeuroSim" / f"NeuroSim{exe_suffix}"
    print("\nBudowanie zakończone pomyślnie.\n" f"Plik wykonywalny: {exe_path}")


if __name__ == "__main__":
    build()
