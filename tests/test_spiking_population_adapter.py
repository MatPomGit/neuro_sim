from typing import Any

import numpy as np

from brain_core.populations.spiking_population import (
    Brian2SpikingPopulationAdapter,
    NeuralMassToSNNInput,
    SNNToNeuralMassOutput,
)
from brain_core.simulation.signal_adapter import (
    CouplingSignalAdapter,
    SNNPopulationMapping,
)


def test_signal_contract_and_shape_validation() -> Any:
    """Opis funkcji test_signal_contract_and_shape_validation."""
    adapter = Brian2SpikingPopulationAdapter(region_names=["HIP"], dt=0.001)
    signal = NeuralMassToSNNInput(
        excitatory_drive_hz=np.array([18.0]),
        inhibitory_drive_hz=np.array([6.0]),
        sync_dt=0.01,
    )

    out = adapter.step(signal)

    assert out.firing_rate_hz.shape == (1,)
    assert out.mean_membrane_potential_mv.shape == (1,)
    assert out.sync_dt == 0.01
    assert np.all(out.firing_rate_hz >= 0.0)


def test_pilot_circuit_is_single_deterministic_hippocampus_demo() -> Any:
    """Adapter SNN ma deterministyczne wyjście dla pojedynczego obwodu HIP."""
    signal = NeuralMassToSNNInput(
        excitatory_drive_hz=np.array([25.0]),
        inhibitory_drive_hz=np.array([7.0]),
        sync_dt=0.005,
    )
    first_adapter = Brian2SpikingPopulationAdapter(region_names=["HIP"], dt=0.001)
    second_adapter = Brian2SpikingPopulationAdapter(region_names=["HIP"], dt=0.001)

    first_out = first_adapter.step(signal)
    second_out = second_adapter.step(signal)

    assert first_out.firing_rate_hz.shape == (1,)
    assert np.allclose(first_out.firing_rate_hz, second_out.firing_rate_hz)
    assert np.allclose(
        first_out.mean_membrane_potential_mv,
        second_out.mean_membrane_potential_mv,
    )


def test_adapter_accepts_single_hip_region_as_tuple() -> None:
    """Adapter akceptuje jednoelementową krotkę z regionem HIP."""
    adapter = Brian2SpikingPopulationAdapter(region_names=("HIP",), dt=0.001)

    assert adapter.region_names == ["HIP"]


def test_coupling_adapter_roundtrip_mapping_and_units() -> Any:
    """Opis funkcji test_coupling_adapter_roundtrip_mapping_and_units."""
    mapping = SNNPopulationMapping(
        snn_region_names=("HIP",),
        neural_mass_region_names=("HIP", "ACC", "PCC"),
    )
    adapter = CouplingSignalAdapter(mapping=mapping, sync_dt=0.01)

    nm_to_snn = adapter.rate_to_spike_drive(
        excitatory_rate_hz=np.array([18.0, 6.0, 7.0]),
        inhibitory_rate_hz=np.array([5.0, 2.0, 2.0]),
    )
    assert np.allclose(nm_to_snn.excitatory_drive_hz, np.array([18.0]))
    assert np.allclose(nm_to_snn.inhibitory_drive_hz, np.array([5.0]))
    assert nm_to_snn.sync_dt == 0.01

    regional = adapter.spike_summary_to_regional_activity(
        SNNToNeuralMassOutput(
            firing_rate_hz=np.array([45.0]),
            mean_membrane_potential_mv=np.array([-62.0]),
            sync_dt=0.01,
        ),
        n_regions=3,
    )
    assert np.allclose(regional, np.array([0.45, 0.0, 0.0]))


def test_closed_loop_drive_is_finite_mapped_and_amplitude_limited() -> Any:
    """Adapter zamienia wyjście SNN na ograniczone wejście closed-loop dla HIP."""
    mapping = SNNPopulationMapping(
        snn_region_names=("HIP",),
        neural_mass_region_names=("VIS", "HIP", "GW"),
    )
    adapter = CouplingSignalAdapter(mapping=mapping, sync_dt=0.01)

    coupling_drive = adapter.spike_summary_to_closed_loop_drive(
        SNNToNeuralMassOutput(
            firing_rate_hz=np.array([100.0]),
            mean_membrane_potential_mv=np.array([-55.0]),
            sync_dt=0.01,
        ),
        n_regions=3,
        coupling_gain=np.array([1.0]),
        max_abs_amplitude=0.15,
    )

    assert coupling_drive.drive.shape == (3,)
    assert np.all(np.isfinite(coupling_drive.drive))
    assert coupling_drive.drive[0] == 0.0
    assert coupling_drive.drive[2] == 0.0
    assert coupling_drive.drive[1] == 0.15


