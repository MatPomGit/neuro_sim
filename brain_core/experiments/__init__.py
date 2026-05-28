"""Moduł eksperymentów: farmakologia, patologie, protokoły eksperymentalne."""

from .lesions import PathologyController, PathologyMutation, pathology_scenarios, build_pathology_controller
from .pharmacology import PharmacologyIntervention, comparison_scenarios

__all__ = ["PharmacologyIntervention", "comparison_scenarios", "PathologyController", "PathologyMutation", "pathology_scenarios", "build_pathology_controller"]

from .protocols import ExperimentProtocol, ProtocolPhase, ProtocolStep, default_train_test_protocol
