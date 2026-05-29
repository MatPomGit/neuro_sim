# Audyt type hints i docstringów

Raport wejściowy do implementacji uzupełniania adnotacji typów i docstringów. Priorytety: **P1** oznacza elementy publiczne albo powiązane z konfiguracją, I/O, raportowaniem, GUI/CLI lub uruchamianiem symulacji; **P2** oznacza elementy wewnętrzne, prywatne helpery, testy oraz lokalne szczegóły implementacji.

## Podsumowanie statusu
- Łącznie sprawdzono **95** plików `*.py`.
- **Wprowadzone / zgodne z audytem:** 73 pliki bez wykrytych braków.
- **Do wprowadzenia:** 22 pliki z brakami; w tym 19 plików z priorytetem P1 i 3 pliki wyłącznie z priorytetem P2.

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
- `brain_core/experiments/lesions.py` — do wprowadzenia — P1/P2.
- `brain_core/experiments/pharmacology.py` — wprowadzone / brak braków.
- `brain_core/experiments/protocols.py` — do wprowadzenia — P1/P2.
- `brain_core/networks/__init__.py` — wprowadzone / brak braków.
- `brain_core/networks/delays.py` — do wprowadzenia — P1/P2.
- `brain_core/networks/structural_network.py` — do wprowadzenia — P1/P2.
- `brain_core/physiology/__init__.py` — wprowadzone / brak braków.
- `brain_core/physiology/bold_hrf.py` — wprowadzone / brak braków.
- `brain_core/physiology/eeg_forward_model.py` — wprowadzone / brak braków.
- `brain_core/physiology/neurovascular_coupling.py` — wprowadzone / brak braków.
- `brain_core/populations/__init__.py` — wprowadzone / brak braków.
- `brain_core/populations/spiking_population.py` — do wprowadzenia — P1/P2.
- `brain_core/populations/wilson_cowan.py` — do wprowadzenia — P1/P2.
- `brain_core/simulation/__init__.py` — wprowadzone / brak braków.
- `brain_core/simulation/config_loader.py` — wprowadzone / brak braków.
- `brain_core/simulation/config_schema.py` — wprowadzone / brak braków.
- `brain_core/simulation/engine.py` — wprowadzone / brak braków.
- `brain_core/simulation/integrators.py` — wprowadzone / brak braków.
- `brain_core/simulation/multiscale_engine.py` — do wprowadzenia — P1/P2.
- `brain_core/simulation/random_sources.py` — do wprowadzenia — P2.
- `brain_core/simulation/run.py` — wprowadzone / brak braków.
- `brain_core/simulation/scheduler.py` — do wprowadzenia — P1/P2.
- `brain_core/simulation/signal_adapter.py` — do wprowadzenia — P1/P2.
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
- `brain_model/gui_app.py` — do wprowadzenia — P1/P2.
- `brain_model/gui_config.py` — wprowadzone / brak braków.
- `brain_model/gui_forms.py` — do wprowadzenia — P1/P2.
- `brain_model/gui_layout.py` — do wprowadzenia — P1/P2.
- `brain_model/gui_runner.py` — do wprowadzenia — P2.
- `brain_model/gui_state.py` — wprowadzone / brak braków.
- `brain_model/io.py` — wprowadzone / brak braków.
- `brain_model/model.py` — do wprowadzenia — P1/P2.
- `brain_model/modules.py` — wprowadzone / brak braków.
- `brain_model/oscillators.py` — do wprowadzenia — P1/P2.
- `brain_model/params.py` — wprowadzone / brak braków.
- `brain_model/plasticity.py` — do wprowadzenia — P1/P2.
- `brain_model/plotting.py` — do wprowadzenia — P1/P2.
- `brain_model/report.py` — wprowadzone / brak braków.
- `brain_model/report_export.py` — wprowadzone / brak braków.
- `brain_model/scenarios/__init__.py` — wprowadzone / brak braków.
- `brain_model/scenarios/library.py` — wprowadzone / brak braków.
- `brain_model/scenarios/types.py` — do wprowadzenia — P1/P2.
- `brain_model/stimuli.py` — wprowadzone / brak braków.
- `brain_model/validation.py` — wprowadzone / brak braków.

### `brain_viewer`
- `brain_viewer/mapping.py` — do wprowadzenia — P1/P2.

