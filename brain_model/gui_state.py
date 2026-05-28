"""Stan danych używany przez GUI modelu poznawczego."""

from __future__ import annotations

from dataclasses import dataclass, field

from .oscillators import WilsonCowanParams
from .params import BrainParams


@dataclass
class GuiState:
    """Przechowuje edytowalny stan GUI niezależnie od widżetów formularza."""

    T: str = "12.0"
    dt: str = field(default_factory=lambda: str(BrainParams().dt))
    auto_dt: bool = True
    seed: str = "7"
    command: str = "run"
    scenario: str = "baseline"
    save_results: bool = True
    brain_params: BrainParams = field(default_factory=BrainParams)
    oscillator_params: WilsonCowanParams = field(default_factory=WilsonCowanParams)
    plots: dict[str, bool] = field(default_factory=dict)
    batch_seeds: str = "7,11,19"
    batch_scenarios: str = "reward-learning"
    sensitivity_params: str = "noise,gw_threshold"
    sensitivity_delta: str = "0.1"
