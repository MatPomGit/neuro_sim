"""Legacy formularze tkinter dla modelu poznawczego.

Aktywne desktopowe GUI jest oparte na PySide6; ten moduł pozostaje warstwą
kompatybilności tkinter i nie powinien być importowany przez moduły `qt_*`.
"""

# ruff: noqa: E501

from __future__ import annotations

import tkinter as tk
from dataclasses import fields
from tkinter import ttk
from typing import Any, Dict, Iterable

from .gui_labels import (
    APP_AUTHOR,
    APP_VERSION,
    COMMAND_LABELS,
    COMMAND_VALUES,
    LAST_UPDATED,
    PARAMETER_DESCRIPTIONS,
    PARAMETER_LABELS,
    RULE_FIELDS,
)

__all__ = [
    "APP_AUTHOR",
    "APP_VERSION",
    "COMMAND_LABELS",
    "COMMAND_VALUES",
    "LAST_UPDATED",
    "PARAMETER_DESCRIPTIONS",
    "PARAMETER_LABELS",
    "RULE_FIELDS",
    "ParameterForm",
    "Tooltip",
]


class Tooltip:
    """Prosta podpowiedź tekstowa wyświetlana po najechaniu na widżet."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        """Zarejestruj obsługę pokazania i ukrycia podpowiedzi."""
        self.widget: tk.Widget = widget
        self.text: str = text
        self.tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event: tk.Event | None = None) -> None:
        """Pokaż okno podpowiedzi obok widżetu."""
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        ttk.Label(
            self.tip,
            text=self.text,
            padding=(8, 5),
            relief="solid",
            borderwidth=1,
            background="#ffffe0",
            wraplength=420,
        ).pack()

    def hide(self, event: tk.Event | None = None) -> None:
        """Ukryj aktywne okno podpowiedzi."""
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ParameterForm(ttk.LabelFrame):
    """Formularz parametrów budowany na podstawie pól dataclass."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        dataclass_type: type[Any],
        defaults: Any,
        include_fields: Iterable[str] | None = None,
    ) -> None:
        """Utwórz kontrolki edycji dla widocznych pól dataclass."""
        super().__init__(parent, text=title, padding=10)
        self.dataclass_type: type[Any] = dataclass_type
        self.defaults: Any = defaults
        self.vars: Dict[str, tk.Variable] = {}
        self.include_fields: set[str] | None = (
            set(include_fields) if include_fields is not None else None
        )

        form_fields = [
            f
            for f in fields(dataclass_type)
            if self.include_fields is None or f.name in self.include_fields
        ]
        for row, field in enumerate(form_fields):
            name = field.name
            value = getattr(defaults, name)

            label = ttk.Label(self, text=PARAMETER_LABELS.get(name, name))
            label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            Tooltip(label, PARAMETER_DESCRIPTIONS.get(name, ""))

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                widget = ttk.Checkbutton(self, variable=var)
                widget.grid(row=row, column=1, sticky="w", pady=3)
            else:
                var = tk.StringVar(value=str(value))
                widget = ttk.Entry(self, textvariable=var, width=14)
                widget.grid(row=row, column=1, sticky="ew", pady=3)

            self.vars[name] = var

        self.columnconfigure(1, weight=1)

    def values(self) -> Any:
        """Zwróć instancję dataclass z wartościami odczytanymi z formularza."""
        kwargs = {}
        for field in fields(self.dataclass_type):
            name = field.name
            if self.include_fields is not None and name not in self.include_fields:
                kwargs[name] = getattr(self.defaults, name)
                continue
            default_value = getattr(self.defaults, name)
            raw = self.vars[name].get()

            try:
                if isinstance(default_value, bool):
                    kwargs[name] = bool(raw)
                elif isinstance(default_value, int) and not isinstance(
                    default_value, bool
                ):
                    kwargs[name] = int(raw)
                else:
                    kwargs[name] = float(raw)
            except ValueError as exc:
                raise ValueError(
                    f"Niepoprawna wartość parametru '{name}': {raw}"
                ) from exc

        return self.dataclass_type(**kwargs)

    def reset(self) -> None:
        """Przywróć w formularzu wartości domyślne."""
        for field in fields(self.dataclass_type):
            if (
                self.include_fields is not None
                and field.name not in self.include_fields
            ):
                continue
            name = field.name
            value = getattr(self.defaults, name)
            self.vars[name].set(value if isinstance(value, bool) else str(value))
