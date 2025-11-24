import logging
from app.services.base_data_service import BaseDataService
from app.db.duckdb_engine import DuckDBEngine
from app.core.config import settings
from app.core.exceptions import DataNotFoundError

logger = logging.getLogger(__name__)


class S3DataService(BaseDataService):
    def __init__(self, db_engine: DuckDBEngine = None):
        super().__init__(db_engine)
        self.bucket = settings.S3_BUCKET
        self.region = settings.AWS_REGION

        if not self.bucket:
            logger.warning("S3DataService initialized without bucket configuration")
        else:
            try:
                self.db_engine._initialize_connection()
                logger.info(
                    f"S3DataService initialized for bucket: {self.bucket} in region: {self.region}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3DataService: {e}")
                raise DataNotFoundError(f"S3 service initialization failed: {e}")

    def get_data_path(self, field_name: str) -> str:
        if not self.bucket:
            raise DataNotFoundError("S3 bucket not configured")

        if not field_name or not isinstance(field_name, str) or not field_name.strip():
            raise DataNotFoundError("Field name must be a non-empty string")

        # Validate field name - allow letters, numbers, underscores, hyphens, and dots
        import re

        if not re.match(r"^[\w\-\.,]+$", field_name):
            raise DataNotFoundError(f"Invalid field name: {field_name}")

        return f"s3://{self.bucket}/{field_name}.parquet"
