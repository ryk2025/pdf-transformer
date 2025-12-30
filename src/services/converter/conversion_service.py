"""
Conversion service orchestrator.

This module orchestrates the conversion process from Excel to PDF.
"""

from pathlib import Path

from fastapi import UploadFile

from src.lib.exceptions import InvalidFileFormat
from src.lib.logging import get_logger, log_file_operation
from src.lib.validation import validate_file
from src.models import ALLOWED_EXTENSIONS, FileFormat
from src.services.converter.excel_parser import get_excel_parser
from src.services.converter.pdf_generator import get_pdf_generator
from src.services.storage.temp_storage import get_temp_storage

logger = get_logger(__name__)


class ConversionService:
    """Service for orchestrating Excel to PDF conversion."""

    def __init__(self) -> None:
        """Initialize conversion service with dependencies."""
        self.temp_storage = get_temp_storage()
        self.excel_parser = get_excel_parser()
        self.pdf_generator = get_pdf_generator()

    def _determine_format(self, filename: str) -> FileFormat:
        """
        Determine file format from filename extension.

        Args:
            filename: Name of the file

        Returns:
            FileFormat enum value

        Raises:
            InvalidFileFormat: If extension is not supported
        """
        ext = Path(filename).suffix.lower()

        if ext == ".xlsx":
            return FileFormat.XLSX
        elif ext == ".xls":
            return FileFormat.XLS
        else:
            raise InvalidFileFormat(
                f"Unsupported file extension: {ext}. "
                f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )

    async def convert(self, file: UploadFile) -> bytes:
        """
        Convert an uploaded Excel file to PDF.

        This orchestrates the entire conversion process:
        1. Validate the uploaded file
        2. Save to temporary storage
        3. Parse Excel file
        4. Generate PDF
        5. Clean up temporary files

        Args:
            file: Uploaded Excel file

        Returns:
            PDF file content as bytes

        Raises:
            InvalidFileFormat: If file format is not supported
            FileTooLarge: If file size exceeds limit
            CorruptedFile: If file is corrupted
            ConversionFailed: If conversion fails
        """
        filename = file.filename or "unknown.xlsx"
        content_type = file.content_type or "application/octet-stream"

        log_file_operation(logger, "upload_received", filename, size=file.size)

        # Determine file format
        file_format = self._determine_format(filename)

        # Validate file
        file_obj = file.file
        validate_file(
            file=file_obj,
            filename=filename,
            content_type=content_type,
            size=file.size or 0,
        )

        log_file_operation(logger, "validation_passed", filename)

        # Save to temporary storage
        file_obj.seek(0)
        temp_path = self.temp_storage.save_upload(
            file_obj,
            suffix=Path(filename).suffix,
        )

        try:
            log_file_operation(logger, "parsing_start", filename)

            # Parse Excel file
            workbook = self.excel_parser.parse(temp_path, file_format)

            log_file_operation(
                logger,
                "parsing_complete",
                filename,
                sheets=len(workbook.sheets),
            )

            # Generate PDF
            log_file_operation(logger, "pdf_generation_start", filename)

            pdf_bytes = self.pdf_generator.generate_to_bytes(workbook)

            log_file_operation(
                logger,
                "pdf_generation_complete",
                filename,
                size=len(pdf_bytes),
            )

            return pdf_bytes

        finally:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
                logger.debug(f"Cleaned up temp file: {temp_path.name}")


# Singleton instance
_conversion_service: ConversionService | None = None


def get_conversion_service() -> ConversionService:
    """
    Get the conversion service instance.

    Returns:
        ConversionService instance
    """
    global _conversion_service
    if _conversion_service is None:
        _conversion_service = ConversionService()
    return _conversion_service


__all__ = [
    "ConversionService",
    "get_conversion_service",
]
