from abc import ABC, abstractmethod
from typing import Dict, List


class BaseWeighting(ABC):
    @abstractmethod
    def calculate(self, assets: List[str]) -> Dict[str, float]:
        """
        Calculate weights for assets.

        Args:
            assets: List of asset identifiers

        Returns:
            Dictionary mapping asset to weight
        """
        pass
