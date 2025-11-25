import logging
import re

import duckdb
import pandas as pd

from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DuckDBEngine:
    """High-performance analytical database engine using DuckDB with vectorized operations."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = None
        self._is_initialized = False

    def _initialize_connection(self):
        if self._conn is None:
            try:
                self._conn = duckdb.connect(database=self.db_path, read_only=False)
                self._conn.execute("INSTALL httpfs;")
                self._conn.execute("LOAD httpfs;")
                self._conn.execute("INSTALL parquet;")
                self._conn.execute("LOAD parquet;")
                self._conn.execute("PRAGMA threads=4;")

                logger.info(f"DuckDB engine initialized: {self.db_path}")
                self._is_initialized = True

            except Exception as e:
                logger.error(f"Failed to initialize DuckDB: {e}")
                raise DatabaseError(f"DuckDB initialization failed: {str(e)}")

    def _validate_identifier(self, identifier: str) -> bool:
        """Validate identifier is safe (alphanumeric and underscores only)."""
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier))

    def _safe_identifier(self, identifier: str) -> str:
        """Validate and return SQL-safe identifier."""
        if not self._validate_identifier(identifier):
            raise DatabaseError(f"Invalid identifier: {identifier}")
        return identifier

    def _detect_date_column(self, table_name: str) -> str:
        """Auto-detect date column from table schema."""
        try:
            schema_query = f"DESCRIBE {self._safe_identifier(table_name)}"
            schema = self.execute_query(schema_query)

            date_columns = ["date", "__index_level_0__", "timestamp", "time"]
            for col_name in schema["column_name"]:
                if col_name.lower() in date_columns:
                    return col_name

            return schema.iloc[0]["column_name"]

        except Exception as e:
            logger.warning(f"Could not detect date column for {table_name}: {e}")
            return "date"

    def register_parquet_file(self, table_name: str, file_path: str):
        """Register parquet file as queryable view."""
        self._initialize_connection()
        if not self._validate_identifier(table_name):
            raise DatabaseError(f"Invalid table name: {table_name}")

        try:
            # Uses string formatting for file path (DuckDB doesn't support parameters for DDL)
            # Also sanitize the file path to prevent SQL injection
            if not file_path or any(
                char in file_path for char in [";", "--", "/*", "*/"]
            ):
                raise DatabaseError(f"Invalid file path: {file_path}")

            query = f"""
                CREATE OR REPLACE VIEW {self._safe_identifier(table_name)} AS
                SELECT * FROM read_parquet('{file_path}')
            """
            if self._conn is None:
                raise DatabaseError("Database connection not initialized")
            self._conn.execute(query)  # type: ignore[union-attr]
            logger.debug(f"Registered parquet file as table: {table_name}")

        except Exception as e:
            logger.error(f"Failed to register parquet file {file_path}: {e}")
            raise DatabaseError(f"Parquet registration failed: {str(e)}")

    def execute_query(self, sql_query: str, params: list = None) -> pd.DataFrame:
        """Execute a SQL query with optional parameters"""
        self._initialize_connection()
        if self._conn is None:
            raise DatabaseError("Database connection not initialized")

        try:
            if params:
                df = self._conn.execute(sql_query, params).fetchdf()
            else:
                df = self._conn.execute(sql_query).fetchdf()

            logger.debug(f"Query executed successfully. Rows: {len(df)}")
            return df

        except duckdb.Error as e:
            error_message = f"DuckDB query error: {e}"
            logger.error(error_message)
            raise DatabaseError(error_message)
        except Exception as e:
            error_message = f"Query execution failed: {e}"
            logger.error(error_message)
            raise DatabaseError(error_message)

    def get_data_range(self, table_name: str, date_column: str | None = None) -> tuple:
        """Get min and max dates from a table"""
        # Validate identifiers
        if not self._validate_identifier(table_name):
            raise DatabaseError(f"Invalid table name: {table_name}")

        # Auto-detect date column if not provided
        if date_column is None:
            date_column = self._detect_date_column(table_name)

        if not self._validate_identifier(date_column):
            raise DatabaseError(f"Invalid date column: {date_column}")

        query = f"""
        SELECT MIN({self._safe_identifier(date_column)}) as min_date,
               MAX({self._safe_identifier(date_column)}) as max_date
        FROM {self._safe_identifier(table_name)}
        """
        result = self.execute_query(query)

        # Convert Timestamp to string for consistent return type
        min_date = result.iloc[0]["min_date"]
        max_date = result.iloc[0]["max_date"]

        # Handles NaT (Not a Time) values from empty tables
        if pd.isna(min_date) or pd.isna(max_date):
            return None, None

        # Convert to string if it's a Timestamp object
        if hasattr(min_date, "strftime"):
            min_date = min_date.strftime("%Y-%m-%d")
        if hasattr(max_date, "strftime"):
            max_date = max_date.strftime("%Y-%m-%d")

        return min_date, max_date

    def filter_data_by_dates(
        self,
        table_name: str,
        target_dates: list[str],
        date_column: str | None = None,
    ) -> pd.DataFrame:
        """Filter data by specific dates"""
        # Validate identifiers
        if not self._validate_identifier(table_name):
            raise DatabaseError(f"Invalid table name: {table_name}")

        # Auto-detect date column if not provided
        if date_column is None:
            date_column = self._detect_date_column(table_name)

        if not self._validate_identifier(date_column):
            raise DatabaseError(f"Invalid date column: {date_column}")

        # Handle empty date list
        if not target_dates:
            logger.debug("Empty date list provided, returning empty DataFrame")
            return pd.DataFrame()

        # Use parameterized query with placeholders
        placeholders = ", ".join(["?" for _ in target_dates])
        query = f"""
        SELECT *
        FROM {self._safe_identifier(table_name)}
        WHERE {self._safe_identifier(date_column)} IN ({placeholders})
        ORDER BY {self._safe_identifier(date_column)}
        """

        return self.execute_query(query, target_dates)

    def get_top_n_securities(
        self,
        table_name: str,
        date_value: str,
        value_column: str,
        n: int,
        date_column: str | None = None,
    ) -> list[str]:
        """Get top N securities by value for a specific date"""
        # Validate identifiers
        if not self._validate_identifier(table_name):
            raise DatabaseError(f"Invalid table name: {table_name}")
        if not self._validate_identifier(value_column):
            raise DatabaseError(f"Invalid value column: {value_column}")

        # Auto-detect date column if not provided
        if date_column is None:
            date_column = self._detect_date_column(table_name)

        if not self._validate_identifier(date_column):
            raise DatabaseError(f"Invalid date column: {date_column}")

        # Validate n parameter
        if n < 0:
            raise DatabaseError("Parameter n must be non-negative")

        query = f"""
        SELECT security, {self._safe_identifier(value_column)}
        FROM {self._safe_identifier(table_name)}
        WHERE {self._safe_identifier(date_column)} = ?
        ORDER BY {self._safe_identifier(value_column)} DESC
        LIMIT ?
        """

        result = self.execute_query(query, [date_value, n])
        return result["security"].tolist()

    def close(self):
        """Close the database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._is_initialized = False
            logger.debug("DuckDB connection closed.")

    def __enter__(self):
        self._initialize_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
