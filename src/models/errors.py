"""
Error response models.

This module defines the error response models for the API.
"""

from pydantic import BaseModel, Field

from src.models import ErrorType


class ErrorResponse(BaseModel):
    """
    Error response model.

    Returned when an error occurs during API processing.
    """

    error_type: ErrorType = Field(
        ...,
        description="Type of error that occurred",
        examples=[ErrorType.INVALID_FILE_FORMAT],
    )

    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Unsupported file format. Please upload .xlsx or .xls files only."],
    )

    status_code: int = Field(
        ...,
        description="HTTP status code",
        examples=[400],
    )

    detail: str | None = Field(
        default=None,
        description="Additional error details (debug information)",
        examples=["File signature does not match expected format"],
    )


__all__ = ["ErrorResponse"]
