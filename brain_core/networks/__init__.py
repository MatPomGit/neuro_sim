
"""
Prymitywy sprzężenia sieciowego i transmisji sygnału.
"""

from .delays import DelayBuffer, delayed_coupling
from .structural_network import StructuralNetwork

__all__ = ["StructuralNetwork", "DelayBuffer", "delayed_coupling"]
