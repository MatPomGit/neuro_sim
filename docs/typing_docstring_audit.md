# Audyt type hints i docstringów

Raport wejściowy do implementacji uzupełniania adnotacji typów i docstringów. Priorytety: **P1** oznacza elementy publiczne albo powiązane z konfiguracją, I/O, raportowaniem, GUI/CLI lub uruchamianiem symulacji; **P2** oznacza elementy wewnętrzne, prywatne helpery, testy oraz lokalne szczegóły implementacji.

## Podsumowanie statusu
- Łącznie sprawdzono **95** plików `*.py`.
- **Wprowadzone / zgodne z audytem:** 95 plików bez wykrytych braków.
- **Do wprowadzenia:** 0 plików z brakami.
- **Ostatnia weryfikacja:** 2026-05-29 — lokalny skan AST potwierdził 0 braków docstringów oraz 0 braków type hints dla funkcji, klas i metod objętych audytem.

## Lista plików `*.py` według modułów
### `analysis`
- `analysis/reports.py`

### `brain_core`
- `brain_core/__init__.py`
- `brain_core/analysis/__init__.py`
- `brain_core/analysis/benchmark_loader.py`
- `brain_core/analysis/connectivity.py`
- `brain_core/analysis/information_flow.py`
- `brain_core/analysis/phase_locking.py`
- `brain_core/analysis/reports.py`
- `brain_core/analysis/signal_metrics.py`
- `brain_core/analysis/spectral.py`
- `brain_core/anatomy/__init__.py`
- `brain_core/anatomy/atlases.py`
- `brain_core/anatomy/connectome.py`
- `brain_core/anatomy/regions.py`
- `brain_core/cognition/__init__.py`
- `brain_core/cognition/mapping.py`
- `brain_core/experiments/__init__.py`
- `brain_core/experiments/lesions.py`
- `brain_core/experiments/pharmacology.py`
- `brain_core/experiments/protocols.py`
- `brain_core/networks/__init__.py`
- `brain_core/networks/delays.py`
- `brain_core/networks/structural_network.py`
- `brain_core/physiology/__init__.py`
- `brain_core/physiology/bold_hrf.py`
- `brain_core/physiology/eeg_forward_model.py`
- `brain_core/physiology/neurovascular_coupling.py`
- `brain_core/populations/__init__.py`
- `brain_core/populations/spiking_population.py`
- `brain_core/populations/wilson_cowan.py`
- `brain_core/simulation/__init__.py`
- `brain_core/simulation/config_loader.py`
- `brain_core/simulation/config_schema.py`
- `brain_core/simulation/engine.py`
- `brain_core/simulation/integrators.py`
- `brain_core/simulation/multiscale_engine.py`
- `brain_core/simulation/random_sources.py`
- `brain_core/simulation/run.py`
- `brain_core/simulation/scheduler.py`
- `brain_core/simulation/signal_adapter.py`
- `brain_core/simulation/state.py`
- `brain_core/synapses/__init__.py`
- `brain_core/synapses/acetylcholine.py`
- `brain_core/synapses/adrenaline.py`
- `brain_core/synapses/cortisol.py`
- `brain_core/synapses/dopamine.py`
- `brain_core/synapses/gaba_glutamate.py`
- `brain_core/synapses/noradrenaline.py`
- `brain_core/synapses/plasticity.py`
- `brain_core/synapses/serotonin.py`
- `brain_core/synapses/state.py`

### `brain_model`
- `brain_model/__init__.py`
- `brain_model/activations.py`
- `brain_model/behavior.py`
- `brain_model/calibration.py`
- `brain_model/connectivity.py`
- `brain_model/gui.py`
- `brain_model/gui_app.py`
- `brain_model/gui_config.py`
- `brain_model/gui_forms.py`
- `brain_model/gui_layout.py`
- `brain_model/gui_runner.py`
- `brain_model/gui_state.py`
- `brain_model/io.py`
- `brain_model/model.py`
- `brain_model/modules.py`
- `brain_model/oscillators.py`
- `brain_model/params.py`
- `brain_model/plasticity.py`
- `brain_model/plotting.py`
- `brain_model/report.py`
- `brain_model/report_export.py`
- `brain_model/scenarios/__init__.py`
- `brain_model/scenarios/library.py`
- `brain_model/scenarios/types.py`
- `brain_model/stimuli.py`
- `brain_model/validation.py`

### `brain_viewer`
- `brain_viewer/mapping.py`

### `root`
- `brain_model.py`
- `main.py`
- `main_gui.py`

### `scripts`
- `scripts/sync_web_defaults.py`

