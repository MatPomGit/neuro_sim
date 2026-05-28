from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from brain_core.simulation.state import SimulationState


PathologyKind = Literal["lesion", "disconnection", "noise_increase", "ei_imbalance", "delay_increase", "atrophy"]
MutationStage = Literal["pre", "runtime"]


@dataclass(frozen=True, slots=True)
class PathologyMutation:
    """
    Mutacja patologiczna aplikowana do stanu symulacji.

    Attributes:
        kind (PathologyKind): Typ mutacji.
        target (str): Cel mutacji (region lub połączenie).
        scope (Literal["region", "edge"]): Zakres mutacji.
        magnitude (float): Siła mutacji.
        stage (MutationStage): Etap aplikacji mutacji.
        source (str | None): Źródło (dla edge-level).
    """
    kind: PathologyKind
    target: str
    scope: Literal["region", "edge"]
    magnitude: float = 1.0
    stage: MutationStage = "pre"
    source: str | None = None

    def apply(self, state: SimulationState) -> None:
        """
        Aplikuje mutację do stanu symulacji.

        Args:
            state (SimulationState): Stan symulacji.
        """
        if self.scope == "region":
            self._apply_region(state)
            return
        self._apply_edge(state)

    def _apply_region(self, state: SimulationState) -> None:
        """
        Aplikuje mutację do regionu.

        Args:
            state (SimulationState): Stan symulacji.

        Raises:
            KeyError: Jeśli region nie istnieje.
            ValueError: Jeśli typ mutacji nie jest wspierany dla regionu.
        """
        if self.target not in state.regions:
            raise KeyError(f"Nie znaleziono regionu: {self.target}")

        signal = np.asarray(state.regions[self.target], dtype=float).copy()
        if self.kind == "lesion":
            signal *= max(0.0, 1.0 - self.magnitude)
        elif self.kind == "noise_increase":
            signal = signal + self.magnitude
        elif self.kind == "ei_imbalance":
            state.metrics[f"ei_shift:{self.target}"] = float(self.magnitude)
            signal = np.maximum(0.0, signal + (0.5 * self.magnitude))
        elif self.kind == "atrophy":
            signal *= max(0.0, 1.0 - 0.5 * self.magnitude)
        else:
            raise ValueError(f"Typ {self.kind} wymaga scope='edge' albo nie jest wspierany dla regionu")

        state.regions[self.target] = signal
        state.metrics[f"pathology:{self.kind}:{self.target}"] = float(np.mean(signal))

    def _apply_edge(self, state: SimulationState) -> None:
        """
        Aplikuje mutację do połączenia (edge).

        Args:
            state (SimulationState): Stan symulacji.

        Raises:
            ValueError: Jeśli brakuje źródła lub typ nie jest wspierany.
            KeyError: Jeśli połączenie nie istnieje.
        """
        if not self.source:
            raise ValueError("Mutacja edge-level wymaga pola 'source'")
        key = f"{self.source}->{self.target}"
        if key not in state.connections:
            raise KeyError(f"Nie znaleziono połączenia: {key}")

        edge = np.asarray(state.connections[key], dtype=float).copy()
        if self.kind == "disconnection":
            edge *= max(0.0, 1.0 - self.magnitude)
        elif self.kind == "delay_increase":
            state.metrics[f"delay_shift:{key}"] = float(self.magnitude)
            edge *= 1.0 / (1.0 + self.magnitude)
        else:
            raise ValueError(f"Typ {self.kind} nie jest wspierany dla edge-level")

        state.connections[key] = edge
        state.metrics[f"pathology:{self.kind}:{key}"] = float(np.mean(edge))


class PathologyController:
    """
    API do mutacji modelu przed i w trakcie symulacji.

    Attributes:
        pre_simulation (list[PathologyMutation]): Mutacje przed symulacją.
        runtime (list[PathologyMutation]): Mutacje w trakcie symulacji.
    """

    def __init__(self, mutations: list[PathologyMutation]):
        """
        Inicjalizuje kontroler mutacji.

        Args:
            mutations (list[PathologyMutation]): Lista mutacji.
        """
        self.pre_simulation = [m for m in mutations if m.stage == "pre"]
        self.runtime = [m for m in mutations if m.stage == "runtime"]

    def apply_pre_simulation(self, state: SimulationState) -> None:
        """
        Aplikuje mutacje przed symulacją.

        Args:
            state (SimulationState): Stan symulacji.
        """
        for mutation in self.pre_simulation:
            mutation.apply(state)

    def apply_runtime(self, state: SimulationState) -> None:
        """
        Aplikuje mutacje w trakcie symulacji.

        Args:
            state (SimulationState): Stan symulacji.
        """
        for mutation in self.runtime:
            mutation.apply(state)


REFERENCE_PATHOLOGY_SCENARIOS: dict[str, list[PathologyMutation]] = {
    "hippocampal_lesion": [
        PathologyMutation(kind="lesion", scope="region", target="Hippocampus", magnitude=0.8, stage="pre"),
    ],
    "dlpfc_weakening": [
        PathologyMutation(kind="atrophy", scope="region", target="DLPFC", magnitude=0.6, stage="runtime"),
        PathologyMutation(kind="disconnection", scope="edge", source="DLPFC", target="ACC", magnitude=0.4, stage="runtime"),
    ],
    "reduced_gaba": [
        PathologyMutation(kind="ei_imbalance", scope="region", target="PFC", magnitude=0.35, stage="pre"),
        PathologyMutation(kind="noise_increase", scope="region", target="PFC", magnitude=0.12, stage="runtime"),
    ],
}


def pathology_scenarios() -> dict[str, list[PathologyMutation]]:
    """
    Zwraca słownik dostępnych scenariuszy patologii.

    Returns:
        dict[str, list[PathologyMutation]]: Słownik scenariuszy.
    """
    return {name: list(mutations) for name, mutations in REFERENCE_PATHOLOGY_SCENARIOS.items()}


def build_pathology_controller(
    entries: list[dict[str, Any]] | None,
    scenario_name: str | None = None
) -> PathologyController:
    """
    Buduje kontroler patologii na podstawie wpisów lub nazwy scenariusza.

    Args:
        entries (list[dict[str, Any]] | None): Lista słowników mutacji.
        scenario_name (str | None): Nazwa scenariusza.

    Returns:
        PathologyController: Kontroler mutacji.

    Raises:
        ValueError: Jeśli nieznany scenariusz.
    """
    mutations: list[PathologyMutation] = []
    if scenario_name:
        scenarios = pathology_scenarios()
        if scenario_name in scenarios:
            mutations.extend(scenarios[scenario_name])
        else:
            raise ValueError(f"Nieznany scenariusz patologii: {scenario_name}")

    if entries:
        allowed_keys = {"kind", "target", "scope", "magnitude", "stage", "source"}
        for entry in entries:
            filtered = {k: v for k, v in entry.items() if k in allowed_keys}
            mutations.append(PathologyMutation(**filtered))

    return PathologyController(mutations)
