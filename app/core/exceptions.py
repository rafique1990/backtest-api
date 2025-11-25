import logging
from typing import Any

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(status_code={self.status_code}, message='{self.message}')>"


class BacktestException(AppException):
    pass


class CalendarRuleError(BacktestException):
    def __init__(
        self,
        message: str = "Invalid calendar rule",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=400, details=details)


class PortfolioSelectionError(BacktestException):
    def __init__(
        self,
        message: str = "Portfolio selection failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=400, details=details)


class DataNotFoundError(BacktestException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=404, details=details)


class InvalidBacktestConfiguration(BacktestException):
    def __init__(self, message: str = "Invalid backtest configuration"):
        super().__init__(message, status_code=400)


class BacktestExecutionError(BacktestException):
    def __init__(self, message: str = "Backtest execution failed"):
        super().__init__(message, status_code=500)


class PromptParsingError(AppException):
    def __init__(
        self,
        message: str = "Failed to parse prompt",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=422, details=details)


class DatabaseError(AppException):
    def __init__(self, message: str, original_error: Exception | None = None):
        details = (
            {"original_error_type": type(original_error).__name__}
            if original_error
            else {}
        )
        super().__init__(message, status_code=500, details=details)


class FactoryConfigurationError(InvalidBacktestConfiguration):
    """Raised when factory cannot create a component due to configuration issues."""

    def __init__(self, component_type: str, message: str):
        super().__init__(f"Factory error for {component_type}: {message}")


# Storage-specific exceptions
class StorageConfigurationError(AppException):
    def __init__(
        self,
        message: str = "Storage configuration error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=500, details=details)


class LocalStorageError(DataNotFoundError):
    def __init__(
        self,
        message: str = "Local storage error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details=details)


class S3StorageError(DataNotFoundError):
    def __init__(
        self,
        message: str = "S3 storage error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details=details)


class FilePermissionError(LocalStorageError):
    def __init__(self, file_path: str, message: str | None = None):
        if message is None:
            message = f"Permission denied for file: {file_path}"
        super().__init__(message, details={"file_path": file_path})


class InvalidFileTypeError(LocalStorageError):
    def __init__(self, file_path: str, expected_type: str = "parquet"):
        message = f"Invalid file type for {file_path}. Expected {expected_type} file."
        super().__init__(
            message, details={"file_path": file_path, "expected_type": expected_type}
        )