### `root`
- `brain_model.py` — do wprowadzenia — P1/P2.
- `main.py` — wprowadzone / brak braków.
- `main_gui.py` — wprowadzone / brak braków.

### `scripts`
- `scripts/sync_web_defaults.py` — wprowadzone / brak braków.

### `tests`
- `tests/test_atlas_connectome.py` — wprowadzone / brak braków.
- `tests/test_gui_layout_static.py` — wprowadzone / brak braków.
- `tests/test_gui_state.py` — wprowadzone / brak braków.
- `tests/test_lesions.py` — wprowadzone / brak braków.
- `tests/test_multiscale_engine.py` — do wprowadzenia — P2.
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
- Status: **do wprowadzenia**.
- **P1** (linia 116): metoda `PathologyController.__init__` — brak type hintów: `return`.
- **P1** (linia 123): atrybut instancji `PathologyController.pre_simulation` — brak jawnej adnotacji pola.
- **P1** (linia 124): atrybut instancji `PathologyController.runtime` — brak jawnej adnotacji pola.

### `brain_core/experiments/pharmacology.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/experiments/protocols.py`
- Status: **do wprowadzenia**.
- **P1** (linia 148): pole klasowe `StroopTask.name` — brak adnotacji typu.
- **P1** (linia 192): pole klasowe `GoNoGoTask.name` — brak adnotacji typu.
- **P1** (linia 217): metoda `GoNoGoTask.score_trial` — brak docstringu metody.
- **P1** (linia 228): klasa `NBackTask` — brak docstringu klasy.
- **P1** (linia 229): pole klasowe `NBackTask.name` — brak adnotacji typu.
- **P1** (linia 231): metoda `NBackTask.__init__` — brak docstringu metody; brak type hintów: `return`.
- **P1** (linia 234): atrybut instancji `NBackTask.n` — brak jawnej adnotacji pola.
- **P1** (linia 236): metoda `NBackTask.generate_stimuli` — brak docstringu metody.
- **P1** (linia 255): metoda `NBackTask.expected_response` — brak docstringu metody.
- **P1** (linia 258): metoda `NBackTask.score_trial` — brak docstringu metody.

### `brain_core/networks/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/networks/delays.py`
- Status: **do wprowadzenia**.
- **P1** (linia 18): metoda `DelayBuffer.__init__` — brak type hintów: `return`.

### `brain_core/networks/structural_network.py`
- Status: **do wprowadzenia**.
- **P1** (linia 15): metoda `StructuralNetwork.__init__` — brak type hintów: `return`.
- **P1** (linia 29): atrybut instancji `StructuralNetwork.region_names` — brak jawnej adnotacji pola.
- **P1** (linia 30): atrybut instancji `StructuralNetwork.connectivity` — brak jawnej adnotacji pola.

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
- Status: **do wprowadzenia**.
- **P1** (linia 55): pole klasowe `Brian2SpikingPopulationAdapter.backend_name` — brak adnotacji typu.
- **P2** (linia 103): metoda `Brian2SpikingPopulationAdapter._validate_input` — brak docstringu metody.

### `brain_core/populations/wilson_cowan.py`
- Status: **do wprowadzenia**.
- **P1** (linia 50): metoda `RegionWilsonCowanModel.__init__` — brak type hintów: `return`.
- **P2** (linia 74): metoda `RegionWilsonCowanModel._tau_E` — brak docstringu metody.
- **P2** (linia 78): metoda `RegionWilsonCowanModel._tau_I` — brak docstringu metody.
- **P2** (linia 82): metoda `RegionWilsonCowanModel._w_EE` — brak docstringu metody.
- **P2** (linia 86): metoda `RegionWilsonCowanModel._w_EI` — brak docstringu metody.
- **P2** (linia 90): metoda `RegionWilsonCowanModel._w_IE` — brak docstringu metody.
- **P2** (linia 94): metoda `RegionWilsonCowanModel._w_II` — brak docstringu metody.
- **P2** (linia 98): metoda `RegionWilsonCowanModel._gain_E` — brak docstringu metody.
- **P2** (linia 102): metoda `RegionWilsonCowanModel._gain_I` — brak docstringu metody.
- **P2** (linia 106): metoda `RegionWilsonCowanModel._threshold_E` — brak docstringu metody.
- **P2** (linia 110): metoda `RegionWilsonCowanModel._threshold_I` — brak docstringu metody.

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
- Status: **do wprowadzenia**.
- **P1** (linia 132): atrybut instancji `MultiScaleEngine.base_dt` — brak jawnej adnotacji pola.
- **P1** (linia 133): atrybut instancji `MultiScaleEngine.tasks` — brak jawnej adnotacji pola.
- **P1** (linia 134): atrybut instancji `MultiScaleEngine.io_contract` — brak jawnej adnotacji pola.

