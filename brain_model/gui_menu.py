"""Menu główne i okna informacyjne GUI."""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Any

from .gui_forms import APP_AUTHOR, APP_VERSION, LAST_UPDATED


def _build_menu(gui: Any) -> None:
    """Zbuduj główne menu aplikacji."""
    menubar = tk.Menu(gui)

    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Nowa instancja", command=gui._open_new_instance)
    file_menu.add_separator()
    file_menu.add_command(
        label="Zapisz konfigurację...", command=gui._save_current_config
    )
    file_menu.add_command(
        label="Wczytaj konfigurację...", command=gui._load_existing_config
    )
    file_menu.add_separator()
    file_menu.add_command(label="Zamknij", command=gui.destroy)
    menubar.add_cascade(label="Plik", menu=file_menu)

    edit_menu = tk.Menu(menubar, tearoff=0)
    edit_menu.add_command(
        label="Konfiguracja symulacji", command=lambda: gui.tabs.select(0)
    )
    edit_menu.add_command(
        label="Konfiguracja wykresów", command=gui._focus_plots_section
    )
    edit_menu.add_command(
        label="Parametry modelu i oscylatorów...", command=gui._open_advanced_settings
    )
    edit_menu.add_separator()
    edit_menu.add_command(label="Przywróć domyślne", command=gui.reset_defaults)
    menubar.add_cascade(label="Ustawienia", menu=edit_menu)

    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="Instrukcja używania", command=gui._show_usage_help)
    help_menu.add_command(label="O programie", command=gui._show_about)
    menubar.add_cascade(label="Pomoc", menu=help_menu)

    gui.config(menu=menubar)


def _show_usage_help(gui: Any) -> None:
    """Pokaż użytkownikowi krótką instrukcję obsługi GUI."""
    messagebox.showinfo(
        "Instrukcja używania",
        (
            "Szybki przepływ dla początkującego:\n"
            "1) W sekcji 'Szybki start' wybierz scenariusz.\n"
            "2) Ustaw czas symulacji w sekundach.\n"
            "3) Kliknij 'Uruchom symulację'.\n"
            "4) Obejrzyj wyniki w zakładce 'Wykresy'.\n\n"
            "Opcjonalnie:\n"
            "- Zostaw włączone 'Zapisz wyniki po symulacji', aby zapisać pliki w outputs/.\n"
            "- W panelu 'Wyniki i wykresy' wybierz zestaw wykresów: Podstawowe, "
            "Diagnostyczne lub Pełne.\n"
            "- Rozwiń 'Opcje zaawansowane' tylko wtedy, gdy chcesz zmienić ziarno, "
            "dt, tryb serii albo analizę wrażliwości.\n\n"
            "Menu Plik zapisuje i wczytuje konfigurację bez zmiany jej dotychczasowego formatu."
        ),
    )


def _show_about(gui: Any) -> None:
    """Pokaż informacje o wersji aplikacji."""
    messagebox.showinfo(
        "O programie",
        (
            "Cognitive Brain Model\n"
            f"Wersja: {APP_VERSION}\n"
            f"Ostatnia aktualizacja: {LAST_UPDATED}\n"
            f"Autor: {APP_AUTHOR}"
        ),
    )


def _open_new_instance(gui: Any) -> None:
    """Uruchom nowe okno programu jako osobny proces."""
    try:
        root_dir = Path(__file__).resolve().parents[1]
        entrypoint = root_dir / "main_gui.py"
        if not entrypoint.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku startowego: {entrypoint}")
        subprocess.Popen([sys.executable, str(entrypoint)], cwd=str(root_dir))
        gui.status_var.set("Uruchomiono nową instancję programu.")
    except Exception as exc:
        messagebox.showerror("Błąd", f"Nie udało się uruchomić nowej instancji: {exc}")
