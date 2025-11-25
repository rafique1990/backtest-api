from abc import ABC, abstractmethod


class BaseWeighting(ABC):
    @abstractmethod
    def calculate(self, assets: list[str]) -> dict[str, float]:
        """
        Calculate weights for assets.

        Args:
            assets: List of asset identifiers

        Returns:
            Dictionary mapping asset to weight
        """
        pass
