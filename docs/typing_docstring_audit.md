# Audyt typing i docstringów (wejście do implementacji)

## Lista plików Python (podział na moduły)

### brain_core
- `brain_core/__init__.py`
- `brain_core/analysis/__init__.py`
- `brain_core/analysis/benchmark_loader.py`
- `brain_core/analysis/connectivity.py`
- `brain_core/analysis/information_flow.py`
- `brain_core/analysis/phase_locking.py`
- `brain_core/analysis/reports.py`
- `brain_core/analysis/signal_metrics.py`
- `brain_core/analysis/spectral.py`
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

### brain_model
- `brain_model/__init__.py`
- `brain_model/activations.py`
- `brain_model/behavior.py`
- `brain_model/calibration.py`
- `brain_model/connectivity.py`
- `brain_model/gui.py`
- `brain_model/io.py`
- `brain_model/model.py`
- `brain_model/modules.py`
- `brain_model/oscillators.py`
- `brain_model/params.py`
- `brain_model/plasticity.py`
- `brain_model/plotting.py`
- `brain_model/report.py`
- `brain_model/scenarios/__init__.py`
- `brain_model/scenarios/library.py`
- `brain_model/scenarios/types.py`
- `brain_model/stimuli.py`
- `brain_model/validation.py`

### tests
- `tests/test_atlas_connectome.py`
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

### scripts
- `scripts/sync_web_defaults.py`

### analysis
- `analysis/reports.py`

### brain_viewer
- `brain_viewer/mapping.py`

### root
- `brain_model.py`
- `main.py`
- `main_gui.py`
- `run_gui.py`

## Braki per plik

### `brain_core/analysis/benchmark_loader.py`
- [P1] Klasa `BenchmarkValidationError` (10): brak docstringu.

### `brain_core/analysis/reports.py`
- [P1] Klasa `AnalysisReport` (20): brak docstringu.
- [P1] Metoda `AnalysisReport.to_json` (23): brak docstringu.
- [P1] Metoda `AnalysisReport.to_markdown` (26): brak docstringu.
- [P1] Metoda `AnalysisReport.to_csv_rows` (38): brak docstringu.

### `brain_core/anatomy/connectome.py`
- [P1] Klasa `Connectome` (9): brak docstringu.

### `brain_core/anatomy/regions.py`
- [P1] Klasa `BrainRegion` (7): brak docstringu.
- [P1] Klasa `RegionAtlas` (13): brak docstringu.
- [P1] Metoda `RegionAtlas.names` (17): brak docstringu.
- [P1] Metoda `RegionAtlas.tau_vector` (21): brak docstringu.

### `brain_core/experiments/lesions.py`
- [P1] Metoda `PathologyMutation.apply` (26): brak docstringu.
- [P2] Metoda `PathologyMutation._apply_region` (32): brak docstringu.
- [P2] Metoda `PathologyMutation._apply_edge` (52): brak docstringu.
- [P2] Metoda `PathologyController.__init__` (75): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `PathologyController.apply_pre_simulation` (79): brak docstringu.
- [P1] Metoda `PathologyController.apply_runtime` (83): brak docstringu.
- [P1] Klasa `PathologyController`: potencjalnie brak adnotacji istotnych atrybutów instancji: pre_simulation, runtime.

### `brain_core/experiments/pharmacology.py`
- [P1] Klasa `PharmacologyIntervention` (9): brak docstringu.
- [P1] Metoda `PharmacologyIntervention.apply` (19): brak docstringu.

