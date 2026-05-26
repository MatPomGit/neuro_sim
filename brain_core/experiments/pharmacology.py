from __future__ import annotations

from dataclasses import dataclass

from brain_core.synapses.state import NeuromodulationState


@dataclass(frozen=True, slots=True)
class PharmacologyIntervention:
    dopamine_shift: float = 0.0
    noradrenaline_shift: float = 0.0
    acetylcholine_shift: float = 0.0
    serotonin_shift: float = 0.0
    gaba_shift: float = 0.0
    glutamate_shift: float = 0.0
    cortisol_shift: float = 0.0
    adrenaline_shift: float = 0.0

    def apply(self, state: NeuromodulationState) -> NeuromodulationState:
        def c(x: float) -> float:
            return min(1.0, max(0.0, x))

        return NeuromodulationState(
            dopamine=c(state.dopamine + self.dopamine_shift),
            noradrenaline=c(state.noradrenaline + self.noradrenaline_shift),
            acetylcholine=c(state.acetylcholine + self.acetylcholine_shift),
            serotonin=c(state.serotonin + self.serotonin_shift),
            gaba=c(state.gaba + self.gaba_shift),
            glutamate=c(state.glutamate + self.glutamate_shift),
            cortisol=c(state.cortisol + self.cortisol_shift),
            adrenaline=c(state.adrenaline + self.adrenaline_shift),
        )


def comparison_scenarios() -> dict[str, PharmacologyIntervention]:
    return {
        "baseline": PharmacologyIntervention(),
        "high_ach": PharmacologyIntervention(acetylcholine_shift=0.35),
        "high_na": PharmacologyIntervention(noradrenaline_shift=0.35, adrenaline_shift=0.10),
        "low_gaba": PharmacologyIntervention(gaba_shift=-0.30, glutamate_shift=0.10),
    }
