"""
PDF generator service.

This module handles generating PDF files from Excel data structures.
"""

from io import BytesIO
from pathlib import Path
from typing import Any
from collections import defaultdict

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
        logger.info(
            f"Successfully wrote PDF: {output_path.name} ({len(pdf_bytes)} bytes)"
        )

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
                    col_widths = calculate_column_widths(
                        sheet, num_columns, EXCEL_UNIT_TO_POINTS
                    )
                    base_row_heights = calculate_row_heights(sheet, len(table_data))

                    # Calculate scale to fit page
                    # We need to find a scale where:
                    # - width: sum(col_widths) * scale <= page_width
                    # - height: sum([max(h * scale, MIN_ROW_HEIGHT)]) <= page_height
                    MIN_ROW_HEIGHT = 7.0

                    total_width = sum(col_widths)
                    total_height = sum(base_row_heights)

                    width_scale = page_width / total_width if total_width > 0 else 1.0

                    # For height, consider MIN_ROW_HEIGHT and add small extra space
                    # for rows that contain wrapped cells to avoid border contact
                    rows_with_wrap = {r for (r, _c) in cells_with_wrap}
                    # Identify rows that contain explicit line breaks (multi-line list items)
                    multiline_rows: set[int] = set()
                    # Track max explicit line count per row for conservative height adjustments
                    row_line_counts: dict[int, int] = defaultdict(int)
                    try:
                        for c in sheet.cells:
                            if (
                                0 <= c.row < sheet.max_row
                                and 0 <= c.column < sheet.max_column
                            ):
                                if isinstance(c.value, str):
                                    vstrip = c.value.strip()
                                    if "\n" in c.value:
                                        multiline_rows.add(c.row)
                                        # Count explicit lines for height estimation (ignore empty lines)
                                        lines = [
                                            ln
                                            for ln in c.value.strip("\n").split("\n")
                                            if ln.strip() != ""
                                        ]
                                        if lines:
                                            row_line_counts[c.row] = max(
                                                row_line_counts[c.row], len(lines)
                                            )
                                    # No font-size based inflation here to avoid overestimation
                    except Exception:
                        pass
                    # Identify rows immediately preceding a multi-line row to avoid pre-list gap
                    pre_multiline_rows: set[int] = set(
                        r for r in range(sheet.max_row) if (r + 1) in multiline_rows
                    )

                    def calc_scaled_height(s: float) -> float:
                        total = 0.0
                        for r, h in enumerate(base_row_heights):
                            # add extra space for wrapped rows, but exclude multi-line rows and the row before them to avoid pre-list gap
                            extra = (
                                2.0
                                if (
                                    r in rows_with_wrap
                                    and r not in multiline_rows
                                    and r not in pre_multiline_rows
                                )
                                else 0.0
                            )
                            total += max(h * s, MIN_ROW_HEIGHT) + extra
                        return total

                    # Binary search for optimal scale considering MIN_ROW_HEIGHT
                    low, high = 0.1, 1.0
                    height_scale = high

                    for _ in range(50):
                        mid = (low + high) / 2
                        scaled_height = calc_scaled_height(mid)

                        if scaled_height <= page_height:
                            height_scale = mid
                            low = mid
                        else:
                            high = mid

                        if abs(scaled_height - page_height) < 1.0:
                            break

                    scale = min(width_scale, height_scale, 1.0)

                    logger.info(
                        f"Table: {total_width:.0f}×{total_height:.0f}pt "
                        f"→ A4: {page_width:.0f}×{page_height:.0f}pt "
                        f"→ Scale: {scale:.1%}"
                    )

                    # Process wrapped cells
                    # Normalize wrapped cells and bullet cells for consistent spacing and alignment
                    self._process_wrapped_cells(
                        table_data, cells_with_wrap, sheet, scale
                    )
                    # Also normalize multi-line cells even if not wrapped
                    try:
                        multiline_cells: set[tuple[int, int]] = set(
                            (
                                c.row,
                                c.column,
                            )
                            for c in sheet.cells
                            if isinstance(getattr(c, "value", None), str)
                            and ("\n" in getattr(c, "value"))
                        )
                    except Exception:
                        multiline_cells = set()
                    if multiline_cells:
                        self._process_wrapped_cells(
                            table_data, multiline_cells, sheet, scale
                        )

                    # Create table with scaled dimensions
                    scaled_col_widths = [w * scale for w in col_widths]
                    row_heights = []
                    for r, h in enumerate(base_row_heights):
                        extra = (
                            2.0
                            if (
                                r in rows_with_wrap
                                and r not in multiline_rows
                                and r not in pre_multiline_rows
                            )
                            else 0.0
                        )
                        row_heights.append(max(h * scale, MIN_ROW_HEIGHT) + extra)

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

    def _process_wrapped_cells(self, table_data, cells_with_wrap, sheet, scale) -> None:
        """Process cells that need text wrapping."""
        for row, col in cells_with_wrap:
            if row < len(table_data) and col < len(table_data[row]):
                cell_value = table_data[row][col]
                if not cell_value:
                    continue
                # If already processed into a Paragraph (e.g., from a previous pass), skip
                if isinstance(cell_value, Paragraph):
                    continue

                # Get cell object for styling
                cell_obj = next(
                    (c for c in sheet.cells if c.row == row and c.column == col),
                    None,
                )

                # Calculate font size: scale with table scale for consistency
                if cell_obj and cell_obj.font_size:
                    font_size = max(6.0, float(cell_obj.font_size) * scale)
                else:
                    font_size = max(6.0, 10.0 * scale)

                # Determine alignment
                alignment = TA_LEFT
                if cell_obj and cell_obj.alignment_horizontal:
                    if cell_obj.alignment_horizontal == "center":
                        alignment = TA_CENTER
                    elif cell_obj.alignment_horizontal == "right":
                        alignment = TA_RIGHT

                # Create paragraph with controlled spacing
                # - Strip leading/trailing newlines to avoid accidental blank lines
                # - Collapse multiple <br/> sequences
                # - Normalize bullet lines (remove leading ideographic/ASCII spaces)
                # - Reduce leading to tighten inter-line spacing
                import re

                cell_value_stripped = cell_value.strip("\n")
                # Normalize bullet lines: trim leading spaces so bullets align
                lines = cell_value_stripped.split("\n")
                norm_lines = []
                for ln in lines:
                    # remove leading ASCII spaces and full-width spaces
                    ln2 = re.sub(r"^[ \u3000]+", "", ln)
                    norm_lines.append(ln2)
                cell_value_html = "<br/>".join(norm_lines)
                # Collapse consecutive <br/> to a single one
                cell_value_html = re.sub(
                    r"(?:<br\s*/?>\s*){2,}", "<br/>", cell_value_html
                )
                # Remove any leading/trailing <br/>
                cell_value_html = re.sub(r"^(?:<br\s*/?>\s*)+", "", cell_value_html)
                cell_value_html = re.sub(r"(?:<br\s*/?>\s*)+$", "", cell_value_html)

                para_style = ParagraphStyle(
                    "CellStyle",
                    fontName=JAPANESE_FONT,
                    fontSize=font_size,
                    leading=max(font_size * 1.15, font_size + 1),
                    alignment=alignment,
                    spaceBefore=0,
                    spaceAfter=0,
                    firstLineIndent=0,
                    leftIndent=0,
                )
                # Improve CJK wrapping when available
                try:
                    setattr(para_style, "wordWrap", "CJK")
                except Exception:
                    pass

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
