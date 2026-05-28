"""Obsługa zbierania, stosowania oraz zapisu konfiguracji GUI."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

from .gui_forms import APP_VERSION


class GuiConfigMixin:
    """Mixin zachowujący format konfiguracji GUI w plikach JSON."""

    def _collect_config(self) -> dict[str, Any]:
        """Zbierz aktualną konfigurację GUI bez zmiany formatu zapisu."""
        return {
            "T": self.T_var.get(),
            "dt": self.dt_var.get(),
            "auto_dt": self.auto_dt_var.get(),
            "seed": self.seed_var.get(),
            "command": self.command_var.get(),
            "batch_seeds": self.batch_seeds_var.get(),
            "batch_scenarios": self.batch_scenarios_var.get(),
            "sensitivity_params": self.sensitivity_var.get(),
            "sensitivity_delta": self.sensitivity_delta_var.get(),
            "scenario": self.scenario_var.get(),
            "save_results": self.save_results_var.get(),
            "brain_params": {name: var.get() for name, var in self.brain_form.vars.items()},
            "oscillator_params": {name: var.get() for name, var in self.osc_form.vars.items()},
            "plots": {name: var.get() for name, var in self.plot_vars.items()},
        }

    def _apply_config(self, config: dict[str, Any]) -> None:
        """Zastosuj konfigurację odczytaną z JSON do kontrolek GUI."""
        self.T_var.set(str(config.get("T", self.T_var.get())))
        self.dt_var.set(str(config.get("dt", self.dt_var.get())))
        self.seed_var.set(str(config.get("seed", self.seed_var.get())))
        self.auto_dt_var.set(bool(config.get("auto_dt", self.auto_dt_var.get())))
        self.command_var.set(str(config.get("command", self.command_var.get())))
        self.batch_seeds_var.set(str(config.get("batch_seeds", self.batch_seeds_var.get())))
        self.batch_scenarios_var.set(
            str(config.get("batch_scenarios", self.batch_scenarios_var.get()))
        )
        self.sensitivity_var.set(str(config.get("sensitivity_params", self.sensitivity_var.get())))
        self.sensitivity_delta_var.set(
            str(config.get("sensitivity_delta", self.sensitivity_delta_var.get()))
        )
        if "dt" in self.brain_form.vars:
            self.brain_form.vars["dt"].set(str(self.dt_var.get()))
        self.scenario_var.set(str(config.get("scenario", self.scenario_var.get())))
        self.save_results_var.set(bool(config.get("save_results", self.save_results_var.get())))
        self._on_auto_dt_toggle()

        for name, value in config.get("brain_params", {}).items():
            if name in self.brain_form.vars:
                self.brain_form.vars[name].set(value)
        for name, value in config.get("oscillator_params", {}).items():
            if name in self.osc_form.vars:
                self.osc_form.vars[name].set(value)
        for name, value in config.get("plots", {}).items():
            if name in self.plot_vars:
                self.plot_vars[name].set(bool(value))

    def _save_current_config(self) -> None:
        """Zapisz bieżącą konfigurację GUI do pliku JSON."""
        default_name = f"brain_model_config_{date.today().isoformat()}.json"
        target = filedialog.asksaveasfilename(
            title="Zapisz konfigurację",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not target:
            return
        payload = {
            "format": "brain-model-gui-config-v1",
            "app_version": APP_VERSION,
            "saved_date": date.today().isoformat(),
            "config": self._collect_config(),
        }
        try:
            Path(target).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.status_var.set(f"Zapisano konfigurację: {target}")
        except Exception as exc:
            messagebox.showerror("Błąd", f"Nie udało się zapisać konfiguracji: {exc}")

    def _load_existing_config(self) -> None:
        """Wczytaj konfigurację GUI z pliku JSON."""
        source = filedialog.askopenfilename(
            title="Wczytaj konfigurację",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not source:
            return
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        config = payload.get("config", payload)
        self._apply_config(config)
        self.status_var.set(f"Wczytano konfigurację: {source}")