### `brain_core/experiments/protocols.py`
- [P1] Klasa `ProtocolPhase` (8): brak docstringu.
- [P1] Klasa `ProtocolPhase` (8): brak adnotacji pól klasowych: TEST, TRAIN.
- [P1] Klasa `ErrorType` (13): brak docstringu.
- [P1] Klasa `ErrorType` (13): brak adnotacji pól klasowych: COMMISSION, INTERFERENCE, NONE, OMISSION.
- [P1] Klasa `ProtocolStep` (21): brak docstringu.
- [P1] Klasa `TrialStimulus` (28): brak docstringu.
- [P1] Klasa `TrialResult` (37): brak docstringu.
- [P1] Klasa `CognitiveTask` (45): brak docstringu.
- [P1] Metoda `CognitiveTask.generate_stimuli` (48): brak docstringu.
- [P1] Metoda `CognitiveTask.expected_response` (50): brak docstringu.
- [P1] Metoda `CognitiveTask.score_trial` (52): brak docstringu.
- [P1] Klasa `ExperimentProtocol` (56): brak docstringu.
- [P1] Metoda `ExperimentProtocol.total_duration` (60): brak docstringu.
- [P1] Klasa `StroopTask` (70): brak docstringu.
- [P1] Klasa `StroopTask` (70): brak adnotacji pól klasowych: name.
- [P1] Metoda `StroopTask.generate_stimuli` (73): brak docstringu.
- [P1] Metoda `StroopTask.expected_response` (90): brak docstringu.
- [P1] Metoda `StroopTask.score_trial` (93): brak docstringu.
- [P1] Klasa `GoNoGoTask` (102): brak docstringu.
- [P1] Klasa `GoNoGoTask` (102): brak adnotacji pól klasowych: name.
- [P1] Metoda `GoNoGoTask.generate_stimuli` (105): brak docstringu.
- [P1] Metoda `GoNoGoTask.expected_response` (119): brak docstringu.
- [P1] Metoda `GoNoGoTask.score_trial` (122): brak docstringu.
- [P1] Klasa `NBackTask` (133): brak docstringu.
- [P1] Klasa `NBackTask` (133): brak adnotacji pól klasowych: name.
- [P2] Metoda `NBackTask.__init__` (136): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `NBackTask.generate_stimuli` (141): brak docstringu.
- [P1] Metoda `NBackTask.expected_response` (160): brak docstringu.
- [P1] Metoda `NBackTask.score_trial` (163): brak docstringu.
- [P1] Klasa `NBackTask`: potencjalnie brak adnotacji istotnych atrybutów instancji: n.

### `brain_core/networks/delays.py`
- [P2] Metoda `DelayBuffer.__init__` (9): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `DelayBuffer.push` (20): brak docstringu.
- [P1] Metoda `DelayBuffer.delayed_activity_matrix` (26): brak docstringu.
- [P1] Klasa `DelayBuffer`: potencjalnie brak adnotacji istotnych atrybutów instancji: delays_steps, max_delay.

### `brain_core/networks/structural_network.py`
- [P2] Metoda `StructuralNetwork.__init__` (9): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `StructuralNetwork.coupling` (16): brak docstringu.
- [P1] Klasa `StructuralNetwork`: potencjalnie brak adnotacji istotnych atrybutów instancji: connectivity, region_names.

### `brain_core/physiology/eeg_forward_model.py`
- [P2] Metoda `EEGForwardModel.__init__` (21): brak docstringu.
- [P1] Metoda `EEGForwardModel.n_sensors` (31): brak docstringu.
- [P1] Metoda `EEGForwardModel.n_sources` (35): brak docstringu.
- [P2] Metoda `EEGForwardModel._apply_reference` (38): brak docstringu.
- [P1] Metoda `EEGForwardModel.project` (47): brak docstringu.
- [P1] Klasa `EEGForwardModel`: potencjalnie brak adnotacji istotnych atrybutów instancji: config, leadfield.
- [P2] Metoda `EEGInverseSolver.__init__` (69): brak docstringu.
- [P2] Metoda `EEGInverseSolver._solve` (75): brak docstringu.
- [P1] Klasa `EEGInverseSolver`: potencjalnie brak adnotacji istotnych atrybutów instancji: leadfield.

### `brain_core/populations/spiking_population.py`
- [P1] Klasa `Brian2SpikingPopulationAdapter` (26): brak adnotacji pól klasowych: backend_name.
- [P2] Metoda `Brian2SpikingPopulationAdapter.__init__` (35): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `Brian2SpikingPopulationAdapter.step` (46): brak docstringu.
- [P2] Metoda `Brian2SpikingPopulationAdapter._validate_input` (62): brak docstringu.
- [P1] Klasa `Brian2SpikingPopulationAdapter`: potencjalnie brak adnotacji istotnych atrybutów instancji: dt, region_names.

### `brain_core/populations/wilson_cowan.py`
- [P1] Klasa `RegionWilsonCowanParams` (9): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel.__init__` (25): brak docstringu; brak adnotacji wartości zwracanej.
- [P2] Metoda `RegionWilsonCowanModel._tau_E` (39): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._tau_I` (43): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._w_EE` (47): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._w_EI` (51): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._w_IE` (55): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._w_II` (59): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._gain_E` (63): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._gain_I` (67): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._threshold_E` (71): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._threshold_I` (75): brak docstringu.
- [P2] Metoda `RegionWilsonCowanModel._sigmoid` (79): brak docstringu.
- [P1] Metoda `RegionWilsonCowanModel.step` (98): brak docstringu.
- [P1] Klasa `RegionWilsonCowanModel`: potencjalnie brak adnotacji istotnych atrybutów instancji: E, I, params, region_names.