### `brain_core/simulation/random_sources.py`
- Status: **do wprowadzenia**.
- **P2** (linia 32): atrybut instancji `RandomSources._root` — brak jawnej adnotacji pola.

### `brain_core/simulation/run.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_core/simulation/scheduler.py`
- Status: **do wprowadzenia**.
- **P1** (linia 45): atrybut instancji `TaskStimulusPlayer.stimuli` — brak jawnej adnotacji pola.

### `brain_core/simulation/signal_adapter.py`
- Status: **do wprowadzenia**.
- **P1** (linia 37): pole klasowe `CouplingSignalAdapter.MAX_FIRING_RATE_HZ` — brak adnotacji typu.
- **P1** (linia 43): atrybut instancji `CouplingSignalAdapter.mapping` — brak jawnej adnotacji pola.
- **P1** (linia 44): atrybut instancji `CouplingSignalAdapter.sync_dt` — brak jawnej adnotacji pola.
- **P2** (linia 45): atrybut instancji `CouplingSignalAdapter._indices` — brak jawnej adnotacji pola.

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
- Status: **do wprowadzenia**.
- **P1** (linia 29): atrybut instancji `BrainModelGUI.brain_defaults` — brak jawnej adnotacji pola.
- **P1** (linia 30): atrybut instancji `BrainModelGUI.osc_defaults` — brak jawnej adnotacji pola.
- **P1** (linia 32): atrybut instancji `BrainModelGUI.state` — brak jawnej adnotacji pola.
- **P2** (linia 41): atrybut instancji `BrainModelGUI._running` — brak jawnej adnotacji pola.

### `brain_model/gui_config.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/gui_forms.py`
- Status: **do wprowadzenia**.
- **P1** (linia 65): atrybut instancji `Tooltip.widget` — brak jawnej adnotacji pola.
- **P1** (linia 66): atrybut instancji `Tooltip.text` — brak jawnej adnotacji pola.
- **P1** (linia 67): atrybut instancji `Tooltip.tip` — brak jawnej adnotacji pola.
- **P1** (linia 110): atrybut instancji `ParameterForm.dataclass_type` — brak jawnej adnotacji pola.
- **P1** (linia 111): atrybut instancji `ParameterForm.defaults` — brak jawnej adnotacji pola.
- **P1** (linia 113): atrybut instancji `ParameterForm.include_fields` — brak jawnej adnotacji pola.

