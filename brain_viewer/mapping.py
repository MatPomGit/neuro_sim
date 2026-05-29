import numpy as np
from numpy.typing import NDArray

class BrainRegionMapper:
    """Mapuje aktywności modułów poznawczych na aktywności regionów mózgu."""

    def __init__(
        self, module_names: list[str], region_names: list[str], mapping_matrix: NDArray[np.float64]
    ) -> None:
        """Inicjalizuje mapper z nazwami modułów, regionów i macierzą projekcji."""
        self.module_names: list[str] = module_names
        self.region_names: list[str] = region_names
        self.M: NDArray[np.float64] = mapping_matrix

    def modules_to_regions(self, module_activity: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        module_activity: array [time, module]
        return: regional_activity [time, region]
        """
        R = module_activity @ self.M.T
        R = np.clip(R, 0.0, 1.0)
        return R
