from abc import ABC, abstractmethod
from datetime import date
from typing import Tuple, List
import pandas as pd

from app.db.duckdb_engine import DuckDBEngine
from app.core.exceptions import DataNotFoundError


class BaseDataService(ABC):
    def __init__(self, db_engine: DuckDBEngine = None):
        self.db_engine = db_engine or DuckDBEngine()
        self._registered_tables: dict[str, str] = {}

    @abstractmethod
    def get_data_path(self, field_name: str) -> str:
        pass

    def _register_table(self, field_name: str):
        if field_name not in self._registered_tables:
            data_path = self.get_data_path(field_name)
            table_name = f"data_{field_name}"
            try:
                self.db_engine.register_parquet_file(table_name, data_path)
                self._registered_tables[field_name] = table_name
            except Exception as e:
                raise DataNotFoundError(
                    f"Failed to register parquet file for {field_name}: {e}"
                )

    def get_data_range(self, field_name: str) -> Tuple[date, date]:
        try:
            self._register_table(field_name)
            table_name = self._registered_tables[field_name]
            min_date, max_date = self.db_engine.get_data_range(table_name)

            # Handle None dates from empty tables
            if min_date is None or max_date is None:
                raise DataNotFoundError(f"No data available for {field_name}")

            return date.fromisoformat(min_date), date.fromisoformat(max_date)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataNotFoundError(f"Error getting data range for {field_name}: {e}")

    def get_data_for_dates(
        self, field_name: str, target_dates: List[str]
    ) -> pd.DataFrame:
        try:
            self._register_table(field_name)
            table_name = self._registered_tables[field_name]

            df = self.db_engine.filter_data_by_dates(table_name, target_dates)

            if df.empty:
                return df

            return df

        except Exception as e:
            raise DataNotFoundError(f"Error getting data for dates: {e}")
