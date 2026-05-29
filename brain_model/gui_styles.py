"""Style wizualne głównego okna GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def configure_styles(root: tk.Tk) -> None:
    """Skonfiguruj spójną, spokojną paletę stylów ttk dla głównego okna GUI."""
    palette = {
        "primary": "#2563eb",
        "primary_active": "#1d4ed8",
        "panel_bg": "#f8fafc",
        "panel_border": "#94a3b8",
        "panel_border_dark": "#64748b",
        "scenario_bg": "#eef6ff",
        "warning": "#b45309",
        "advanced_fg": "#64748b",
        "text": "#0f172a",
        "muted": "#475569",
        "card_bg": "#ffffff",
        "accent_bg": "#e0f2fe",
    }

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(background=palette["panel_bg"])
    style.configure("TFrame", background=palette["panel_bg"])
    style.configure(
        "TNotebook",
        background=palette["panel_bg"],
        bordercolor=palette["panel_border"],
        borderwidth=1,
    )
    style.configure(
        "TNotebook.Tab",
        background="#e2e8f0",
        bordercolor=palette["panel_border_dark"],
        borderwidth=1,
        padding=(10, 6),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette["card_bg"]), ("active", "#f1f5f9")],
        foreground=[("selected", palette["primary"])],
    )
    style.configure("Header.TFrame", background=palette["panel_bg"])
    style.configure("Footer.TFrame", background=palette["panel_bg"])
    style.configure(
        "Workflow.TFrame",
        background=palette["accent_bg"],
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "HeaderTitle.TLabel",
        background=palette["panel_bg"],
        foreground=palette["text"],
        font=("TkDefaultFont", 13, "bold"),
    )
    style.configure(
        "HeaderSubtitle.TLabel",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "SectionHint.TLabel",
        background=palette["panel_bg"],
        foreground=palette["muted"],
        font=("TkDefaultFont", 9),
    )
    style.configure(
        "WorkflowTitle.TLabel",
        background=palette["accent_bg"],
        foreground=palette["text"],
        font=("TkDefaultFont", 10, "bold"),
    )
    style.configure(
        "WorkflowStep.TLabel",
        background=palette["accent_bg"],
        foreground=palette["muted"],
        font=("TkDefaultFont", 9),
    )
    style.configure(
        "Footer.TLabel",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "QuickStart.TLabelframe",
        background=palette["card_bg"],
        bordercolor=palette["panel_border"],
        relief="solid",
    )
    style.configure(
        "QuickStart.TLabelframe.Label",
        background=palette["card_bg"],
        foreground=palette["text"],
        font=("TkDefaultFont", 10, "bold"),
    )
    style.configure(
        "ScenarioInfo.TLabel",
        background=palette["scenario_bg"],
        foreground=palette["text"],
        padding=8,
    )
    style.configure(
        "Primary.TButton",
        background=palette["primary"],
        foreground="#ffffff",
        font=("TkDefaultFont", 10, "bold"),
        padding=(10, 6),
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", palette["primary_active"]),
            ("pressed", palette["primary_active"]),
        ],
        foreground=[("disabled", "#e2e8f0")],
    )
    style.configure(
        "Status.TLabel",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "Warning.Status.TLabel",
        background=palette["panel_bg"],
        foreground=palette["warning"],
        font=("TkDefaultFont", 9, "bold"),
    )
    style.configure(
        "Status.Horizontal.TProgressbar",
        background=palette["primary"],
        troughcolor="#e2e8f0",
        bordercolor=palette["panel_border"],
        lightcolor=palette["primary"],
        darkcolor=palette["primary"],
    )
    style.configure(
        "Advanced.TCheckbutton",
        background=palette["panel_bg"],
        foreground=palette["advanced_fg"],
        indicatorcolor=palette["card_bg"],
        indicatorrelief="solid",
        bordercolor=palette["panel_border_dark"],
        borderwidth=1,
    )
    style.map(
        "Advanced.TCheckbutton",
        indicatorcolor=[("selected", palette["primary"]), ("active", "#dbeafe")],
    )
    style.configure(
        "Advanced.TLabelframe",
        background=palette["card_bg"],
        bordercolor=palette["panel_border"],
    )
    style.configure(
        "Advanced.TLabelframe.Label",
        background=palette["card_bg"],
        foreground=palette["advanced_fg"],
    )
    style.configure(
        "Plots.TLabelframe",
        background=palette["card_bg"],
        bordercolor=palette["panel_border"],
    )
    style.configure(
        "Plots.TLabelframe.Label",
        background=palette["card_bg"],
        foreground=palette["text"],
        font=("TkDefaultFont", 10, "bold"),
    )
    style.configure(
        "Advanced.TButton",
        background="#e2e8f0",
        foreground=palette["advanced_fg"],
        padding=(8, 4),
    )
    style.map("Advanced.TButton", background=[("active", "#cbd5e1")])