def test_snn_report_section_compares_baseline_and_local_circuit() -> Any:
    """Raport demo ma zawierać porównanie przebiegu bez SNN i z obwodem lokalnym."""
    from brain_core.simulation.config_loader import load_config
    from brain_core.simulation.engine import run_experiment

    cfg = load_config("configs/snn_hippocampus_demo.yaml")
    cfg.output["save_results"] = False

    result = run_experiment(cfg)
    snn_comparison = result["analysis_report"]["snn_comparison"]

    assert snn_comparison["regions"] == ["HIP"]
    assert snn_comparison["requested_mode"] == "closed_loop"
    assert snn_comparison["computed_modes"] == [
        "baseline",
        "report_only_snn",
        "closed_loop_snn",
    ]
    assert "mode" not in snn_comparison
    assert snn_comparison["sync_dt_s"] == 0.010
    assert snn_comparison["max_feedback_amplitude"] == 0.15
    assert snn_comparison["input_rate_unit"] == "Hz"
    assert snn_comparison["output_activity_unit"] == "fraction"
    assert "HIP" in snn_comparison["region_differences"]
    assert snn_comparison["region_differences"]["HIP"]["max_abs_difference"] >= 0.0
    assert set(snn_comparison["mode_metrics"]) == {
        "baseline",
        "report_only_snn",
        "closed_loop_snn",
    }
    assert "HIP" in snn_comparison["mode_metrics"]["baseline"]
    assert "demonstracyjne" in snn_comparison["comparison_scope_pl"]
    assert "pełny model biologiczny" in snn_comparison["comparison_scope_pl"]


def test_snn_closed_loop_report_is_stable_and_deterministic() -> Any:
    """Demo SNN ma stabilne długości, brak NaN, limit sprzężenia i deterministykę."""
    from brain_core.simulation.config_loader import load_config
    from brain_core.simulation.engine import run_experiment

    cfg = load_config("configs/snn_hippocampus_demo.yaml")
    cfg.output["save_results"] = False
    cfg.task["duration"] = 1.0

    first = run_experiment(cfg)
    second = run_experiment(cfg)
    first_report = first["analysis_report"]["snn_comparison"]
    second_report = second["analysis_report"]["snn_comparison"]
    hip_modes = first_report["mode_metrics"]

    assert np.all(np.isfinite(first["activity"]))
    assert first["activity"].shape == second["activity"].shape
    for mode_name in ("baseline", "report_only_snn", "closed_loop_snn"):
        hip_metrics = hip_modes[mode_name]["HIP"]
        assert hip_metrics["length"] == first["activity"].shape[0]
        assert all(np.isfinite(value) for value in hip_metrics.values())
    assert (
        hip_modes["closed_loop_snn"]["HIP"]["max_abs_feedback_drive"]
        <= first_report["max_feedback_amplitude"]
    )
    assert first_report["mode_metrics"] == second_report["mode_metrics"]


def test_snn_report_only_request_marks_closed_loop_as_computed_variant() -> Any:
    """Raport rozdziela tryb żądany od pełnej listy wariantów porównawczych."""
    from brain_core.simulation.config_loader import load_config
    from brain_core.simulation.engine import run_experiment

    cfg = load_config("configs/snn_hippocampus_demo.yaml")
    cfg.output["save_results"] = False
    cfg.task["duration"] = 1.0
    cfg.snn["mode"] = "report_only"

    result = run_experiment(cfg)
    snn_comparison = result["analysis_report"]["snn_comparison"]

    assert snn_comparison["requested_mode"] == "report_only"
    assert snn_comparison["computed_modes"] == [
        "baseline",
        "report_only_snn",
        "closed_loop_snn",
    ]
    assert "mode" not in snn_comparison
    assert set(snn_comparison["mode_metrics"]) == set(snn_comparison["computed_modes"])


def test_snn_markdown_report_names_requested_and_computed_modes() -> Any:
    """Raport Markdown pokazuje tryb żądany i warianty faktycznie policzone."""
    from brain_core.analysis.reports import AnalysisReport

    report = AnalysisReport(
        {
            "snn_comparison": {
                "status_pl": "włączony demonstracyjny obwód SNN hipokampa",
                "regions": ["HIP"],
                "requested_mode": "report_only",
                "computed_modes": [
                    "baseline",
                    "report_only_snn",
                    "closed_loop_snn",
                ],
                "comparison_note_pl": (
                    "closed_loop_snn jest dodatkowym wariantem porównawczym "
                    "liczonym także dla report_only."
                ),
                "comparison_scope_pl": (
                    "SNN jest porównaniem demonstracyjnym, a nie pełnym modelem "
                    "biologicznym."
                ),
                "sync_dt_s": 0.01,
                "max_feedback_amplitude": 0.15,
                "input_rate_unit": "Hz",
                "output_activity_unit": "fraction",
                "mode_metrics": {
                    mode_name: {"HIP": {"length": 5, "max_activity": 0.1}}
                    for mode_name in (
                        "baseline",
                        "report_only_snn",
                        "closed_loop_snn",
                    )
                },
            }
        }
    )

    markdown = report.to_markdown()

    assert "żądany tryb SNN**: report_only" in markdown
    assert (
        "policzone warianty**: baseline, report_only_snn, closed_loop_snn" in markdown
    )
    assert "zakres porównania**" in markdown
    assert "pełnym modelem biologicznym" in markdown
    assert "uwaga porównawcza**" in markdown
    assert "dodatkowym wariantem porównawczym" in markdown
    assert "baseline" in markdown
    assert "report_only_snn" in markdown
    assert "closed_loop_snn" in markdown
