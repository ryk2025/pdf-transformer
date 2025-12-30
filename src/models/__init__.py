"""
Base models and common types for PDF transformer service.

This module defines the foundational data structures used across the application.
All models use Pydantic for validation and type safety.
"""

from enum import Enum
from typing import TypeAlias

# Common type aliases
FileSize: TypeAlias = int  # File size in bytes
FilePath: TypeAlias = str  # File system path


class FileFormat(str, Enum):
    """Supported Excel file formats."""

    XLSX = "xlsx"
    XLS = "xls"


class ErrorType(str, Enum):
    """Error types for API responses."""

    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    CORRUPTED_FILE = "CORRUPTED_FILE"
    CONVERSION_FAILED = "CONVERSION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Constants
MAX_FILE_SIZE: FileSize = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_EXTENSIONS: set[str] = {".xlsx", ".xls"}
ALLOWED_MIME_TYPES: set[str] = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
}

__all__ = [
    "FileSize",
    "FilePath",
    "FileFormat",
    "ErrorType",
    "MAX_FILE_SIZE",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
]
