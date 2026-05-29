from __future__ import annotations

from dataclasses import dataclass

from brain_core.synapses.state import NeuromodulationState


@dataclass(frozen=True, slots=True)
class PharmacologyIntervention:
    """
    Klasa reprezentująca interwencję farmakologiczną (przesunięcia neuromodulatorów).

    Attributes:
        dopamine_shift (float): Przesunięcie dopaminy.
        noradrenaline_shift (float): Przesunięcie noradrenaliny.
        acetylcholine_shift (float): Przesunięcie acetylocholiny.
        serotonin_shift (float): Przesunięcie serotoniny.
        gaba_shift (float): Przesunięcie GABA.
        glutamate_shift (float): Przesunięcie glutaminianu.
        cortisol_shift (float): Przesunięcie kortyzolu.
        adrenaline_shift (float): Przesunięcie adrenaliny.
    """
    dopamine_shift: float = 0.0
    noradrenaline_shift: float = 0.0
    acetylcholine_shift: float = 0.0
    serotonin_shift: float = 0.0
    gaba_shift: float = 0.0
    glutamate_shift: float = 0.0
    cortisol_shift: float = 0.0
    adrenaline_shift: float = 0.0

    def apply(self, state: NeuromodulationState) -> NeuromodulationState:
        """
        Zastosuj interwencję do stanu neuromodulacji.

        Args:
            state (NeuromodulationState): Stan wejściowy.

        Returns:
            NeuromodulationState: Stan po interwencji.
        """
        def c(x: float) -> float:
            """Ogranicza poziom neuromodulatora do zakresu [0, 1]."""
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
    """
    Zwraca przykładowe scenariusze interwencji farmakologicznych.

    Returns:
        dict[str, PharmacologyIntervention]: Słownik nazw do interwencji.
    """
    return {
        "baseline": PharmacologyIntervention(),
        "high_ach": PharmacologyIntervention(acetylcholine_shift=0.35),
        "high_na": PharmacologyIntervention(noradrenaline_shift=0.35, adrenaline_shift=0.10),
        "low_gaba": PharmacologyIntervention(gaba_shift=-0.30, glutamate_shift=0.10),
    }
