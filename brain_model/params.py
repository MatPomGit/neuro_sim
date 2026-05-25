from dataclasses import dataclass, field

from .plasticity import ConnectivityAdaptationConfig, PlasticityRuleConfig


@dataclass
class BrainParams:
    """
    Parametry globalne modelu.
    """

    dt: float = 0.005
    noise: float = 0.015
    gw_threshold: float = 0.62
    gw_gain: float = 10.0
    learning_rate_semantic: float = 0.004
    learning_rate_value: float = 0.02
    decay_semantic: float = 0.001
    enable_oscillators: bool = True
    decision_threshold: float = 0.62
    confidence_gain: float = 1.8

    semantic_rule: PlasticityRuleConfig = field(default_factory=lambda: PlasticityRuleConfig(
        enabled=True,
        learning_rate=0.004,
        decay=0.001,
    ))
    value_rule: PlasticityRuleConfig = field(default_factory=lambda: PlasticityRuleConfig(
        enabled=True,
        learning_rate=0.02,
        decay=0.0,
    ))
    connectivity_adaptation: ConnectivityAdaptationConfig = field(default_factory=ConnectivityAdaptationConfig)
