from __future__ import annotations

from dataclasses import dataclass

from .acetylcholine import acetylcholine_effect
from .adrenaline import adrenaline_effect
from .cortisol import cortisol_effect
from .dopamine import dopamine_effect
from .gaba_glutamate import gaba_glutamate_effect
from .noradrenaline import noradrenaline_effect
from .serotonin import serotonin_effect


@dataclass(slots=True)
class NeuromodulationState:
    """Poziomy neuromodulatorów przypisane do pojedynczego regionu."""

    dopamine: float = 0.5
    noradrenaline: float = 0.5
    acetylcholine: float = 0.5
    serotonin: float = 0.5
    gaba: float = 0.5
    glutamate: float = 0.5
    cortisol: float = 0.5
    adrenaline: float = 0.5


@dataclass(slots=True)
class NeuromodulationConfig:
    """Konfiguracja tempa aktualizacji stanu neuromodulacji."""

    update_rate: float = 0.15


def create_region_state(region_names: list[str], default_level: float = 0.5) -> dict[str, NeuromodulationState]:
    """Tworzy początkowy stan neuromodulacji dla listy regionów."""
    return {
        region: NeuromodulationState(
            dopamine=default_level,
            noradrenaline=default_level,
            acetylcholine=default_level,
            serotonin=default_level,
            gaba=default_level,
            glutamate=default_level,
            cortisol=default_level,
            adrenaline=default_level,
        )
        for region in region_names
    }


def update_region_state(
    current: NeuromodulationState,
    reward_prediction_error: float,
    prediction_error: float,
    threat_signal: float,
    satiety_signal: float,
    attention_drive: float,
    novelty_drive: float,
    inhibition_drive: float,
    excitation_drive: float,
    arousal_signal: float,
    config: NeuromodulationConfig | None = None,
) -> NeuromodulationState:
    """Aktualizuje stan neuromodulacji regionu na podstawie sygnałów wejściowych."""
    cfg = config or NeuromodulationConfig()
    target_dopamine = dopamine_effect(reward_prediction_error, current.dopamine)
    target_noradrenaline = noradrenaline_effect(prediction_error, threat_signal, current.noradrenaline)
    target_ach = acetylcholine_effect(attention_drive, novelty_drive, current.acetylcholine)
    target_serotonin = serotonin_effect(threat_signal, satiety_signal, current.serotonin)
    target_gaba, target_glu = gaba_glutamate_effect(inhibition_drive, excitation_drive, current.gaba, current.glutamate)
    target_cortisol = cortisol_effect(threat_signal, prediction_error, target_serotonin, current.cortisol)
    target_adrenaline = adrenaline_effect(threat_signal, arousal_signal, target_noradrenaline, current.adrenaline)

    a = max(0.0, min(1.0, cfg.update_rate))
    return NeuromodulationState(
        dopamine=(1.0 - a) * current.dopamine + a * target_dopamine,
        noradrenaline=(1.0 - a) * current.noradrenaline + a * target_noradrenaline,
        acetylcholine=(1.0 - a) * current.acetylcholine + a * target_ach,
        serotonin=(1.0 - a) * current.serotonin + a * target_serotonin,
        gaba=(1.0 - a) * current.gaba + a * target_gaba,
        glutamate=(1.0 - a) * current.glutamate + a * target_glu,
        cortisol=(1.0 - a) * current.cortisol + a * target_cortisol,
        adrenaline=(1.0 - a) * current.adrenaline + a * target_adrenaline,
    )