### `tests`
- `tests/test_atlas_connectome.py`
- `tests/test_gui_layout_static.py`
- `tests/test_gui_state.py`
- `tests/test_lesions.py`
- `tests/test_multiscale_engine.py`
- `tests/test_neuromodulation.py`
- `tests/test_observation_and_analysis.py`
- `tests/test_plasticity_protocols.py`
- `tests/test_signal_metrics_modules.py`
- `tests/test_spiking_population_adapter.py`
- `tests/test_task_protocols_and_engine.py`
- `tests/test_task_stimulus_player.py`
- `tests/test_wilson_cowan_network.py`

## Status wdrożenia według plików
### `analysis`
- `analysis/reports.py` — wprowadzone / brak braków.

### `brain_core`
- `brain_core/__init__.py` — wprowadzone / brak braków.
- `brain_core/analysis/__init__.py` — wprowadzone / brak braków.
- `brain_core/analysis/benchmark_loader.py` — wprowadzone / brak braków.
- `brain_core/analysis/connectivity.py` — wprowadzone / brak braków.
- `brain_core/analysis/information_flow.py` — wprowadzone / brak braków.
- `brain_core/analysis/phase_locking.py` — wprowadzone / brak braków.
- `brain_core/analysis/reports.py` — wprowadzone / brak braków.
- `brain_core/analysis/signal_metrics.py` — wprowadzone / brak braków.
- `brain_core/analysis/spectral.py` — wprowadzone / brak braków.
- `brain_core/anatomy/__init__.py` — wprowadzone / brak braków.
- `brain_core/anatomy/atlases.py` — wprowadzone / brak braków.
- `brain_core/anatomy/connectome.py` — wprowadzone / brak braków.
- `brain_core/anatomy/regions.py` — wprowadzone / brak braków.
- `brain_core/cognition/__init__.py` — wprowadzone / brak braków.
- `brain_core/cognition/mapping.py` — wprowadzone / brak braków.
- `brain_core/experiments/__init__.py` — wprowadzone / brak braków.
- `brain_core/experiments/lesions.py` — wprowadzone / brak braków.
- `brain_core/experiments/pharmacology.py` — wprowadzone / brak braków.
- `brain_core/experiments/protocols.py` — wprowadzone / brak braków.
- `brain_core/networks/__init__.py` — wprowadzone / brak braków.
- `brain_core/networks/delays.py` — wprowadzone / brak braków.
- `brain_core/networks/structural_network.py` — wprowadzone / brak braków.
- `brain_core/physiology/__init__.py` — wprowadzone / brak braków.
- `brain_core/physiology/bold_hrf.py` — wprowadzone / brak braków.
- `brain_core/physiology/eeg_forward_model.py` — wprowadzone / brak braków.
- `brain_core/physiology/neurovascular_coupling.py` — wprowadzone / brak braków.
- `brain_core/populations/__init__.py` — wprowadzone / brak braków.
- `brain_core/populations/spiking_population.py` — wprowadzone / brak braków.
- `brain_core/populations/wilson_cowan.py` — wprowadzone / brak braków.
- `brain_core/simulation/__init__.py` — wprowadzone / brak braków.
- `brain_core/simulation/config_loader.py` — wprowadzone / brak braków.
- `brain_core/simulation/config_schema.py` — wprowadzone / brak braków.
- `brain_core/simulation/engine.py` — wprowadzone / brak braków.
- `brain_core/simulation/integrators.py` — wprowadzone / brak braków.
- `brain_core/simulation/multiscale_engine.py` — wprowadzone / brak braków.
- `brain_core/simulation/random_sources.py` — wprowadzone / brak braków.
- `brain_core/simulation/run.py` — wprowadzone / brak braków.
- `brain_core/simulation/scheduler.py` — wprowadzone / brak braków.
- `brain_core/simulation/signal_adapter.py` — wprowadzone / brak braków.
- `brain_core/simulation/state.py` — wprowadzone / brak braków.
- `brain_core/synapses/__init__.py` — wprowadzone / brak braków.
- `brain_core/synapses/acetylcholine.py` — wprowadzone / brak braków.
- `brain_core/synapses/adrenaline.py` — wprowadzone / brak braków.
- `brain_core/synapses/cortisol.py` — wprowadzone / brak braków.
- `brain_core/synapses/dopamine.py` — wprowadzone / brak braków.
- `brain_core/synapses/gaba_glutamate.py` — wprowadzone / brak braków.
- `brain_core/synapses/noradrenaline.py` — wprowadzone / brak braków.
- `brain_core/synapses/plasticity.py` — wprowadzone / brak braków.
- `brain_core/synapses/serotonin.py` — wprowadzone / brak braków.
- `brain_core/synapses/state.py` — wprowadzone / brak braków.

