from dataclasses import dataclass


@dataclass
class BrainParams:
    """
    Parametry globalne modelu.

    dt:
        Krok czasowy symulacji.
    noise:
        Skala szumu neuronalnego.
    gw_threshold:
        Próg nieliniowego zapłonu global workspace.
    gw_gain:
        Stromość funkcji zapłonu global workspace.
    learning_rate_semantic:
        Powolne uczenie semantyczne.
    learning_rate_value:
        Uczenie wartościowania na podstawie błędu predykcji nagrody.
    decay_semantic:
        Powolny zanik aktywacji/śladu semantycznego.
    enable_oscillators:
        Czy symulować oscylatory Wilsona-Cowana dla modułów poznawczych.
    """

    dt: float = 0.005
    noise: float = 0.015
    gw_threshold: float = 0.62
    gw_gain: float = 10.0
    learning_rate_semantic: float = 0.004
    learning_rate_value: float = 0.02
    decay_semantic: float = 0.001
    enable_oscillators: bool = True