### `brain_model/gui_layout.py`
- Status: **do wprowadzenia**.
- **P1** (linia 151): atrybut instancji `GuiLayoutMixin.tabs` — brak jawnej adnotacji pola.
- **P1** (linia 204): atrybut instancji `GuiLayoutMixin.status_var` — brak jawnej adnotacji pola.
- **P1** (linia 205): atrybut instancji `GuiLayoutMixin.status_label` — brak jawnej adnotacji pola.
- **P1** (linia 209): atrybut instancji `GuiLayoutMixin.progress_var` — brak jawnej adnotacji pola.
- **P1** (linia 210): atrybut instancji `GuiLayoutMixin.progress` — brak jawnej adnotacji pola.
- **P1** (linia 218): atrybut instancji `GuiLayoutMixin.summary_var` — brak jawnej adnotacji pola.
- **P1** (linia 228): atrybut instancji `GuiLayoutMixin.plot_panel` — brak jawnej adnotacji pola.
- **P1** (linia 233): atrybut instancji `GuiLayoutMixin.sim_frame` — brak jawnej adnotacji pola.
- **P1** (linia 238): atrybut instancji `GuiLayoutMixin.T_var` — brak jawnej adnotacji pola.
- **P1** (linia 239): atrybut instancji `GuiLayoutMixin.scenario_var` — brak jawnej adnotacji pola.
- **P1** (linia 240): atrybut instancji `GuiLayoutMixin.save_results_var` — brak jawnej adnotacji pola.
- **P1** (linia 245): atrybut instancji `GuiLayoutMixin.scenario_combo` — brak jawnej adnotacji pola.
- **P1** (linia 274): atrybut instancji `GuiLayoutMixin.scenario_details_var` — brak jawnej adnotacji pola.
- **P1** (linia 288): atrybut instancji `GuiLayoutMixin.advanced_options_visible_var` — brak jawnej adnotacji pola.
- **P1** (linia 298): atrybut instancji `GuiLayoutMixin.advanced_options_frame` — brak jawnej adnotacji pola.
- **P1** (linia 303): atrybut instancji `GuiLayoutMixin.seed_var` — brak jawnej adnotacji pola.
- **P1** (linia 304): atrybut instancji `GuiLayoutMixin.dt_var` — brak jawnej adnotacji pola.
- **P1** (linia 305): atrybut instancji `GuiLayoutMixin.auto_dt_var` — brak jawnej adnotacji pola.
- **P1** (linia 306): atrybut instancji `GuiLayoutMixin.command_var` — brak jawnej adnotacji pola.
- **P1** (linia 307): atrybut instancji `GuiLayoutMixin.batch_seeds_var` — brak jawnej adnotacji pola.
- **P1** (linia 308): atrybut instancji `GuiLayoutMixin.batch_scenarios_var` — brak jawnej adnotacji pola.
- **P1** (linia 309): atrybut instancji `GuiLayoutMixin.sensitivity_var` — brak jawnej adnotacji pola.
- **P1** (linia 310): atrybut instancji `GuiLayoutMixin.sensitivity_delta_var` — brak jawnej adnotacji pola.
- **P1** (linia 412): atrybut instancji `GuiLayoutMixin.plots_frame` — brak jawnej adnotacji pola.
- **P1** (linia 435): atrybut instancji `GuiLayoutMixin.plot_preset_var` — brak jawnej adnotacji pola.

### `brain_model/gui_runner.py`
- Status: **do wprowadzenia**.
- **P2** (linia 60): atrybut instancji `GuiRunnerMixin._running` — brak jawnej adnotacji pola.
- **P2** (linia 65): atrybut instancji `GuiRunnerMixin._worker_thread` — brak jawnej adnotacji pola.

### `brain_model/gui_state.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/io.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/model.py`
- Status: **do wprowadzenia**.
- **P1** (linia 41): atrybut instancji `CognitiveBrainModel.p` — brak jawnej adnotacji pola.
- **P1** (linia 42): atrybut instancji `CognitiveBrainModel.rng` — brak jawnej adnotacji pola.
- **P1** (linia 44): atrybut instancji `CognitiveBrainModel.names` — brak jawnej adnotacji pola.
- **P1** (linia 45): atrybut instancji `CognitiveBrainModel.idx` — brak jawnej adnotacji pola.
- **P1** (linia 46): atrybut instancji `CognitiveBrainModel.n` — brak jawnej adnotacji pola.
- **P1** (linia 48): atrybut instancji `CognitiveBrainModel.tau` — brak jawnej adnotacji pola.
- **P1** (linia 49): atrybut instancji `CognitiveBrainModel.W` — brak jawnej adnotacji pola.
- **P1** (linia 51): atrybut instancji `CognitiveBrainModel.scenario_id` — brak jawnej adnotacji pola.
- **P1** (linia 52): atrybut instancji `CognitiveBrainModel.scenario` — brak jawnej adnotacji pola.
- **P1** (linia 56): atrybut instancji `CognitiveBrainModel.stimulus_fn` — brak jawnej adnotacji pola.
- **P1** (linia 70): atrybut instancji `CognitiveBrainModel.oscillator_bank` — brak jawnej adnotacji pola.

### `brain_model/modules.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/oscillators.py`
- Status: **do wprowadzenia**.
- **P1** (linia 93): atrybut instancji `WilsonCowanOscillatorBank.module_names` — brak jawnej adnotacji pola.
- **P1** (linia 94): atrybut instancji `WilsonCowanOscillatorBank.idx` — brak jawnej adnotacji pola.
- **P1** (linia 95): atrybut instancji `WilsonCowanOscillatorBank.n` — brak jawnej adnotacji pola.
- **P1** (linia 96): atrybut instancji `WilsonCowanOscillatorBank.connectivity` — brak jawnej adnotacji pola.
- **P1** (linia 97): atrybut instancji `WilsonCowanOscillatorBank.band_map` — brak jawnej adnotacji pola.
- **P1** (linia 98): atrybut instancji `WilsonCowanOscillatorBank.params` — brak jawnej adnotacji pola.
- **P1** (linia 100): atrybut instancji `WilsonCowanOscillatorBank.module_bands` — brak jawnej adnotacji pola.
- **P1** (linia 101): atrybut instancji `WilsonCowanOscillatorBank.frequency` — brak jawnej adnotacji pola.
- **P1** (linia 102): atrybut instancji `WilsonCowanOscillatorBank.tau_e` — brak jawnej adnotacji pola.
- **P1** (linia 103): atrybut instancji `WilsonCowanOscillatorBank.tau_i` — brak jawnej adnotacji pola.