### `brain_model`
- `brain_model/__init__.py` — wprowadzone / brak braków.
- `brain_model/activations.py` — wprowadzone / brak braków.
- `brain_model/behavior.py` — wprowadzone / brak braków.
- `brain_model/calibration.py` — wprowadzone / brak braków.
- `brain_model/connectivity.py` — wprowadzone / brak braków.
- `brain_model/gui.py` — wprowadzone / brak braków.
- `brain_model/gui_app.py` — wprowadzone / brak braków.
- `brain_model/gui_config.py` — wprowadzone / brak braków.
- `brain_model/gui_forms.py` — wprowadzone / brak braków.
- `brain_model/gui_layout.py` — wprowadzone / brak braków.
- `brain_model/gui_runner.py` — wprowadzone / brak braków.
- `brain_model/gui_state.py` — wprowadzone / brak braków.
- `brain_model/io.py` — wprowadzone / brak braków.
- `brain_model/model.py` — wprowadzone / brak braków.
- `brain_model/modules.py` — wprowadzone / brak braków.
- `brain_model/oscillators.py` — wprowadzone / brak braków.
- `brain_model/params.py` — wprowadzone / brak braków.
- `brain_model/plasticity.py` — wprowadzone / brak braków.
- `brain_model/plotting.py` — wprowadzone / brak braków.
- `brain_model/report.py` — wprowadzone / brak braków.
- `brain_model/report_export.py` — wprowadzone / brak braków.
- `brain_model/scenarios/__init__.py` — wprowadzone / brak braków.
- `brain_model/scenarios/library.py` — wprowadzone / brak braków.
- `brain_model/scenarios/types.py` — wprowadzone / brak braków.
- `brain_model/stimuli.py` — wprowadzone / brak braków.
- `brain_model/validation.py` — wprowadzone / brak braków.

### `brain_viewer`
- `brain_viewer/mapping.py` — wprowadzone / brak braków.

### `root`
- `brain_model.py` — wprowadzone / brak braków.
- `main.py` — wprowadzone / brak braków.
- `main_gui.py` — wprowadzone / brak braków.

### `scripts`
- `scripts/sync_web_defaults.py` — wprowadzone / brak braków.

### `tests`
- `tests/test_atlas_connectome.py` — wprowadzone / brak braków.
- `tests/test_gui_layout_static.py` — wprowadzone / brak braków.
- `tests/test_gui_state.py` — wprowadzone / brak braków.
- `tests/test_lesions.py` — wprowadzone / brak braków.
- `tests/test_multiscale_engine.py` — wprowadzone / brak braków.
- `tests/test_neuromodulation.py` — wprowadzone / brak braków.
- `tests/test_observation_and_analysis.py` — wprowadzone / brak braków.
- `tests/test_plasticity_protocols.py` — wprowadzone / brak braków.
- `tests/test_signal_metrics_modules.py` — wprowadzone / brak braków.
- `tests/test_spiking_population_adapter.py` — wprowadzone / brak braków.
- `tests/test_task_protocols_and_engine.py` — wprowadzone / brak braków.
- `tests/test_task_stimulus_player.py` — wprowadzone / brak braków.
- `tests/test_wilson_cowan_network.py` — wprowadzone / brak braków.

## Zakres braków według plików
### `analysis/reports.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/benchmark_loader.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/connectivity.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/information_flow.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/phase_locking.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/reports.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/signal_metrics.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/analysis/spectral.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/anatomy/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/anatomy/atlases.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/anatomy/connectome.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/anatomy/regions.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/cognition/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/cognition/mapping.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/experiments/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/experiments/lesions.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/experiments/pharmacology.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/experiments/protocols.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/networks/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/networks/delays.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/networks/structural_network.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/physiology/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/physiology/bold_hrf.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/physiology/eeg_forward_model.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/physiology/neurovascular_coupling.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/populations/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/populations/spiking_population.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/populations/wilson_cowan.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/config_loader.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/config_schema.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/engine.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/integrators.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/multiscale_engine.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/random_sources.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/run.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/scheduler.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/signal_adapter.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/state.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/acetylcholine.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/adrenaline.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/cortisol.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/dopamine.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/gaba_glutamate.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/noradrenaline.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/plasticity.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/serotonin.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/synapses/state.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/activations.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/behavior.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/calibration.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/connectivity.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_app.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_config.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_forms.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_layout.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_runner.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_state.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/io.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/model.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/modules.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/oscillators.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/params.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/plasticity.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/plotting.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/report.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/report_export.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/scenarios/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/scenarios/library.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/scenarios/types.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/stimuli.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/validation.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_viewer/mapping.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `main.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `main_gui.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `scripts/sync_web_defaults.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_atlas_connectome.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_gui_layout_static.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_gui_state.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_lesions.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_multiscale_engine.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_neuromodulation.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_observation_and_analysis.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_plasticity_protocols.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_signal_metrics_modules.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_spiking_population_adapter.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_task_protocols_and_engine.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_task_stimulus_player.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `tests/test_wilson_cowan_network.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.
