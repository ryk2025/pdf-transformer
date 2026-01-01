"""
PDF generator service.

This module handles generating PDF files from Excel data structures.
"""

from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Table,
)

from src.lib.exceptions import ConversionFailed
from src.lib.logging import get_logger
from src.models.excel import ExcelWorkbook
from src.services.converter.formatting_utils import (
    calculate_column_widths,
    calculate_row_heights,
)
from src.services.converter.style_builder import TableStyleBuilder
from src.services.converter.table_builder import sheet_to_table_data

logger = get_logger(__name__)

# Constants
EXCEL_UNIT_TO_POINTS = 1.8

# Register Japanese fonts
try:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    
    from reportlab.lib.fonts import addMapping
    addMapping("HeiseiMin-W3", 0, 0, "HeiseiMin-W3")
    addMapping("HeiseiMin-W3", 1, 0, "HeiseiKakuGo-W5")
    addMapping("HeiseiMin-W3", 0, 1, "HeiseiMin-W3")
    addMapping("HeiseiMin-W3", 1, 1, "HeiseiKakuGo-W5")

    JAPANESE_FONT = "HeiseiMin-W3"
    JAPANESE_FONT_BOLD = "HeiseiKakuGo-W5"
    logger.info("Japanese fonts registered successfully")
except Exception as e:
    logger.warning(f"Failed to register Japanese fonts: {e}")
    JAPANESE_FONT = "Helvetica"
    JAPANESE_FONT_BOLD = "Helvetica-Bold"


class PDFGenerator:
    """Service for generating PDF files from Excel data."""

    def __init__(self):
        """Initialize PDF generator."""
        self.style_builder = TableStyleBuilder(JAPANESE_FONT, JAPANESE_FONT_BOLD)

    def generate(self, workbook: ExcelWorkbook, output_path: Path) -> None:
        """
        Generate a PDF file from an Excel workbook.

        Args:
            workbook: Excel workbook data
            output_path: Path to save the PDF file

        Raises:
            ConversionFailed: If PDF generation fails
        """
        logger.info(f"Generating PDF from {len(workbook.sheets)} sheet(s)")
        pdf_bytes = self.generate_to_bytes(workbook)
        output_path.write_bytes(pdf_bytes)
        logger.info(f"Successfully wrote PDF: {output_path.name} ({len(pdf_bytes)} bytes)")

    def generate_to_bytes(self, workbook: ExcelWorkbook) -> bytes:
        """
        Generate a PDF file to bytes (in-memory).

        Args:
            workbook: Excel workbook data

        Returns:
            PDF file content as bytes

        Raises:
            ConversionFailed: If PDF generation fails
        """
        logger.info(f"Generating PDF from {len(workbook.sheets)} sheet(s) to memory")

        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.3 * inch,
                leftMargin=0.3 * inch,
                topMargin=0.4 * inch,
                bottomMargin=0.4 * inch,
            )

            story = []
            page_width = A4[0] - 1.0 * inch
            page_height = A4[1] - 0.8 * inch

            for idx, sheet in enumerate(workbook.sheets):
                if sheet.cells:
                    table_data, span_commands, cells_border_info, cells_with_wrap = (
                        sheet_to_table_data(sheet)
                    )

                    # Calculate dimensions
                    num_columns = len(table_data[0]) if table_data else 0
                    col_widths = calculate_column_widths(sheet, num_columns, EXCEL_UNIT_TO_POINTS)
                    base_row_heights = calculate_row_heights(sheet, len(table_data))

                    # Calculate scale to fit page
                    total_width = sum(col_widths)
                    total_height = sum(base_row_heights)
                    
                    width_scale = page_width / total_width if total_width > 0 else 1.0
                    height_scale = page_height / total_height if total_height > 0 else 1.0
                    scale = min(width_scale, height_scale, 1.0)

                    logger.info(
                        f"Table: {total_width:.0f}×{total_height:.0f}pt "
                        f"→ A4: {page_width:.0f}×{page_height:.0f}pt "
                        f"→ Scale: {scale:.1%}"
                    )

                    # Process wrapped cells
                    self._process_wrapped_cells(
                        table_data, cells_with_wrap, sheet, scale
                    )

                    # Create table with scaled dimensions
                    scaled_col_widths = [w * scale for w in col_widths]
                    row_heights = [max(h * scale + 3, 12) for h in base_row_heights]

                    table = Table(
                        table_data,
                        colWidths=scaled_col_widths,
                        rowHeights=row_heights,
                        repeatRows=0,
                    )

                    # Apply styling
                    table_style = self.style_builder.build_table_style(
                        sheet, span_commands, cells_border_info, scale
                    )
                    table.setStyle(table_style)

                    story.append(table)
                else:
                    from reportlab.lib.styles import getSampleStyleSheet
                    styles = getSampleStyleSheet()
                    story.append(Paragraph("<i>Empty sheet</i>", styles["Normal"]))

                # Add page break between sheets
                if idx < len(workbook.sheets) - 1:
                    story.append(PageBreak())

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Successfully generated PDF ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise ConversionFailed(f"Failed to generate PDF: {str(e)}")

    def _process_wrapped_cells(
        self, table_data, cells_with_wrap, sheet, scale
    ) -> None:
        """Process cells that need text wrapping."""
        for row, col in cells_with_wrap:
            if row < len(table_data) and col < len(table_data[row]):
                cell_value = table_data[row][col]
                if not cell_value:
                    continue

                # Get cell object for styling
                cell_obj = next(
                    (c for c in sheet.cells if c.row == row and c.column == col),
                    None,
                )

                # Calculate font size
                base_font_size = (
                    max(6, cell_obj.font_size - 2) if cell_obj and cell_obj.font_size else 8
                )
                font_size = max(3, base_font_size * scale)

                # Determine alignment
                alignment = TA_LEFT
                if cell_obj and cell_obj.alignment_horizontal:
                    if cell_obj.alignment_horizontal == "center":
                        alignment = TA_CENTER
                    elif cell_obj.alignment_horizontal == "right":
                        alignment = TA_RIGHT

                # Create paragraph
                cell_value_html = cell_value.replace("\n", "<br/>")
                para_style = ParagraphStyle(
                    "CellStyle",
                    fontName=JAPANESE_FONT,
                    fontSize=font_size,
                    leading=font_size * 1.5,
                    alignment=alignment,
                )
                table_data[row][col] = Paragraph(cell_value_html, para_style)


# Singleton instance
_pdf_generator: PDFGenerator | None = None


def get_pdf_generator() -> PDFGenerator:
    """
    Get the PDF generator service instance.

    Returns:
        PDFGenerator instance
    """
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFGenerator()
    return _pdf_generator


__all__ = ["PDFGenerator", "get_pdf_generator"]