### `brain_model/params.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/plasticity.py`
- Status: **do wprowadzenia**.
- **P1** (linia 9): klasa `PlasticityRuleConfig` — brak docstringu klasy.
- **P1** (linia 16): klasa `HebbianRuleConfig` — brak docstringu klasy.
- **P1** (linia 24): klasa `ConnectivityAdaptationConfig` — brak docstringu klasy.

### `brain_model/plotting.py`
- Status: **do wprowadzenia**.
- **P1** (linia 553): atrybut instancji `PlotWindow.notebook` — brak jawnej adnotacji pola.
- **P1** (linia 556): atrybut instancji `PlotWindow.status` — brak jawnej adnotacji pola.
- **P2** (linia 563): atrybut instancji `PlotWindow._figures` — brak jawnej adnotacji pola.
- **P2** (linia 564): atrybut instancji `PlotWindow._canvases` — brak jawnej adnotacji pola.

### `brain_model/report.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/report_export.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/scenarios/__init__.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/scenarios/library.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/scenarios/types.py`
- Status: **do wprowadzenia**.
- **P1** (linia 11): klasa `TimeWindow` — brak docstringu klasy.
- **P1** (linia 15): metoda `TimeWindow.contains` — brak docstringu metody.
- **P1** (linia 20): klasa `Pulse` — brak docstringu klasy.
- **P1** (linia 26): klasa `ChannelProfile` — brak docstringu klasy.
- **P1** (linia 32): klasa `StimulusPerturbation` — brak docstringu klasy.
- **P1** (linia 40): klasa `StimulusScenario` — brak docstringu klasy.
- **P1** (linia 55): metoda `StimulusScenario.normalized_channels` — brak docstringu metody.
- **P1** (linia 58): metoda `StimulusScenario.to_metadata` — brak docstringu metody.

### `brain_model/stimuli.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model/validation.py`
- Status: **wprowadzone / brak wykrytych braków w zakresie audytu**.

### `brain_model.py`
- Status: **do wprowadzenia**.
- **P1** (linia 61): atrybut instancji `CognitiveBrainModel.p` — brak jawnej adnotacji pola.
- **P1** (linia 62): atrybut instancji `CognitiveBrainModel.rng` — brak jawnej adnotacji pola.
- **P1** (linia 64): atrybut instancji `CognitiveBrainModel.names` — brak jawnej adnotacji pola.
- **P1** (linia 68): atrybut instancji `CognitiveBrainModel.idx` — brak jawnej adnotacji pola.
- **P1** (linia 69): atrybut instancji `CognitiveBrainModel.n` — brak jawnej adnotacji pola.
- **P1** (linia 71): atrybut instancji `CognitiveBrainModel.tau` — brak jawnej adnotacji pola.
- **P1** (linia 90): atrybut instancji `CognitiveBrainModel.W` — brak jawnej adnotacji pola.

### `brain_viewer/mapping.py`
- Status: **do wprowadzenia**.
- **P1** (linia 4): klasa `BrainRegionMapper` — brak docstringu klasy.
- **P1** (linia 5): metoda `BrainRegionMapper.__init__` — brak docstringu metody.
- **P1** (linia 8): atrybut instancji `BrainRegionMapper.module_names` — brak jawnej adnotacji pola.
- **P1** (linia 9): atrybut instancji `BrainRegionMapper.region_names` — brak jawnej adnotacji pola.
- **P1** (linia 10): atrybut instancji `BrainRegionMapper.M` — brak jawnej adnotacji pola.

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
- Status: **do wprowadzenia**.
- **P2** (linia 15): atrybut instancji `CounterModule.steps` — brak jawnej adnotacji pola.

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
