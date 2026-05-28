"""Uruchamianie symulacji GUI oraz podsumowania metryk."""

from __future__ import annotations

import json
import queue
import threading
import time as pytime
from dataclasses import replace
from tkinter import messagebox
from typing import Any

import numpy as np

from brain_core.simulation.config_loader import load_config_from_string
from brain_core.simulation.engine import run_experiment

from .io import build_output_dir, save_run
from .model import CognitiveBrainModel
from .oscillators import WilsonCowanParams
from .params import BrainParams


class GuiRunnerMixin:
    """Mixin odpowiadający za walidację, uruchomienie i metryki symulacji."""

    def _read_scalar_params(self) -> tuple[float, int, float]:
        """Odczytaj i zwaliduj czas, seed oraz krok czasowy symulacji."""
        try:
            T = float(self.T_var.get())
            seed = int(self.seed_var.get())
            dt = (
                self._auto_dt_for_duration(T)
                if self.auto_dt_var.get()
                else float(self.dt_var.get())
            )
        except ValueError as exc:
            raise ValueError("Niepoprawny czas symulacji, seed lub krok czasowy dt.") from exc

        if T <= 0:
            raise ValueError("Czas symulacji T musi być większy od zera.")
        if dt <= 0:
            raise ValueError("Krok czasowy dt musi być większy od zera.")
        if T < dt:
            raise ValueError("Czas symulacji T nie może być mniejszy od kroku czasowego dt.")

        return T, seed, dt

    def start_simulation(self) -> None:
        """Uruchom symulację w wątku roboczym."""
        if self._running:
            messagebox.showinfo("Informacja", "Symulacja już trwa.")
            return
        self._running = True
        self.status_var.set("Symulacja w toku...")
        self.progress_var.set(0)
        self.summary_var.set("")
        self._worker_thread = threading.Thread(target=self._run_simulation_worker, daemon=True)
        self._worker_thread.start()
        self.after(100, self._poll_worker)

    def _run_simulation_worker(self) -> None:
        """Wykonaj symulację lub batch i przekaż wynik do kolejki GUI."""
        try:
            T, seed, dt = self._read_scalar_params()
            self.brain_form.vars["dt"].set(str(dt))
            brain_params = self._build_brain_params()
            oscillator_params = self.osc_form.values()

            if brain_params.dt <= 0:
                raise ValueError("dt musi być większe od zera.")
            if brain_params.noise < 0:
                raise ValueError("noise nie może być ujemny.")
            if oscillator_params.oscillator_noise < 0:
                raise ValueError("oscillator_noise nie może być ujemny.")

            start = pytime.perf_counter()
            if self.command_var.get() == "run":
                config_doc = {
                    "model": {
                        "noise": brain_params.noise,
                        "gw_threshold": brain_params.gw_threshold,
                        "gw_gain": brain_params.gw_gain,
                    },
                    "integrator": {
                        "method": "euler",
                        "oscillator": {
                            "cognitive_drive_gain": oscillator_params.cognitive_drive_gain,
                            "oscillator_noise": oscillator_params.oscillator_noise,
                        },
                    },
                    "timestep": dt,
                    "seed": seed,
                    "task": {"scenario": self.scenario_var.get(), "duration": T},
                    "output": {"save_results": False, "label": "gui", "output_dir": "outputs"},
                }
                config_payload = json.dumps(config_doc)
                cfg = load_config_from_string(config_payload, format_hint="json")
                result = run_experiment(cfg, progress_callback=self._progress_single)
                model = result["model"]
                time = result["time"]
                activity = result["activity"]
                diagnostics = result["diagnostics"]
                oscillations = result["oscillations"]
                behavior = result["behavior"]
                summary_text = self._summarize_metrics(
                    [self._extract_metrics(diagnostics, behavior)]
                )
            else:
                runs, model, time, activity, diagnostics, oscillations, behavior = self._run_batch(
                    T=T,
                    base_params=brain_params,
                    oscillator_params=oscillator_params,
                )
                summary_text = self._summarize_metrics(runs)
            elapsed = pytime.perf_counter() - start

            save_info = None
            if self.save_results_var.get():
                try:
                    out_dir = build_output_dir(self.scenario_var.get(), "gui")
                    save_info = save_run(
                        out_dir,
                        time,
                        activity,
                        diagnostics,
                        oscillations,
                        extra_metadata={
                            "behavior": {
                                "decision": [str(v) for v in behavior["decision"]],
                                "latency": behavior["latency"].tolist(),
                                "confidence": behavior["confidence"].tolist(),
                                "decision_score": behavior["decision_score"].tolist(),
                                "decision_event": behavior["decision_event"].astype(int).tolist(),
                            }
                        },
                        model_params=model.p,
                        oscillator_params=model.oscillator_bank.params,
                        scenario=oscillations.get("metadata"),
                        seed=seed,
                        duration_s=elapsed,
                    )
                except Exception as exc:
                    self._result_queue.put(
                        ("warning", f"Nie udało się zapisać wyników symulacji: {exc}")
                    )

            msg = "Symulacja zakończona."
            if save_info:
                msg += f" Wyniki zapisane: {save_info['output_dir']}"
            payload = (
                msg,
                summary_text,
                save_info,
                model,
                time,
                activity,
                diagnostics,
                oscillations,
                behavior,
            )
            self._result_queue.put(("done", payload))

        except Exception as exc:
            self._result_queue.put(("error", str(exc)))

    def _progress_single(self, ratio: float) -> None:
        """Przekaż postęp pojedynczego uruchomienia do kolejki GUI."""
        self._result_queue.put(("progress", max(0.0, min(100.0, ratio * 100.0))))

    def _poll_worker(self) -> None:
        """Odbierz komunikaty z wątku roboczego i zaktualizuj GUI."""
        while True:
            try:
                kind, payload = self._result_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                self.progress_var.set(payload)
            elif kind == "done":
                self._running = False
                self._apply_run_result(payload)
            elif kind == "error":
                self._running = False
                self.status_var.set("Błąd konfiguracji.")
                messagebox.showerror("Błąd", payload)
            elif kind == "warning":
                messagebox.showwarning("Ostrzeżenie", payload)
        if self._running:
            self.after(100, self._poll_worker)

    def _extract_metrics(
        self, diagnostics: dict[str, Any], behavior: dict[str, Any]
    ) -> dict[str, float | int]:
        """Wylicz podstawowe metryki diagnostyczne i behawioralne."""
        return {
            "prediction_error_mean": float(np.mean(diagnostics["prediction_error"])),
            "gw_ignition_mean": float(np.mean(diagnostics["gw_ignition"])),
            "confidence_mean": float(np.mean(behavior["confidence"])),
            "decision_events": int(np.sum(behavior["decision_event"])),
        }

    def _summarize_metrics(self, runs: list[dict[str, float | int]]) -> str:
        """Zbuduj tekstowe podsumowanie średnich metryk uruchomień."""
        agg = {
            "prediction_error_mean": np.mean([r["prediction_error_mean"] for r in runs]),
            "gw_ignition_mean": np.mean([r["gw_ignition_mean"] for r in runs]),
            "confidence_mean": np.mean([r["confidence_mean"] for r in runs]),
            "decision_events": np.mean([r["decision_events"] for r in runs]),
        }
        return (
            f"Podsumowanie metryk:\n"
            f"mean(prediction_error)={agg['prediction_error_mean']:.4f}, "
            f"mean(gw_ignition)={agg['gw_ignition_mean']:.4f}, "
            f"mean(confidence)={agg['confidence_mean']:.4f}, "
            f"mean(decision_events)={agg['decision_events']:.2f}"
        )

    def _parse_list(self, raw: str) -> list[str]:
        """Podziel tekst z listą rozdzielaną przecinkami na wartości."""
        return [part.strip() for part in raw.split(",") if part.strip()]

    def _run_batch(
        self,
        T: float,
        base_params: BrainParams,
        oscillator_params: WilsonCowanParams,
    ) -> tuple[list[dict[str, float | int]], Any, Any, Any, Any, Any, Any]:
        """Wykonaj serię symulacji dla seedów, scenariuszy i perturbacji."""
        seeds = [int(s) for s in self._parse_list(self.batch_seeds_var.get())]
        scenarios = self._parse_list(self.batch_scenarios_var.get()) or [self.scenario_var.get()]
        sens_params = self._parse_list(self.sensitivity_var.get())
        delta = float(self.sensitivity_delta_var.get())
        base_total = len(seeds) * len(scenarios)
        perturb_total = base_total * len(sens_params) * 2
        total_runs = base_total + perturb_total if sens_params else base_total
        completed = 0
        metrics = []
        last = None
        for scenario in scenarios:
            for seed in seeds:
                model = CognitiveBrainModel(
                    params=base_params,
                    oscillator_params=oscillator_params,
                    seed=seed,
                    stimulus=scenario,
                )
                time, activity, diagnostics, oscillations, behavior = model.simulate(T=T)
                metrics.append(self._extract_metrics(diagnostics, behavior))
                last = (model, time, activity, diagnostics, oscillations, behavior)
                completed += 1
                self._progress_single(completed / total_runs)
                for p_name in sens_params:
                    if not hasattr(base_params, p_name):
                        continue
                    base_val = getattr(base_params, p_name)
                    for sign in (-1.0, 1.0):
                        perturbed = replace(
                            base_params, **{p_name: base_val * (1.0 + sign * delta)}
                        )
                        model = CognitiveBrainModel(
                            params=perturbed,
                            oscillator_params=oscillator_params,
                            seed=seed,
                            stimulus=scenario,
                        )
                        _, _, diag_p, _, beh_p = model.simulate(T=T)
                        metrics.append(self._extract_metrics(diag_p, beh_p))
                        completed += 1
                        self._progress_single(completed / total_runs)
        if last is None:
            raise ValueError("Batch nie wygenerował żadnych przebiegów.")
        return metrics, *last
