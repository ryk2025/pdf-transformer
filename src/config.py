"""
Application configuration management.

This module manages environment settings and configuration for the PDF transformer service.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Settings can be overridden via environment variables with APP_ prefix.
    """

    # File upload settings
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file size in bytes",
    )

    allowed_extensions: set[str] = Field(
        default={".xlsx", ".xls"},
        description="Allowed file extensions",
    )

    allowed_mime_types: set[str] = Field(
        default={
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        },
        description="Allowed MIME types",
    )

    # Processing settings
    conversion_timeout: int = Field(
        default=30,
        description="Conversion timeout in seconds",
    )

    temp_dir: Path = Field(
        default_factory=lambda: Path("/tmp/pdf-transformer"),
        description="Temporary directory for file processing",
    )

    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )

    port: int = Field(
        default=8000,
        description="Server port",
    )

    debug: bool = Field(
        default=False,
        description="Debug mode",
    )

    # API settings
    api_title: str = Field(
        default="Excel to PDF Conversion API",
        description="API title",
    )

    api_version: str = Field(
        default="0.1.0",
        description="API version",
    )

    api_description: str = Field(
        default="REST API service for converting Excel files to PDF format",
        description="API description",
    )

    # Security settings
    temp_file_permissions: int = Field(
        default=0o600,
        description="File permissions for temporary files (owner read/write only)",
    )

    log_sanitize: bool = Field(
        default=True,
        description="Sanitize sensitive information in logs",
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_temp_dir(self) -> None:
        """Create temporary directory if it doesn't exist."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        # Set secure permissions on temp directory
        os.chmod(self.temp_dir, 0o700)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings instance
    """
    settings = Settings()
    settings.ensure_temp_dir()
    return settings


# Export singleton instance
settings: Final[Settings] = get_settings()

__all__ = [
    "Settings",
    "get_settings",
    "settings",
]
