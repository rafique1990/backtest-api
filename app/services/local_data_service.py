import logging
import os
from pathlib import Path
from app.services.base_data_service import BaseDataService
from app.db.duckdb_engine import DuckDBEngine
from app.core.config import settings
from app.core.exceptions import (
    DataNotFoundError,
    FilePermissionError,
    InvalidFileTypeError,
)

logger = logging.getLogger(__name__)


class LocalDataService(BaseDataService):
    def __init__(self, db_engine: DuckDBEngine = None):
        super().__init__(db_engine)
        self.data_dir = Path(settings.LOCAL_DATA_DIR).resolve()
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"LocalDataService initialized with data directory: {self.data_dir}"
            )
        except PermissionError as e:
            logger.error(
                f"Permission denied creating data directory {self.data_dir}: {e}"
            )
            raise DataNotFoundError(f"Cannot create data directory: {e}") from e
        except Exception as e:
            logger.error(f"Failed to initialize LocalDataService: {e}")
            raise

    def get_data_path(self, field_name: str) -> str:
        if not field_name or not isinstance(field_name, str) or not field_name.strip():
            raise DataNotFoundError("Field name must be a non-empty string") from e

        # Validate field name to prevent path traversal - allow unicode and common financial field patterns
        import re

        # Allow letters, numbers, underscores, hyphens, dots, and unicode characters
        if not re.match(r"^[\w\-\.,\u00C0-\u017F\u4e00-\u9fff]+$", field_name):
            raise DataNotFoundError(f"Invalid field name: {field_name}") from e

        file_path = self.data_dir / f"{field_name}.parquet"

        if not file_path.exists():
            raise DataNotFoundError(f"Local data file not found: {file_path}")

        if file_path.is_dir():
            raise DataNotFoundError(
                f"Path exists but is a directory, not a file: {file_path}"
            )

        # Check file extension
        if file_path.suffix.lower() != ".parquet":
            raise InvalidFileTypeError(str(file_path), "parquet")

        # Check read permissions
        if not os.access(file_path, os.R_OK):
            raise FilePermissionError(str(file_path))

        return str(file_path)