### `brain_core/simulation/integrators.py`
- [P2] Metoda `DynamicsFn.__call__` (14): brak docstringu.
- [P2] Metoda `NoiseFn.__call__` (20): brak docstringu.
- [P1] Metoda `BaseIntegrator.step` (26): brak docstringu.

### `brain_core/simulation/multiscale_engine.py`
- [P1] Metoda `TimeScaleModule.update` (41): brak docstringu.
- [P2] Metoda `MultiScaleEngine.__init__` (74): brak adnotacji wartości zwracanej.
- [P1] Klasa `MultiScaleEngine`: potencjalnie brak adnotacji istotnych atrybutów instancji: base_dt, io_contract, tasks.

### `brain_core/simulation/scheduler.py`
- [P1] Metoda `SimulationModule.update` (14): brak docstringu.
- [P1] Klasa `TaskStimulusPlayer`: potencjalnie brak adnotacji istotnych atrybutów instancji: stimuli.

### `brain_core/simulation/signal_adapter.py`
- [P1] Klasa `CouplingSignalAdapter` (28): brak adnotacji pól klasowych: MAX_FIRING_RATE_HZ.
- [P2] Metoda `CouplingSignalAdapter.__init__` (39): brak docstringu; brak adnotacji wartości zwracanej.
- [P2] Metoda `CouplingSignalAdapter._validate_nm_vector` (75): brak docstringu.
- [P1] Klasa `CouplingSignalAdapter`: potencjalnie brak adnotacji istotnych atrybutów instancji: mapping, sync_dt.

### `brain_core/synapses/plasticity.py`
- [P1] Klasa `NeuralMassPlasticityConfig` (9): brak docstringu.
- [P1] Klasa `PlasticityTracker` (21): brak docstringu.
- [P1] Metoda `PlasticityTracker.record` (25): brak docstringu.

### `brain_core/synapses/state.py`
- [P1] Klasa `NeuromodulationState` (15): brak docstringu.
- [P1] Klasa `NeuromodulationConfig` (27): brak docstringu.

### `brain_model/activations.py`
- [P1] Funkcja `sigmoid` (4): brak adnotacji parametrów: z, beta; brak adnotacji wartości zwracanej.

### `brain_model/connectivity.py`
- [P1] Funkcja `build_connectivity` (9): brak adnotacji parametrów: names; brak adnotacji wartości zwracanej.

### `brain_model/gui.py`
- [P1] Klasa `Tooltip` (98): brak docstringu.
- [P1] Metoda `Tooltip.__init__` (99): brak docstringu; brak adnotacji parametrów: widget; brak adnotacji wartości zwracanej.
- [P1] Metoda `Tooltip.show` (106): brak docstringu; brak adnotacji parametrów: event; brak adnotacji wartości zwracanej.
- [P1] Metoda `Tooltip.hide` (124): brak docstringu; brak adnotacji parametrów: event; brak adnotacji wartości zwracanej.
- [P1] Klasa `Tooltip`: potencjalnie brak adnotacji istotnych atrybutów instancji: text, tip, widget.
- [P1] Metoda `ParameterForm.__init__` (133): brak docstringu; brak adnotacji parametrów: parent, dataclass_type, defaults, include_fields; brak adnotacji wartości zwracanej.
- [P1] Metoda `ParameterForm.values` (162): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `ParameterForm.reset` (184): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Klasa `ParameterForm`: potencjalnie brak adnotacji istotnych atrybutów instancji: dataclass_type, defaults, include_fields.
- [P1] Metoda `BrainModelGUI.__init__` (196): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._build_layout` (214): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._build_menu` (399): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._focus_plots_section` (427): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._open_advanced_settings` (431): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._refresh_scenario_details` (463): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._auto_dt_for_duration` (473): brak docstringu.
- [P1] Metoda `BrainModelGUI._on_auto_dt_toggle` (478): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._open_new_instance` (486): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._collect_config` (495): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._apply_config` (513): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._save_current_config` (539): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._load_existing_config` (558): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._show_usage_help` (570): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._show_about` (585): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI.reset_defaults` (596): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._build_brain_params` (615): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._read_scalar_params` (624): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI.start_simulation` (641): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._run_simulation_worker` (653): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._progress_single` (731): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._poll_worker` (734): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._apply_run_result` (754): brak docstringu; brak adnotacji parametrów: payload; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._extract_metrics` (845): brak docstringu; brak adnotacji parametrów: diagnostics, behavior; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._summarize_metrics` (853): brak docstringu; brak adnotacji parametrów: runs; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._parse_list` (868): brak docstringu; brak adnotacji wartości zwracanej.
- [P1] Metoda `BrainModelGUI._run_batch` (871): brak docstringu; brak adnotacji parametrów: T, base_params, oscillator_params; brak adnotacji wartości zwracanej.
- [P1] Klasa `BrainModelGUI`: potencjalnie brak adnotacji istotnych atrybutów instancji: T_var, auto_dt_var, batch_scenarios_var, batch_seeds_var, brain_defaults, brain_form, command_var, dt_var, osc_defaults, osc_form, plot_panel, plots_frame, progress, progress_var, save_results_var, scenario_combo, scenario_details_var, scenario_var, seed_var, sensitivity_delta_var, sensitivity_var, sim_frame, status_var, summary_var, tabs.
- [P1] Funkcja `run_gui` (906): brak adnotacji wartości zwracanej.

