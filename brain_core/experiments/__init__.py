"""Moduł eksperymentów: farmakologia, patologie, protokoły eksperymentalne."""

from .lesions import (
    PathologyController,
    PathologyMutation,
    build_pathology_controller,
    pathology_scenarios,
)
from .pharmacology import PharmacologyIntervention, comparison_scenarios
from .protocols import (
    ExperimentProtocol,
    ProtocolPhase,
    ProtocolStep,
    default_train_test_protocol,
)

__all__ = [
    "ExperimentProtocol",
    "PharmacologyIntervention",
    "PathologyController",
    "PathologyMutation",
    "ProtocolPhase",
    "ProtocolStep",
    "build_pathology_controller",
    "comparison_scenarios",
    "default_train_test_protocol",
    "pathology_scenarios",
]
