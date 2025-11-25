from datetime import date

from dateutil.relativedelta import relativedelta  # type: ignore[import-untyped]

from app.backtest.calendar.base import BaseCalendar


class QuarterlyCalendar(BaseCalendar):
    def __init__(self, rules):
        """
        Initialize with calendar rules.

        Args:
            rules: CalendarRules object with initial_date
        """
        self.initial_date = rules.initial_date

    def generate_dates(self, start_date: date, end_date: date) -> list[date]:
        """
        Generate quarterly dates between start_date and end_date.

        Args:
            start_date: Start date for date generation
            end_date: End date for date generation

        Returns:
            List of quarterly dates
        """
        dates = []

        # Start from the first day of the quarter containing start_date
        start_quarter_month = ((start_date.month - 1) // 3) * 3 + 1
        current_date = date(start_date.year, start_quarter_month, 1)

        # Generate quarterly dates until we exceed end_date
        while current_date <= end_date:
            # Calculate quarter end date (last day of the quarter)
            quarter_end_month = ((current_date.month - 1) // 3 + 1) * 3
            if quarter_end_month > 12:
                quarter_end_month = 12
                quarter_year = current_date.year
            else:
                quarter_year = current_date.year

            # Get last day of the quarter
            if quarter_end_month == 12:
                quarter_end = date(quarter_year, 12, 31)
            else:
                next_quarter_start = date(quarter_year, quarter_end_month + 1, 1)
                quarter_end = next_quarter_start - relativedelta(days=1)

            # Only add if within the requested range and after start_date
            if start_date <= quarter_end <= end_date:
                dates.append(quarter_end)

            # Move to next quarter
            current_date = current_date + relativedelta(months=3)

        return sorted(dates)
