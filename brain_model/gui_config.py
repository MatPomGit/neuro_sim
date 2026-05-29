"""Obsługa zbierania, stosowania oraz zapisu konfiguracji GUI."""

from __future__ import annotations

import json
from dataclasses import fields, replace
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, TypeVar

from .gui_forms import APP_VERSION, RULE_FIELDS

TDataclass = TypeVar("TDataclass")


class GuiConfigMixin:
    """Mixin zachowujący format konfiguracji GUI w plikach JSON."""

    def _sync_state_from_controls(self) -> None:
        """Przepisz wartości z widocznych kontrolek głównego okna do stanu GUI."""
        self.state.T = self.T_var.get()
        self.state.dt = self.dt_var.get()
        self.state.auto_dt = bool(self.auto_dt_var.get())
        self.state.seed = self.seed_var.get()
        self.state.command = self.command_var.get()
        self.state.batch_seeds = self.batch_seeds_var.get()
        self.state.batch_scenarios = self.batch_scenarios_var.get()
        self.state.sensitivity_params = self.sensitivity_var.get()
        self.state.sensitivity_delta = self.sensitivity_delta_var.get()
        self.state.scenario = self.scenario_var.get()
        self.state.save_results = bool(self.save_results_var.get())
        self.state.plots = {name: bool(var.get()) for name, var in self.plot_vars.items()}

    def _sync_controls_from_state(self) -> None:
        """Przepisz stan GUI do widocznych kontrolek głównego okna."""
        self.T_var.set(self.state.T)
        self.dt_var.set(self.state.dt)
        self.auto_dt_var.set(self.state.auto_dt)
        self.seed_var.set(self.state.seed)
        self.command_var.set(self.state.command)
        self.batch_seeds_var.set(self.state.batch_seeds)
        self.batch_scenarios_var.set(self.state.batch_scenarios)
        self.sensitivity_var.set(self.state.sensitivity_params)
        self.sensitivity_delta_var.set(self.state.sensitivity_delta)
        self.scenario_var.set(self.state.scenario)
        self.save_results_var.set(self.state.save_results)
        for name, value in self.state.plots.items():
            if name in self.plot_vars:
                self.plot_vars[name].set(bool(value))
        self._sync_plot_preset_from_vars()

    def _sync_advanced_forms_from_state(self, brain_form: Any, osc_form: Any) -> None:
        """Wypełnij formularze zaawansowane wartościami zapisanymi w stanie GUI."""
        for name, var in brain_form.vars.items():
            value = getattr(self.state.brain_params, name)
            var.set(value if isinstance(value, bool) else str(value))
        for name, var in osc_form.vars.items():
            value = getattr(self.state.oscillator_params, name)
            var.set(value if isinstance(value, bool) else str(value))

    def _sync_state_from_advanced_forms(self, brain_form: Any, osc_form: Any) -> None:
        """Zapisz wartości zatwierdzonych formularzy zaawansowanych do stanu GUI."""
        edited_brain_params = brain_form.values()
        try:
            current_dt = float(self.state.dt)
        except ValueError:
            current_dt = self.state.brain_params.dt
        self.state.brain_params = replace(
            edited_brain_params,
            dt=current_dt,
            semantic_rule=self.brain_defaults.semantic_rule,
            value_rule=self.brain_defaults.value_rule,
            connectivity_adaptation=self.brain_defaults.connectivity_adaptation,
        )
        self.state.oscillator_params = osc_form.values()

    def _collect_config(self) -> dict[str, Any]:
        """Zbierz aktualną konfigurację GUI bez zmiany formatu zapisu."""
        self._sync_state_from_controls()
        return {
            "T": self.state.T,
            "dt": self.state.dt,
            "auto_dt": self.state.auto_dt,
            "seed": self.state.seed,
            "command": self.state.command,
            "batch_seeds": self.state.batch_seeds,
            "batch_scenarios": self.state.batch_scenarios,
            "sensitivity_params": self.state.sensitivity_params,
            "sensitivity_delta": self.state.sensitivity_delta,
            "scenario": self.state.scenario,
            "save_results": self.state.save_results,
            "brain_params": {
                **self._editable_dataclass_values(self.state.brain_params, exclude=RULE_FIELDS),
                "dt": self.state.dt,
            },
            "oscillator_params": self._editable_dataclass_values(self.state.oscillator_params),
            "plots": dict(self.state.plots),
        }

    def _apply_config(self, config: dict[str, Any]) -> None:
        """Zastosuj konfigurację odczytaną z JSON do stanu i kontrolek GUI."""
        self.state.T = str(config.get("T", self.state.T))
        self.state.dt = str(config.get("dt", self.state.dt))
        self.state.seed = str(config.get("seed", self.state.seed))
        self.state.auto_dt = bool(config.get("auto_dt", self.state.auto_dt))
        self.state.command = str(config.get("command", self.state.command))
        self.state.batch_seeds = str(config.get("batch_seeds", self.state.batch_seeds))
        self.state.batch_scenarios = str(
            config.get("batch_scenarios", self.state.batch_scenarios)
        )
        self.state.sensitivity_params = str(
            config.get("sensitivity_params", self.state.sensitivity_params)
        )
        self.state.sensitivity_delta = str(
            config.get("sensitivity_delta", self.state.sensitivity_delta)
        )
        self.state.scenario = str(config.get("scenario", self.state.scenario))
        self.state.save_results = bool(config.get("save_results", self.state.save_results))
        self.state.brain_params = self._dataclass_with_updates(
            self.state.brain_params, config.get("brain_params", {})
        )
        self.state.oscillator_params = self._dataclass_with_updates(
            self.state.oscillator_params, config.get("oscillator_params", {})
        )
        self.state.plots.update(
            {
                name: bool(value)
                for name, value in config.get("plots", {}).items()
                if name in self.plot_vars
            }
        )
        self._sync_controls_from_state()
        self._refresh_scenario_details()
        self._on_auto_dt_toggle()
        try:
            self.state.brain_params = replace(self.state.brain_params, dt=float(self.dt_var.get()))
            self.state.dt = self.dt_var.get()
        except ValueError:
            pass

    def _editable_dataclass_values(
        self, instance: Any, exclude: tuple[str, ...] = ()
    ) -> dict[str, Any]:
        """Zwróć słownik prostych pól dataclass przeznaczonych do zapisu w konfiguracji."""
        return {
            field.name: getattr(instance, field.name)
            for field in fields(instance)
            if field.name not in exclude
        }

    def _dataclass_with_updates(self, instance: TDataclass, values: dict[str, Any]) -> TDataclass:
        """Zbuduj kopię dataclass z wartościami przekonwertowanymi jak w formularzu GUI."""
        updates: dict[str, Any] = {}
        for field in fields(instance):
            if field.name in RULE_FIELDS or field.name not in values:
                continue
            default_value = getattr(instance, field.name)
            raw = values[field.name]
            try:
                if isinstance(default_value, bool):
                    updates[field.name] = raw if isinstance(raw, bool) else str(raw).lower() in ("true", "1", "yes", "on")
                elif isinstance(default_value, int) and not isinstance(default_value, bool):
                    updates[field.name] = int(raw)
                elif isinstance(default_value, float):
                    updates[field.name] = float(raw)
                else:
                    updates[field.name] = raw
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Niepoprawna wartość parametru '{field.name}': {raw}") from exc
        return replace(instance, **updates)

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
            Path(target).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
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
        try:
            payload = json.loads(Path(source).read_text(encoding="utf-8"))
            config = payload.get("config", payload)
            self._apply_config(config)
            self.status_var.set(f"Wczytano konfigurację: {source}")
        except Exception as exc:
            messagebox.showerror("Błąd", f"Nie udało się wczytać konfiguracji: {exc}")