### `brain_model/model.py`
- [P1] Klasa `CognitiveBrainModel`: potencjalnie brak adnotacji istotnych atrybutów instancji: W, idx, n, names, oscillator_bank, p, rng, scenario, scenario_id, stimulus_fn, tau.

### `brain_model/oscillators.py`
- [P1] Klasa `WilsonCowanOscillatorBank`: potencjalnie brak adnotacji istotnych atrybutów instancji: band_map, connectivity, frequency, idx, module_bands, module_names, n, params, tau_e, tau_i.

### `brain_model/plasticity.py`
- [P1] Klasa `PlasticityRuleConfig` (8): brak docstringu.
- [P1] Klasa `HebbianRuleConfig` (15): brak docstringu.
- [P1] Klasa `ConnectivityAdaptationConfig` (23): brak docstringu.
- [P1] Funkcja `apply_state_learning` (33): brak adnotacji parametrów: dx, x, diagnostics, params, idx; brak adnotacji wartości zwracanej.
- [P1] Funkcja `update_connectivity` (48): brak adnotacji parametrów: W, x, diagnostics, params, idx; brak adnotacji wartości zwracanej.
- [P1] Funkcja `build_weight_history_series` (80): brak adnotacji wartości zwracanej.

### `brain_model/plotting.py`
- [P1] Klasa `PlotWindow`: potencjalnie brak adnotacji istotnych atrybutów instancji: notebook, status.

### `brain_model/scenarios/library.py`
- [P1] Funkcja `list_scenarios` (117): brak adnotacji wartości zwracanej.

### `brain_model/scenarios/types.py`
- [P1] Klasa `TimeWindow` (11): brak docstringu.
- [P1] Metoda `TimeWindow.contains` (15): brak docstringu.
- [P1] Klasa `Pulse` (20): brak docstringu.
- [P1] Klasa `ChannelProfile` (26): brak docstringu.
- [P1] Klasa `StimulusPerturbation` (32): brak docstringu.
- [P1] Klasa `StimulusScenario` (40): brak docstringu.
- [P1] Metoda `StimulusScenario.normalized_channels` (55): brak docstringu.
- [P1] Metoda `StimulusScenario.to_metadata` (58): brak docstringu.

### `brain_model.py`
- [P2] Klasa `CognitiveBrainModel`: potencjalnie brak adnotacji istotnych atrybutów instancji: W, idx, n, names, p, rng, tau.

### `brain_viewer/mapping.py`
- [P2] Klasa `BrainRegionMapper` (3): brak docstringu.
- [P2] Metoda `BrainRegionMapper.__init__` (4): brak docstringu; brak adnotacji parametrów: module_names, region_names, mapping_matrix; brak adnotacji wartości zwracanej.
- [P2] Metoda `BrainRegionMapper.modules_to_regions` (9): brak adnotacji parametrów: module_activity; brak adnotacji wartości zwracanej.
- [P2] Klasa `BrainRegionMapper`: potencjalnie brak adnotacji istotnych atrybutów instancji: M, module_names, region_names.

### `tests/test_multiscale_engine.py`
- [P2] Klasa `CounterModule`: potencjalnie brak adnotacji istotnych atrybutów instancji: steps.

## Legenda priorytetów
- **P1**: element krytyczny (publiczne API, konfiguracja, I/O, warstwa wejścia/wyjścia).
- **P2**: element wewnętrzny (helpery, prywatne metody, kod testowy/wewnętrzny).