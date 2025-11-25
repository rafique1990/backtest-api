import os
import tempfile
from unittest.mock import patch

import duckdb
import pandas as pd
import pytest

from app.core.exceptions import DatabaseError
from app.db.duckdb_engine import DuckDBEngine


class TestDuckDBEngine:
    """Test cases for DuckDBEngine class"""

    @pytest.fixture
    def duckdb_engine(self):
        """Create a DuckDBEngine instance with in-memory database"""
        return DuckDBEngine(db_path=":memory:")

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing"""
        return pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "security": ["AAPL", "MSFT", "GOOG"],
                "value": [100.0, 150.0, 200.0],
            }
        )

    @pytest.fixture
    def temp_parquet_file(self, sample_dataframe):
        """Create a temporary parquet file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            sample_dataframe.to_parquet(f.name, index=False)
            yield f.name
            os.unlink(f.name)

    def test_initialization(self, duckdb_engine):
        """Test DuckDBEngine initialization"""
        assert duckdb_engine.db_path == ":memory:"
        assert duckdb_engine._conn is None
        assert duckdb_engine._is_initialized is False

    def test_initialize_connection_success(self, duckdb_engine):
        """Test successful connection initialization"""
        duckdb_engine._initialize_connection()

        assert duckdb_engine._conn is not None
        assert duckdb_engine._is_initialized is True
        assert isinstance(duckdb_engine._conn, duckdb.DuckDBPyConnection)

    def test_initialize_connection_failure(self):
        """Test connection initialization failure"""
        with patch("duckdb.connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            engine = DuckDBEngine(db_path="invalid_path")
            with pytest.raises(DatabaseError, match="DuckDB initialization failed"):
                engine._initialize_connection()

    def test_register_parquet_file_success(self, duckdb_engine, temp_parquet_file):
        """Test successful parquet file registration"""
        table_name = "test_table"

        duckdb_engine.register_parquet_file(table_name, temp_parquet_file)

        # Verify table was created by querying it
        result = duckdb_engine.execute_query(
            f"SELECT COUNT(*) as count FROM {table_name}"
        )
        assert result.iloc[0]["count"] == 3

    def test_register_parquet_file_invalid_path(self, duckdb_engine):
        """Test parquet registration with invalid file path"""
        with pytest.raises(DatabaseError, match="Parquet registration failed"):
            duckdb_engine.register_parquet_file(
                "test_table", "nonexistent_file.parquet"
            )

    def test_execute_query_success(self, duckdb_engine):
        """Test successful query execution"""
        # Create a test table
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        duckdb_engine._conn.execute("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob')")

        result = duckdb_engine.execute_query("SELECT * FROM test ORDER BY id")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]["id"] == 1
        assert result.iloc[0]["name"] == "Alice"

    def test_execute_query_syntax_error(self, duckdb_engine):
        """Test query execution with syntax error"""
        with pytest.raises(DatabaseError, match="DuckDB query error"):
            duckdb_engine.execute_query("SELECT * FROM nonexistent_table")

    def test_execute_query_empty_result(self, duckdb_engine):
        """Test query execution with empty result"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute("CREATE TABLE empty_table (id INTEGER)")

        result = duckdb_engine.execute_query("SELECT * FROM empty_table")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["id"]

    def test_get_data_range_success(self, duckdb_engine, temp_parquet_file):
        """Test successful data range retrieval"""
        table_name = "test_data"
        duckdb_engine.register_parquet_file(table_name, temp_parquet_file)

        min_date, max_date = duckdb_engine.get_data_range(table_name)

        assert min_date == "2024-01-01"
        assert max_date == "2024-01-03"

    def test_get_data_range_custom_date_column(self, duckdb_engine):
        """Test data range with custom date column name"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute(
            """
            CREATE TABLE custom_dates (
                custom_date_col DATE,
                value FLOAT
            )
        """
        )
        duckdb_engine._conn.execute(
            """
            INSERT INTO custom_dates VALUES
            ('2024-01-01', 100.0),
            ('2024-01-05', 200.0)
        """
        )

        min_date, max_date = duckdb_engine.get_data_range(
            "custom_dates", "custom_date_col"
        )

        assert min_date == "2024-01-01"
        assert max_date == "2024-01-05"

    def test_get_data_range_empty_table(self, duckdb_engine):
        """Test data range with empty table"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute("CREATE TABLE empty_table (date DATE)")

        min_date, max_date = duckdb_engine.get_data_range("empty_table")

        # DuckDB returns None for min/max on empty tables
        assert pd.isna(min_date)
        assert pd.isna(max_date)

    def test_filter_data_by_dates_success(self, duckdb_engine, temp_parquet_file):
        """Test successful date filtering"""
        table_name = "test_data"
        duckdb_engine.register_parquet_file(table_name, temp_parquet_file)

        target_dates = ["2024-01-01", "2024-01-03"]
        result = duckdb_engine.filter_data_by_dates(table_name, target_dates)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert set(result["date"].tolist()) == set(target_dates)

    def test_filter_data_by_dates_empty_result(self, duckdb_engine, temp_parquet_file):
        """Test date filtering with no matching dates"""
        table_name = "test_data"
        duckdb_engine.register_parquet_file(table_name, temp_parquet_file)

        target_dates = ["2024-12-31"]  # Date not in data
        result = duckdb_engine.filter_data_by_dates(table_name, target_dates)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_filter_data_by_dates_empty_list(self, duckdb_engine, temp_parquet_file):
        """Test date filtering with empty date list"""
        table_name = "test_data"
        duckdb_engine.register_parquet_file(table_name, temp_parquet_file)

        result = duckdb_engine.filter_data_by_dates(table_name, [])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_filter_data_by_dates_sql_injection_safe(self, duckdb_engine):
        """Test that date filtering is safe from SQL injection"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute("CREATE TABLE test (date DATE, value FLOAT)")
        duckdb_engine._conn.execute("INSERT INTO test VALUES ('2024-01-01', 100.0)")

        # Attempt SQL injection through table name (should be blocked by identifier validation)
        with pytest.raises(DatabaseError, match="Invalid table name"):
            duckdb_engine.filter_data_by_dates(
                "test; DROP TABLE test; --", ["2024-01-01"]
            )

    def test_get_top_n_securities_success(self, duckdb_engine, temp_parquet_file):
        """Test successful top N securities retrieval"""
        table_name = "test_data"
        duckdb_engine.register_parquet_file(table_name, temp_parquet_file)

        result = duckdb_engine.get_top_n_securities(
            table_name=table_name, date_value="2024-01-01", value_column="value", n=2
        )

        assert isinstance(result, list)
        assert len(result) == 1  # Only one security on 2024-01-01 in our sample
        assert result[0] == "AAPL"

    def test_get_top_n_securities_multiple_rows(self, duckdb_engine):
        """Test top N securities with multiple rows per date"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute(
            """
            CREATE TABLE multi_securities (
                date DATE,
                security VARCHAR,
                value FLOAT
            )
        """
        )
        duckdb_engine._conn.execute(
            """
            INSERT INTO multi_securities VALUES
            ('2024-01-01', 'AAPL', 100.0),
            ('2024-01-01', 'MSFT', 150.0),
            ('2024-01-01', 'GOOG', 200.0),
            ('2024-01-02', 'TSLA', 50.0)
        """
        )

        result = duckdb_engine.get_top_n_securities(
            table_name="multi_securities",
            date_value="2024-01-01",
            value_column="value",
            n=2,
        )

        assert result == ["GOOG", "MSFT"]  # Sorted by value descending

    def test_get_top_n_securities_n_larger_than_available(self, duckdb_engine):
        """Test top N securities where N is larger than available securities"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute(
            """
            CREATE TABLE few_securities (
                date DATE,
                security VARCHAR,
                value FLOAT
            )
        """
        )
        duckdb_engine._conn.execute(
            """
            INSERT INTO few_securities VALUES
            ('2024-01-01', 'AAPL', 100.0),
            ('2024-01-01', 'MSFT', 150.0)
        """
        )

        result = duckdb_engine.get_top_n_securities(
            table_name="few_securities",
            date_value="2024-01-01",
            value_column="value",
            n=5,  # Request more than available
        )

        assert len(result) == 2  # Should return all available
        assert result == ["MSFT", "AAPL"]

    def test_get_top_n_securities_no_data_for_date(self, duckdb_engine):
        """Test top N securities with no data for specified date"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute(
            """
            CREATE TABLE date_test (
                date DATE,
                security VARCHAR,
                value FLOAT
            )
        """
        )
        duckdb_engine._conn.execute(
            """
            INSERT INTO date_test VALUES
            ('2024-01-01', 'AAPL', 100.0)
        """
        )

        result = duckdb_engine.get_top_n_securities(
            table_name="date_test",
            date_value="2024-12-31",  # Date with no data
            value_column="value",
            n=5,
        )

        assert result == []  # Should return empty list

    def test_get_top_n_securities_n_zero(self, duckdb_engine):
        """Test top N securities with N=0"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute(
            """
            CREATE TABLE test_n_zero (
                date DATE,
                security VARCHAR,
                value FLOAT
            )
        """
        )
        duckdb_engine._conn.execute(
            """
            INSERT INTO test_n_zero VALUES
            ('2024-01-01', 'AAPL', 100.0)
        """
        )

        result = duckdb_engine.get_top_n_securities(
            table_name="test_n_zero", date_value="2024-01-01", value_column="value", n=0
        )

        assert result == []  # Should return empty list

    def test_close_connection(self, duckdb_engine):
        """Test connection closing"""
        duckdb_engine._initialize_connection()
        assert duckdb_engine._conn is not None

        duckdb_engine.close()

        assert duckdb_engine._conn is None
        assert duckdb_engine._is_initialized is False

    def test_context_manager(self):
        """Test context manager functionality"""
        with DuckDBEngine(":memory:") as engine:
            assert engine._conn is not None
            assert engine._is_initialized is True

            # Should be able to execute queries
            result = engine.execute_query("SELECT 1 as test")
            assert result.iloc[0]["test"] == 1

        # Connection should be closed after context manager exits
        assert engine._conn is None
        assert engine._is_initialized is False

    def test_connection_reuse(self, duckdb_engine):
        """Test that connection is reused after initialization"""
        duckdb_engine._initialize_connection()
        original_conn = duckdb_engine._conn

        # Call initialize again - should reuse same connection
        duckdb_engine._initialize_connection()

        assert duckdb_engine._conn is original_conn  # Same connection object

    def test_thread_pool_configuration(self, duckdb_engine):
        """Test that thread pool is properly configured"""
        duckdb_engine._initialize_connection()

        # Verify thread configuration was set
        result = duckdb_engine.execute_query(
            "SELECT current_setting('threads') as threads"
        )
        assert int(result.iloc[0]["threads"]) == 4

    def test_large_query_execution(self, duckdb_engine):
        """Test execution of query with large result set"""
        duckdb_engine._initialize_connection()

        # Create table with many rows
        duckdb_engine._conn.execute(
            "CREATE TABLE large_table (id INTEGER, value FLOAT)"
        )

        # Insert 1000 rows
        for i in range(1000):
            duckdb_engine._conn.execute(
                f"INSERT INTO large_table VALUES ({i}, {i * 1.5})"
            )

        result = duckdb_engine.execute_query(
            "SELECT COUNT(*) as count FROM large_table"
        )

        assert result.iloc[0]["count"] == 1000

    def test_special_characters_in_data(self, duckdb_engine):
        """Test handling of special characters in data"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute(
            "CREATE TABLE special_chars (name VARCHAR, value FLOAT)"
        )

        # Insert data with special characters using parameterized queries
        test_names = [
            "Test'Quote",
            'Test"DoubleQuote',
            "Test;Semicolon",
            "Test--Comment",
        ]
        for name in test_names:
            # Use parameterized query
            duckdb_engine._conn.execute(
                "INSERT INTO special_chars VALUES (?, ?)", [name, 100.0]
            )

        result = duckdb_engine.execute_query(
            "SELECT COUNT(*) as count FROM special_chars"
        )
        assert result.iloc[0]["count"] == len(test_names)

    def test_null_handling(self, duckdb_engine):
        """Test proper handling of NULL values"""
        duckdb_engine._initialize_connection()
        duckdb_engine._conn.execute("CREATE TABLE null_test (id INTEGER, value FLOAT)")
        duckdb_engine._conn.execute(
            "INSERT INTO null_test VALUES (1, NULL), (2, 100.0)"
        )

        result = duckdb_engine.execute_query("SELECT * FROM null_test ORDER BY id")

        assert pd.isna(result.iloc[0]["value"])
        assert result.iloc[1]["value"] == 100.0
