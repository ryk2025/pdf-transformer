"""
Conversion request and response models.

This module defines the API models for Excel to PDF conversion.
"""

from pydantic import BaseModel, Field


class ConversionRequest(BaseModel):
    """
    Conversion request model (for documentation purposes).
    
    In practice, file uploads use multipart/form-data, not JSON.
    This model documents the expected request structure.
    """
    
    filename: str = Field(
        ...,
        description="Original filename of the uploaded Excel file",
        examples=["report.xlsx", "data.xls"],
    )
    
    content_type: str = Field(
        ...,
        description="MIME type of the uploaded file",
        examples=[
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ],
    )
    
    size: int = Field(
        ...,
        description="File size in bytes",
        gt=0,
        examples=[1024, 1048576],
    )


class ConversionResponse(BaseModel):
    """
    Conversion response model (for documentation purposes).
    
    The actual response is a binary PDF file stream.
    This model documents the response structure.
    """
    
    content_type: str = Field(
        default="application/pdf",
        description="MIME type of the response",
    )
    
    filename: str = Field(
        ...,
        description="Generated PDF filename",
        examples=["report.pdf", "data.pdf"],
    )
    
    size: int = Field(
        ...,
        description="PDF file size in bytes",
        gt=0,
    )


__all__ = [
    "ConversionRequest",
    "ConversionResponse",
]
