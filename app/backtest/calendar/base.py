from abc import ABC, abstractmethod
from datetime import date


class BaseCalendar(ABC):
    @abstractmethod
    def generate_dates(self, start_date: date, end_date: date) -> list[date]:
        """
        Generate rebalancing dates between start and end dates.

        Args:
            start_date: Start date for date generation
            end_date: End date for date generation

        Returns:
            List of rebalancing dates
        """
        pass
