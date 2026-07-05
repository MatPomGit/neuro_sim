"""Obsługa zbierania, stosowania oraz zapisu konfiguracji GUI."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, fields, replace
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any, TypeVar

from .gui_forms import APP_VERSION, COMMAND_LABELS, COMMAND_VALUES, RULE_FIELDS

if TYPE_CHECKING:
    from .oscillators import WilsonCowanParams
    from .params import BrainParams

TDataclass = TypeVar("TDataclass")


@dataclass(frozen=True)
class _PreparedConfigStateValues:
    """Przechowuje zwalidowane wartości konfiguracji przed mutacją stanu GUI.

    Parameters
    ----------
    T:
        Tekstowa wartość czasu trwania symulacji.
    dt:
        Tekstowa wartość kroku czasowego zachowywana w stanie GUI.
    auto_dt:
        Flaga automatycznego doboru kroku czasowego.
    seed:
        Tekstowa wartość ziarna losowości.
    command:
        Techniczna nazwa komendy uruchamianej z GUI.
    batch_seeds:
        Tekstowa lista ziaren dla uruchomień seryjnych.
    batch_scenarios:
        Tekstowa lista scenariuszy dla uruchomień seryjnych.
    sensitivity_params:
        Tekstowa lista parametrów analizy wrażliwości.
    sensitivity_delta:
        Tekstowa wartość zmiany parametru analizy wrażliwości.
    scenario:
        Techniczna nazwa scenariusza eksperymentalnego.
    save_results:
        Flaga zapisu artefaktów eksperymentu.
    brain_params:
        Parametry modelu mózgu po konwersji typów i ustawieniu `dt`.
    oscillator_params:
        Parametry oscylatorów po konwersji typów.
    plots:
        Zestaw wykresów po konwersji wartości logicznych.
    """

    T: str
    dt: str
    auto_dt: bool
    seed: str
    command: str
    batch_seeds: str
    batch_scenarios: str
    sensitivity_params: str
    sensitivity_delta: str
    scenario: str
    save_results: bool
    brain_params: "BrainParams"
    oscillator_params: "WilsonCowanParams"
    plots: dict[str, bool]


class GuiConfigMixin:
    """Mixin zachowujący format konfiguracji GUI w plikach JSON."""

    def _sync_state_from_controls(self) -> None:
        """Przepisz wartości z widocznych kontrolek głównego okna do stanu GUI."""
        self.state.T = self.T_var.get()
        self.state.dt = self.dt_var.get()
        self.state.auto_dt = bool(self.auto_dt_var.get())
        self.state.seed = self.seed_var.get()
        self.state.command = COMMAND_VALUES.get(
            self.command_var.get(), self.command_var.get()
        )
        self.state.batch_seeds = self.batch_seeds_var.get()
        self.state.batch_scenarios = self.batch_scenarios_var.get()
        self.state.sensitivity_params = self.sensitivity_var.get()
        self.state.sensitivity_delta = self.sensitivity_delta_var.get()
        self.state.scenario = self.scenario_var.get()
        self.state.save_results = bool(self.save_results_var.get())
        self.state.plots = {
            name: bool(var.get()) for name, var in self.plot_vars.items()
        }

    def _sync_controls_from_state(self) -> None:
        """Przepisz stan GUI do widocznych kontrolek głównego okna."""
        self.T_var.set(self.state.T)
        self.dt_var.set(self.state.dt)
        self.auto_dt_var.set(self.state.auto_dt)
        self.seed_var.set(self.state.seed)
        self.command_var.set(COMMAND_LABELS.get(self.state.command, self.state.command))
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
        self.state.brain_params = replace(edited_brain_params, dt=current_dt)
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
                **self._editable_dataclass_values(
                    self.state.brain_params, exclude=RULE_FIELDS
                ),
                "dt": self.state.dt,
            },
            "oscillator_params": self._editable_dataclass_values(
                self.state.oscillator_params
            ),
            "plots": dict(self.state.plots),
        }

    def _validate_dt_value(self, raw_dt: Any) -> float:
        """Sprawdź krok symulacji przed zastosowaniem konfiguracji GUI.

        Parameters
        ----------
        raw_dt:
            Wartość kroku czasowego odczytana z konfiguracji albo kontrolki GUI.

        Returns:
        -------
        float
            Skończona, dodatnia wartość kroku czasowego.

        Raises:
        ------
        ValueError
            Gdy wartość nie jest liczbą skończoną większą od zera.
        """
        if isinstance(raw_dt, bool):
            raise ValueError(
                f"Niepoprawna wartość dt: {raw_dt}. "
                "Wymagana jest liczba skończona większa od zera."
            )
        try:
            dt_value = float(raw_dt)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Niepoprawna wartość dt: {raw_dt}. "
                "Wymagana jest liczba skończona większa od zera."
            ) from exc
        if not math.isfinite(dt_value) or dt_value <= 0.0:
            raise ValueError(
                f"Niepoprawna wartość dt: {raw_dt}. "
                "Wymagana jest liczba skończona większa od zera."
            )
        return dt_value

    def _apply_config(self, config: dict[str, Any]) -> None:
        """Zastosuj konfigurację odczytaną z JSON do stanu i kontrolek GUI."""
        prepared_values = self._prepare_config_state_values(config)

        self.state.T = prepared_values.T
        self.state.dt = prepared_values.dt
        self.state.seed = prepared_values.seed
        self.state.auto_dt = prepared_values.auto_dt
        self.state.command = prepared_values.command
        self.state.batch_seeds = prepared_values.batch_seeds
        self.state.batch_scenarios = prepared_values.batch_scenarios
        self.state.sensitivity_params = prepared_values.sensitivity_params
        self.state.sensitivity_delta = prepared_values.sensitivity_delta
        self.state.scenario = prepared_values.scenario
        self.state.save_results = prepared_values.save_results
        self.state.brain_params = prepared_values.brain_params
        self.state.oscillator_params = prepared_values.oscillator_params
        self.state.plots = prepared_values.plots
        self._sync_controls_from_state()
        self._refresh_scenario_details()
        self._on_auto_dt_toggle()

    def _prepare_config_state_values(
        self, config: dict[str, Any]
    ) -> _PreparedConfigStateValues:
        """Przygotuj komplet wartości konfiguracji przed zmianą stanu GUI.

        Parameters
        ----------
        config:
            Słownik konfiguracji odczytany z pliku JSON GUI.

        Returns:
        -------
        _PreparedConfigStateValues
            Zwalidowane i przekonwertowane wartości gotowe do atomowego przypisania
            do `self.state`.

        Raises:
        ------
        ValueError
            Gdy `dt` albo pole parametrów modelu ma niepoprawny typ lub wartość.
        """
        raw_dt = config.get("dt", self.state.dt)
        dt_value = self._validate_dt_value(raw_dt)

        new_brain_params = self._dataclass_with_updates(
            self.state.brain_params, config.get("brain_params", {})
        )
        new_brain_params = replace(new_brain_params, dt=dt_value)
        new_oscillator_params = self._dataclass_with_updates(
            self.state.oscillator_params, config.get("oscillator_params", {})
        )
        new_plots = dict(self.state.plots)
        new_plots.update(
            {
                name: bool(value)
                for name, value in config.get("plots", {}).items()
                if name in self.plot_vars
            }
        )

        return _PreparedConfigStateValues(
            T=str(config.get("T", self.state.T)),
            dt=str(raw_dt),
            auto_dt=bool(config.get("auto_dt", self.state.auto_dt)),
            seed=str(config.get("seed", self.state.seed)),
            command=str(config.get("command", self.state.command)),
            batch_seeds=str(config.get("batch_seeds", self.state.batch_seeds)),
            batch_scenarios=str(
                config.get("batch_scenarios", self.state.batch_scenarios)
            ),
            sensitivity_params=str(
                config.get("sensitivity_params", self.state.sensitivity_params)
            ),
            sensitivity_delta=str(
                config.get("sensitivity_delta", self.state.sensitivity_delta)
            ),
            scenario=str(config.get("scenario", self.state.scenario)),
            save_results=bool(config.get("save_results", self.state.save_results)),
            brain_params=new_brain_params,
            oscillator_params=new_oscillator_params,
            plots=new_plots,
        )

    def _editable_dataclass_values(
        self, instance: Any, exclude: tuple[str, ...] = ()
    ) -> dict[str, Any]:
        """Zwróć słownik prostych pól dataclass przeznaczonych do zapisu w konfiguracji."""
        return {
            field.name: getattr(instance, field.name)
            for field in fields(instance)
            if field.name not in exclude
        }

    def _dataclass_with_updates(
        self, instance: TDataclass, values: dict[str, Any]
    ) -> TDataclass:
        """Zbuduj kopię dataclass z wartościami przekonwertowanymi jak w formularzu GUI."""
        updates: dict[str, Any] = {}
        for field in fields(instance):
            if field.name in RULE_FIELDS or field.name not in values:
                continue
            default_value = getattr(instance, field.name)
            raw = values[field.name]
            try:
                if isinstance(default_value, bool):
                    updates[field.name] = (
                        raw
                        if isinstance(raw, bool)
                        else str(raw).lower() in ("true", "1", "yes", "on")
                    )
                elif isinstance(default_value, int) and not isinstance(
                    default_value, bool
                ):
                    updates[field.name] = int(raw)
                elif isinstance(default_value, float):
                    updates[field.name] = float(raw)
                else:
                    updates[field.name] = raw
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Niepoprawna wartość parametru '{field.name}': {raw}"
                ) from exc
        return replace(instance, **updates)

    def _save_current_config(self) -> None:
        """Zapisz bieżącą konfigurację GUI do pliku JSON."""
        default_name = f"brain_model_config_{date.today().isoformat()}.json"
        target = filedialog.asksaveasfilename(
            title="Zapisz konfigurację",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("Pliki JSON", "*.json"), ("Wszystkie pliki", "*.*")],
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
            filetypes=[("Pliki JSON", "*.json"), ("Wszystkie pliki", "*.*")],
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
