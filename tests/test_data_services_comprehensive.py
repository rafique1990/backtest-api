import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.core.exceptions import DataNotFoundError, FilePermissionError
from app.db.duckdb_engine import DuckDBEngine
from app.services.base_data_service import BaseDataService
from app.services.local_data_service import LocalDataService
from app.services.s3_data_service import S3DataService


class TestBaseDataServiceComprehensive:
    """Comprehensive tests for BaseDataService"""

    @pytest.fixture
    def mock_db_engine(self):
        mock_engine = Mock(spec=DuckDBEngine)
        mock_engine.register_parquet_file = Mock()
        mock_engine.get_data_range = Mock(
            return_value=(pd.Timestamp("2020-01-01"), pd.Timestamp("2025-01-22"))
        )
        mock_engine.filter_data_by_dates = Mock(
            return_value=pd.DataFrame(
                {"date": ["2024-01-01"], "security": ["AAPL"], "value": [100.0]}
            )
        )
        return mock_engine

    @pytest.fixture
    def concrete_service(self, mock_db_engine):
        class ConcreteService(BaseDataService):
            def get_data_path(self, field_name: str) -> str:
                return f"/fake/path/{field_name}.parquet"

        return ConcreteService(db_engine=mock_db_engine)


class TestLocalDataServiceComprehensive:
    """Comprehensive tests for LocalDataService"""

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def local_service(self, temp_data_dir):
        with patch("app.services.local_data_service.settings") as mock_settings:
            mock_settings.LOCAL_DATA_DIR = str(temp_data_dir)
            service = LocalDataService()
            return service

    @pytest.fixture
    def sample_parquet_file(self, temp_data_dir):
        file_path = temp_data_dir / "market_capitalization.parquet"
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "security": ["AAPL", "MSFT"],
                "value": [100.0, 150.0],
            }
        )
        df.to_parquet(file_path, index=False)
        return file_path

    def test_initialization_success(self, temp_data_dir):
        """Test successful initialization"""
        with patch("app.services.local_data_service.settings") as mock_settings:
            mock_settings.LOCAL_DATA_DIR = str(temp_data_dir)
            service = LocalDataService()
            # Compares resolved paths to handle symlinks like /private/var on macOS
            assert service.data_dir.resolve() == Path(temp_data_dir).resolve()

    def test_initialization_permission_error(self):
        """Test initialization with permission error"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")

            with patch("app.services.local_data_service.settings") as mock_settings:
                mock_settings.LOCAL_DATA_DIR = "/root/protected"

                with pytest.raises(
                    DataNotFoundError, match="Cannot create data directory"
                ):
                    LocalDataService()

    def test_get_data_path_success(self, local_service, sample_parquet_file):
        """Test successful data path retrieval"""
        result = local_service.get_data_path("market_capitalization")
        # Uses resolved paths for comparison to handle macOS /private/var symlinks
        assert Path(result).resolve() == sample_parquet_file.resolve()

    def test_get_data_path_file_not_found(self, local_service):
        """Tests data path with non-existent file"""
        with pytest.raises(DataNotFoundError, match="Local data file not found"):
            local_service.get_data_path("nonexistent")

    def test_get_data_path_directory_instead_of_file(
        self, local_service, temp_data_dir
    ):
        """Tests data path when path is a directory"""
        dir_path = temp_data_dir / "directory"
        dir_path.mkdir()

        # Create a parquet file with the directory name to trigger the directory check
        file_path = temp_data_dir / "directory.parquet"
        file_path.mkdir()  # Make it a directory

        with pytest.raises(
            DataNotFoundError, match="Path exists but is a directory, not a file"
        ):
            local_service.get_data_path("directory")

    def test_get_data_path_wrong_extension(self, local_service, temp_data_dir):
        """Test data path with wrong file extension"""
        csv_file = temp_data_dir / "data.csv"
        csv_file.write_text("test data")

        # Should raise error because data.parquet doesn't exist
        with pytest.raises(DataNotFoundError, match="Local data file not found"):
            local_service.get_data_path("data")

    def test_get_data_path_wrong_extension_existing_file(
        self, local_service, temp_data_dir
    ):
        """Test data path with existing file but wrong extension"""
        # Create a file with .parquet extension but wrong content
        wrong_file = temp_data_dir / "wrong_extension.parquet"
        wrong_file.write_text("this is not a parquet file")

        # Should return the path (validation happens in DuckDB during registration)
        result_path = local_service.get_data_path("wrong_extension")
        assert Path(result_path).resolve() == wrong_file.resolve()

    def test_get_data_path_permission_denied(self, local_service, temp_data_dir):
        """Test data path with permission denied"""
        if os.name == "nt":
            pytest.skip("Permission tests not reliable on Windows")

        protected_file = temp_data_dir / "protected.parquet"
        df = pd.DataFrame({"data": [1, 2, 3]})
        df.to_parquet(protected_file)
        protected_file.chmod(0o000)  # No permissions

        try:
            with pytest.raises(FilePermissionError):
                local_service.get_data_path("protected")
        finally:
            protected_file.chmod(0o644)  # Restore permissions

    def test_get_data_path_invalid_field_name(self, local_service):
        """Test data path with invalid field names"""
        # Test empty field name
        with pytest.raises(
            DataNotFoundError, match="Field name must be a non-empty string"
        ):
            local_service.get_data_path("")

        # Test None field name
        with pytest.raises(
            DataNotFoundError, match="Field name must be a non-empty string"
        ):
            local_service.get_data_path(None)

        # Test field name with path traversal
        with pytest.raises(DataNotFoundError, match="Invalid field name"):
            local_service.get_data_path("../sensitive_file")

        # Test field name with special characters
        with pytest.raises(DataNotFoundError, match="Invalid field name"):
            local_service.get_data_path("file;.parquet")

    def test_get_data_path_valid_special_characters(self, local_service, temp_data_dir):
        """Test data path with valid special characters in field name"""
        valid_names = ["market_cap", "adtv-3-month", "price.data.2024"]

        for field_name in valid_names:
            file_path = temp_data_dir / f"{field_name}.parquet"
            df = pd.DataFrame({"data": [1, 2, 3]})
            df.to_parquet(file_path)

            try:
                result = local_service.get_data_path(field_name)
                assert Path(result).resolve() == file_path.resolve()
            finally:
                file_path.unlink()

    def test_environment_specific_paths(self, temp_data_dir):
        """Test path resolution in different environments"""
        test_cases = [
            ("./data", temp_data_dir),
            ("../data", temp_data_dir.parent / "data"),
        ]

        for input_path, _expected_path in test_cases:
            with patch("app.services.local_data_service.settings") as mock_settings:
                mock_settings.LOCAL_DATA_DIR = input_path

                with patch("pathlib.Path.mkdir"):
                    service = LocalDataService()
                    # The path should be resolved to absolute path
                    assert service.data_dir.is_absolute()


class TestS3DataServiceComprehensive:
    """Comprehensive tests for S3DataService"""

    @pytest.fixture
    def s3_service(self):
        with patch("app.services.s3_data_service.settings") as mock_settings:
            mock_settings.S3_BUCKET = "test-bucket"
            mock_settings.AWS_REGION = "us-east-1"
            return S3DataService()

    @pytest.fixture
    def s3_service_no_bucket(self):
        with patch("app.services.s3_data_service.settings") as mock_settings:
            mock_settings.S3_BUCKET = ""
            return S3DataService()

    def test_initialization_with_bucket(self, s3_service):
        """Test initialization with bucket configuration"""
        assert s3_service.bucket == "test-bucket"
        assert s3_service.region == "us-east-1"

    def test_initialization_without_bucket(self, s3_service_no_bucket):
        """Test initialization without bucket configuration"""
        assert s3_service_no_bucket.bucket == ""
        # Should not raise error during initialization

    def test_initialization_db_error(self):
        """Test initialization when database connection fails"""
        with patch("app.services.s3_data_service.settings") as mock_settings:
            mock_settings.S3_BUCKET = "test-bucket"

            with patch(
                "app.db.duckdb_engine.DuckDBEngine._initialize_connection"
            ) as mock_init:
                mock_init.side_effect = Exception("DB connection failed")

                with pytest.raises(
                    DataNotFoundError, match="S3 service initialization failed"
                ):
                    S3DataService()

    def test_get_data_path_success(self, s3_service):
        """Test successful S3 path construction"""
        result = s3_service.get_data_path("market_capitalization")
        assert result == "s3://test-bucket/market_capitalization.parquet"

    def test_get_data_path_no_bucket(self, s3_service_no_bucket):
        """Test S3 path without bucket configuration"""
        with pytest.raises(DataNotFoundError, match="S3 bucket not configured"):
            s3_service_no_bucket.get_data_path("test_field")

    def test_get_data_path_invalid_field_name(self, s3_service):
        """Test S3 path with invalid field names"""
        # Test empty field name
        with pytest.raises(
            DataNotFoundError, match="Field name must be a non-empty string"
        ):
            s3_service.get_data_path("")

        # Test None field name
        with pytest.raises(
            DataNotFoundError, match="Field name must be a non-empty string"
        ):
            s3_service.get_data_path(None)

        # Test field name with invalid characters
        with pytest.raises(DataNotFoundError, match="Invalid field name"):
            s3_service.get_data_path("file;.parquet")

    def test_get_data_path_valid_special_characters(self, s3_service):
        """Test S3 path with valid special characters"""
        valid_names = ["market_cap", "adtv-3-month", "price.data.2024"]

        for field_name in valid_names:
            result = s3_service.get_data_path(field_name)
            expected = f"s3://test-bucket/{field_name}.parquet"
            assert result == expected

    def test_s3_path_edge_cases(self, s3_service):
        """Test S3 path construction with edge cases"""
        test_cases = [
            ("a", "s3://test-bucket/a.parquet"),  # Single character
            (
                "very_long_field_name_that_is_still_valid",
                "s3://test-bucket/very_long_field_name_that_is_still_valid.parquet",
            ),
            ("mixedCase", "s3://test-bucket/mixedCase.parquet"),  # Mixed case
        ]

        for field_name, expected in test_cases:
            result = s3_service.get_data_path(field_name)
            assert result == expected


class TestDataServiceIntegration:
    """Integration tests for data services with real configurations"""

    @pytest.fixture
    def mock_db_engine(self):
        mock_engine = Mock(spec=DuckDBEngine)
        mock_engine.register_parquet_file = Mock()
        mock_engine.get_data_range = Mock(
            return_value=(pd.Timestamp("2020-01-01"), pd.Timestamp("2025-01-22"))
        )
        mock_engine.filter_data_by_dates = Mock(
            return_value=pd.DataFrame(
                {"date": ["2024-01-01"], "security": ["AAPL"], "value": [100.0]}
            )
        )
        return mock_engine

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_development_environment_local_storage(self, mock_db_engine, temp_data_dir):
        """Test local storage in development environment"""
        with patch("app.services.local_data_service.settings") as mock_settings:
            mock_settings.ENV = "development"
            mock_settings.STORAGE_BACKEND = "local"
            mock_settings.LOCAL_DATA_DIR = str(temp_data_dir)

            # Create test file
            test_file = temp_data_dir / "volume.parquet"
            pd.DataFrame({"data": [1, 2, 3]}).to_parquet(test_file)

            service = LocalDataService(db_engine=mock_db_engine)

            # Should use local file system
            result_path = service.get_data_path("volume")
            assert Path(result_path).resolve() == test_file.resolve()
            assert "s3://" not in result_path

    def test_production_environment_s3_storage(self, mock_db_engine):
        """Test S3 storage in production environment"""
        with patch("app.services.s3_data_service.settings") as mock_settings:
            mock_settings.ENV = "production"
            mock_settings.STORAGE_BACKEND = "s3"
            mock_settings.S3_BUCKET = "production-bucket"
            mock_settings.AWS_REGION = "us-east-1"

            service = S3DataService(db_engine=mock_db_engine)

            # Should use S3 paths
            result_path = service.get_data_path("market_capitalization")
            assert result_path == "s3://production-bucket/market_capitalization.parquet"
            assert "s3://" in result_path


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_unicode_field_names(self, temp_data_dir):
        """Test handling of unicode field names"""
        unicode_names = [
            "市场_数据",  # Chinese characters
            "café_price",  # Accented characters
            "naïve_volume",  # More accented characters
        ]

        with patch("app.services.local_data_service.settings") as mock_settings:
            mock_settings.LOCAL_DATA_DIR = str(temp_data_dir)
            service = LocalDataService()

            for unicode_name in unicode_names:
                # Create the file first
                file_path = temp_data_dir / f"{unicode_name}.parquet"
                df = pd.DataFrame({"data": [1, 2, 3]})
                df.to_parquet(file_path)

                try:
                    # Should work with unicode names
                    result_path = service.get_data_path(unicode_name)
                    assert Path(result_path).resolve() == file_path.resolve()
                finally:
                    file_path.unlink()


class TestConfigurationValidation:
    """Test configuration validation"""

    def test_missing_configuration_handling(self):
        """Test behavior with missing configuration"""
        # S3 service without bucket
        with patch("app.services.s3_data_service.settings") as mock_settings:
            mock_settings.S3_BUCKET = ""

            service = S3DataService()

            with pytest.raises(DataNotFoundError, match="S3 bucket not configured"):
                service.get_data_path("test")
