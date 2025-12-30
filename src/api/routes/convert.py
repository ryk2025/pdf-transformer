"""
Convert endpoint.

This module defines the /convert POST endpoint for Excel to PDF conversion.
"""

from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from src.lib.logging import get_logger
from src.services.converter.conversion_service import get_conversion_service

logger = get_logger(__name__)

router = APIRouter()


@router.post("/convert")
async def convert_excel_to_pdf(
    file: UploadFile = File(..., description="Excel file to convert (.xlsx or .xls)"),
) -> Response:
    """
    Convert an Excel file to PDF format.

    This endpoint accepts an Excel file upload and returns a PDF file.

    **Supported formats:**
    - .xlsx (Excel 2007+)
    - .xls (Excel 97-2003)

    **File size limit:** 10MB

    **Features:**
    - Multi-sheet support (each sheet becomes a PDF page)
    - Basic formatting preservation (borders, alignment, fonts)
    - Table structure preservation

    Args:
        file: Uploaded Excel file

    Returns:
        PDF file as binary response

    Raises:
        400: Invalid file format or corrupted file
        413: File size exceeds limit
        422: Conversion failed
        500: Internal server error
    """
    logger.info(f"Conversion request received: {file.filename}")

    # Get conversion service
    service = get_conversion_service()

    # Convert Excel to PDF
    pdf_bytes = await service.convert(file)

    # Generate output filename
    original_name = file.filename or "converted"
    pdf_filename = Path(original_name).stem + ".pdf"

    logger.info(f"Conversion successful: {pdf_filename}")

    # Return PDF as response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{pdf_filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


__all__ = ["router"]
