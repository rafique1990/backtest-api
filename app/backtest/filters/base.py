from abc import ABC, abstractmethod

import pandas as pd


class BaseFilter(ABC):
    @abstractmethod
    def select(self, data: pd.DataFrame, n: int = None) -> list[str]:
        """
        Select assets based on filtering criteria.

        Args:
            data: DataFrame with securities as columns
            n: Optional number of assets to select

        Returns:
            List of selected security identifiers
        """
        pass
