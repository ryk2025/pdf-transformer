"""
PDF generator service.

This module handles generating PDF files from Excel data structures.
"""

from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.lib.exceptions import ConversionFailed
from src.lib.logging import get_logger
from src.models.excel import ExcelCell, ExcelSheet, ExcelWorkbook
from src.models.pdf import PDFDocument, PDFPage, PDFTable

logger = get_logger(__name__)

# Register Japanese CID fonts for proper Japanese character rendering
try:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))  # Japanese Serif
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))  # Japanese Sans-serif
    JAPANESE_FONT = "HeiseiMin-W3"
    JAPANESE_FONT_BOLD = "HeiseiKakuGo-W5"
    logger.info("Japanese CID fonts registered successfully")
except Exception as e:
    logger.warning(f"Failed to register Japanese fonts: {e}, falling back to Helvetica")
    JAPANESE_FONT = "Helvetica"
    JAPANESE_FONT_BOLD = "Helvetica-Bold"


def _hex_to_rgb_tuple(hex_color: str) -> tuple[float, float, float]:
    """
    Convert hex color to RGB tuple (0-1 range).

    Args:
        hex_color: Hex color string (e.g., "FF0000")

    Returns:
        RGB tuple with values in 0-1 range
    """
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)
    except (ValueError, IndexError):
        return (0.0, 0.0, 0.0)


def _sheet_to_table_data(
    sheet: ExcelSheet,
) -> tuple[
    list[list[str]],
    list[tuple[str, tuple[int, int], tuple[int, int]]],
    dict[tuple[int, int], dict[str, str | None]],
    set[tuple[int, int]],
]:
    """
    Convert Excel sheet to 2D table data with span information.

    Creates a compact table containing only the used range (cells with content or
    part of merged regions) rather than the full sparse grid.

    Args:
        sheet: Excel sheet

    Returns:
        Tuple of (data, span_commands, cells_border_info, cells_with_wrap) where:
        - data is 2D list of cell values as strings (only used range)
        - span_commands is list of ReportLab SPAN commands for merged cells
        - cells_border_info is dict mapping (row, col) to border info dict with keys:
          'left', 'right', 'top', 'bottom' (each value is border style or None)
        - cells_with_wrap is set of (row, col) tuples for cells that need text wrapping
    """
    # Determine the actual used range by finding max row/col with content
    if not sheet.cells:
        # Empty sheet, return minimal table
        return [[""]], [], set()

    max_content_row = 0
    max_content_col = 0

    for cell in sheet.cells:
        # Consider the cell's actual span when determining bounds
        cell_max_row = cell.row + cell.row_span - 1
        cell_max_col = cell.column + cell.col_span - 1
        max_content_row = max(max_content_row, cell_max_row)
        max_content_col = max(max_content_col, cell_max_col)

    # Add 1 because we're zero-indexed
    actual_rows = max_content_row + 1
    actual_cols = max_content_col + 1

    logger.info(
        f"Table dimensions: using {actual_rows}×{actual_cols} "
        f"(original: {sheet.max_row}×{sheet.max_column})"
    )

    # Initialize grid with only the used range
    data: list[list[str]] = []
    for _ in range(actual_rows):
        data.append([""] * actual_cols)

    # Track which cells should have borders and their individual side styles
    cells_border_info: dict[tuple[int, int], dict[str, str | None]] = {}
    span_commands: list[tuple[str, tuple[int, int], tuple[int, int]]] = []
    cells_with_wrap: set[tuple[int, int]] = set()

    # Fill grid with cell values and track spans
    for cell in sheet.cells:
        if 0 <= cell.row < actual_rows and 0 <= cell.column < actual_cols:
            value = cell.value
            if value is None:
                value = ""

            # Handle vertical text (rotation 255 or 90 degrees)
            # Excel uses 255 for vertical text orientation
            text_value = str(value)
            if cell.text_rotation == 255 or cell.text_rotation == 90:
                # Format as vertical text by adding line breaks between characters
                text_value = "\n".join(list(text_value))

            data[cell.row][cell.column] = text_value

            # Track cells that need text wrapping
            if cell.wrap_text:
                cells_with_wrap.add((cell.row, cell.column))

            # If cell has span, add SPAN command and mark all cells in span
            if cell.row_span > 1 or cell.col_span > 1:
                end_row = min(cell.row + cell.row_span - 1, actual_rows - 1)
                end_col = min(cell.column + cell.col_span - 1, actual_cols - 1)

                span_commands.append(
                    ("SPAN", (cell.column, cell.row), (end_col, end_row))
                )

                # If this merged cell has borders in Excel, mark ALL cells in the span
                if cell.has_border:
                    border_info = {
                        "left": cell.border_left,
                        "right": cell.border_right,
                        "top": cell.border_top,
                        "bottom": cell.border_bottom,
                    }
                    for r in range(cell.row, end_row + 1):
                        for c in range(cell.column, end_col + 1):
                            cells_border_info[(r, c)] = border_info
            else:
                # Single cell - add border sides if Excel has border set
                if cell.has_border:
                    cells_border_info[(cell.row, cell.column)] = {
                        "left": cell.border_left,
                        "right": cell.border_right,
                        "top": cell.border_top,
                        "bottom": cell.border_bottom,
                    }

    return data, span_commands, cells_border_info, cells_with_wrap


def _calculate_column_widths(
    sheet: ExcelSheet, page_width: float, num_columns: int
) -> list[float]:
    """
    Calculate column widths for PDF table based on Excel column widths.

    Args:
        sheet: Excel sheet with column width information
        page_width: Available page width in points
        num_columns: Actual number of columns in the table (may be less than max_column)

    Returns:
        List of column widths in points
    """
    if not sheet.column_widths:
        # Equal width for all columns
        return [page_width / num_columns] * num_columns

    # Minimum column width to ensure text is visible (in points)
    MIN_COL_WIDTH = 8.0  # Roughly enough for 1-2 characters

    # Excel width units are approximately 1/8 inch for default font
    # Convert Excel units to PDF points proportionally
    excel_widths = []
    for col_idx in range(num_columns):
        width = sheet.column_widths.get(col_idx, 8.43)  # Default Excel width ~8.43
        excel_widths.append(width)

    total_excel_width = sum(excel_widths)
    if total_excel_width == 0:
        return [page_width / num_columns] * num_columns

    # First attempt: scale proportionally
    pdf_widths = [(w / total_excel_width) * page_width for w in excel_widths]

    # Apply minimum width and recalculate
    # This ensures very narrow columns are still readable
    adjusted_widths = []
    extra_width_needed = 0.0

    for width in pdf_widths:
        if width < MIN_COL_WIDTH:
            adjusted_widths.append(MIN_COL_WIDTH)
            extra_width_needed += MIN_COL_WIDTH - width
        else:
            adjusted_widths.append(width)

    # If we added extra width, scale down the wider columns proportionally
    if extra_width_needed > 0:
        total_adjusted = sum(adjusted_widths)
        if total_adjusted > page_width:
            # Scale all columns down to fit
            scale_factor = page_width / total_adjusted
            adjusted_widths = [w * scale_factor for w in adjusted_widths]

    return adjusted_widths


def _create_table_style(
    sheet: ExcelSheet,
    span_commands: list[tuple[str, tuple[int, int], tuple[int, int]]] | list[Any],
    cells_border_info: dict[tuple[int, int], dict[str, str | None]],
) -> TableStyle:
    """
    Create ReportLab TableStyle from Excel sheet formatting.

    Only applies borders to cells that have borders set in Excel, with appropriate styles
    on individual sides. This creates a cleaner form-like appearance without excessive grid lines.

    Args:
        sheet: Excel sheet with formatting information
        span_commands: List of SPAN commands for merged cells
        cells_border_info: Dict mapping (row, col) to border info with individual side styles

    Returns:
        TableStyle object
    """
    style_commands: list[Any] = [
        ("FONTNAME", (0, 0), (-1, -1), JAPANESE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]

    # DO NOT apply global INNERGRID or BOX - we'll add borders selectively
    # based only on cells that have borders set in Excel

    # Add span commands first
    style_commands.extend(span_commands)

    # Apply borders ONLY to cells that have borders set in Excel, per individual side
    for (row, col), border_info in cells_border_info.items():
        cell_pos = (col, row)

        # Helper function to get line style parameters
        def get_line_params(border_style: str | None) -> tuple[float, list[int] | None]:
            if not border_style:
                return 0.5, None

            if border_style == "thin":
                return 0.5, None
            elif border_style == "medium":
                return 1.0, None
            elif border_style == "thick":
                return 1.5, None
            elif border_style == "dotted":
                return 0.5, [1, 2]  # 1pt on, 2pt off
            elif border_style == "dashed":
                return 0.5, [3, 2]  # 3pt on, 2pt off
            else:
                return 0.5, None

        # Apply left border if present
        if border_info.get("left"):
            line_width, dash_pattern = get_line_params(border_info["left"])
            if dash_pattern:
                style_commands.append(
                    (
                        "LINEBEFORE",
                        cell_pos,
                        cell_pos,
                        line_width,
                        colors.black,
                        None,
                        dash_pattern,
                    )
                )
            else:
                style_commands.append(
                    ("LINEBEFORE", cell_pos, cell_pos, line_width, colors.black)
                )

        # Apply right border if present
        if border_info.get("right"):
            line_width, dash_pattern = get_line_params(border_info["right"])
            if dash_pattern:
                style_commands.append(
                    (
                        "LINEAFTER",
                        cell_pos,
                        cell_pos,
                        line_width,
                        colors.black,
                        None,
                        dash_pattern,
                    )
                )
            else:
                style_commands.append(
                    ("LINEAFTER", cell_pos, cell_pos, line_width, colors.black)
                )

        # Apply top border if present
        if border_info.get("top"):
            line_width, dash_pattern = get_line_params(border_info["top"])
            if dash_pattern:
                style_commands.append(
                    (
                        "LINEABOVE",
                        cell_pos,
                        cell_pos,
                        line_width,
                        colors.black,
                        None,
                        dash_pattern,
                    )
                )
            else:
                style_commands.append(
                    ("LINEABOVE", cell_pos, cell_pos, line_width, colors.black)
                )

        # Apply bottom border if present
        if border_info.get("bottom"):
            line_width, dash_pattern = get_line_params(border_info["bottom"])
            if dash_pattern:
                style_commands.append(
                    (
                        "LINEBELOW",
                        cell_pos,
                        cell_pos,
                        line_width,
                        colors.black,
                        None,
                        dash_pattern,
                    )
                )
            else:
                style_commands.append(
                    ("LINEBELOW", cell_pos, cell_pos, line_width, colors.black)
                )

    # Apply cell-specific formatting
    for cell in sheet.cells:
        if 0 <= cell.row < sheet.max_row and 0 <= cell.column < sheet.max_column:
            start_pos = (cell.column, cell.row)

            # For merged cells, apply styling to the entire span
            if cell.row_span > 1 or cell.col_span > 1:
                end_row = min(cell.row + cell.row_span - 1, sheet.max_row - 1)
                end_col = min(cell.column + cell.col_span - 1, sheet.max_column - 1)
                end_pos = (end_col, end_row)
            else:
                end_pos = (cell.column, cell.row)

            # Font styling
            if cell.font_bold:
                style_commands.append(
                    ("FONTNAME", start_pos, end_pos, JAPANESE_FONT_BOLD)
                )

            # Apply actual font size from Excel, reduced by 2 points for better PDF rendering
            if cell.font_size:
                adjusted_font_size = max(6, cell.font_size - 2)  # Minimum 6pt
                style_commands.append(
                    ("FONTSIZE", start_pos, end_pos, adjusted_font_size)
                )

            # Font color
            if cell.font_color and cell.font_color != "000000":
                rgb = _hex_to_rgb_tuple(cell.font_color)
                style_commands.append(
                    ("TEXTCOLOR", start_pos, end_pos, colors.Color(*rgb))
                )

            # Background color
            if cell.bg_color:
                rgb = _hex_to_rgb_tuple(cell.bg_color)
                style_commands.append(
                    ("BACKGROUND", start_pos, end_pos, colors.Color(*rgb))
                )

            # Horizontal alignment
            if cell.alignment_horizontal:
                align_map = {
                    "left": "LEFT",
                    "center": "CENTER",
                    "right": "RIGHT",
                }
                alignment = align_map.get(cell.alignment_horizontal, "LEFT")
                style_commands.append(("ALIGN", start_pos, end_pos, alignment))

            # Vertical alignment
            if cell.alignment_vertical:
                valign_map = {
                    "top": "TOP",
                    "center": "MIDDLE",
                    "middle": "MIDDLE",
                    "bottom": "BOTTOM",
                }
                valignment = valign_map.get(cell.alignment_vertical, "TOP")
                style_commands.append(("VALIGN", start_pos, end_pos, valignment))

    return TableStyle(style_commands)


class PDFGenerator:
    """Service for generating PDF files from Excel data."""

    def generate(self, workbook: ExcelWorkbook, output_path: Path) -> None:
        """
        Generate a PDF file from an Excel workbook.

        Args:
            workbook: Excel workbook data
            output_path: Path to save the PDF file

        Raises:
            ConversionFailed: If PDF generation fails
        """
        logger.info(
            f"Generating PDF from {len(workbook.sheets)} sheet(s): "
            f"{output_path.name}"
        )

        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            # Build story (content)
            story: list[PageBreak | Spacer | Paragraph | Table] = []
            styles = getSampleStyleSheet()

            # Calculate available page width for tables
            page_width = A4[0] - 1.0 * inch  # A4 width minus margins

            for idx, sheet in enumerate(workbook.sheets):
                # Add sheet title
                title = Paragraph(
                    f"<b>{sheet.name}</b>",
                    styles["Heading1"],
                )
                story.append(title)
                story.append(Spacer(1, 0.2 * inch))

                # Convert sheet to table data
                if sheet.cells:
                    table_data, span_commands, cells_border_info, cells_with_wrap = (
                        _sheet_to_table_data(sheet)
                    )

                    # Calculate column widths based on actual table dimensions
                    num_columns = len(table_data[0]) if table_data else 0
                    col_widths = _calculate_column_widths(
                        sheet, page_width, num_columns
                    )

                    # Convert cells with wrap_text to Paragraph objects for proper wrapping
                    for row, col in cells_with_wrap:
                        if row < len(table_data) and col < len(table_data[row]):
                            cell_value = table_data[row][col]
                            if cell_value:  # Only wrap non-empty cells
                                # Get cell font size (default to 8pt after our reduction)
                                cell_obj = next(
                                    (
                                        c
                                        for c in sheet.cells
                                        if c.row == row and c.column == col
                                    ),
                                    None,
                                )
                                font_size = (
                                    max(6, cell_obj.font_size - 2)
                                    if cell_obj and cell_obj.font_size
                                    else 8
                                )

                                from reportlab.lib.styles import ParagraphStyle
                                from reportlab.lib.enums import TA_LEFT

                                para_style = ParagraphStyle(
                                    "CellStyle",
                                    fontName=JAPANESE_FONT,
                                    fontSize=font_size,
                                    leading=font_size * 1.2,
                                    alignment=TA_LEFT,
                                )
                                table_data[row][col] = Paragraph(cell_value, para_style)

                    # Create table with explicit column widths
                    table = Table(table_data, colWidths=col_widths, repeatRows=0)

                    # Apply styling with span commands and selective borders
                    table_style = _create_table_style(
                        sheet, span_commands, cells_border_info
                    )
                    table.setStyle(table_style)

                    # Calculate if table needs scaling to fit on one page
                    # Wrap table to get its actual size
                    from reportlab.pdfgen import canvas

                    temp_canvas = canvas.Canvas(BytesIO())
                    table_width, table_height = table.wrapOn(
                        temp_canvas, page_width, A4[1]
                    )

                    available_height = A4[1] - 1.5 * inch  # Margins + title space

                    # If table is too large, scale it down
                    if table_height > available_height or table_width > page_width:
                        scale_w = (
                            page_width / table_width
                            if table_width > page_width
                            else 1.0
                        )
                        scale_h = (
                            available_height / table_height
                            if table_height > available_height
                            else 1.0
                        )
                        scale = min(scale_w, scale_h, 0.95)  # Max 95% to ensure it fits

                        if scale < 1.0:
                            # Recreate table with scaled column widths
                            scaled_col_widths = [w * scale for w in col_widths]
                            table = Table(
                                table_data, colWidths=scaled_col_widths, repeatRows=0
                            )
                            table.setStyle(table_style)
                            logger.info(
                                f"Scaled table by {scale:.1%} to fit on one page (was {table_height:.0f}pt, now fits in {available_height:.0f}pt)"
                            )

                    story.append(table)
                else:
                    # Empty sheet
                    empty_text = Paragraph("<i>Empty sheet</i>", styles["Normal"])
                    story.append(empty_text)

                # Add page break between sheets (except last)
                if idx < len(workbook.sheets) - 1:
                    story.append(PageBreak())

            # Build PDF
            doc.build(story)

            logger.info(f"Successfully generated PDF: {output_path.name}")

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise ConversionFailed(f"Failed to generate PDF: {str(e)}")

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
            # Create in-memory buffer
            buffer = BytesIO()

            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            # Build story (content)
            story: list[PageBreak | Spacer | Paragraph | Table] = []
            styles = getSampleStyleSheet()

            # Calculate available page width for tables
            page_width = A4[0] - 1.0 * inch  # A4 width minus margins

            for idx, sheet in enumerate(workbook.sheets):
                # Add sheet title
                title = Paragraph(
                    f"<b>{sheet.name}</b>",
                    styles["Heading1"],
                )
                story.append(title)
                story.append(Spacer(1, 0.2 * inch))

                # Convert sheet to table data
                if sheet.cells:
                    table_data, span_commands, cells_border_info, cells_with_wrap = (
                        _sheet_to_table_data(sheet)
                    )

                    # Calculate column widths based on actual table dimensions
                    num_columns = len(table_data[0]) if table_data else 0
                    col_widths = _calculate_column_widths(
                        sheet, page_width, num_columns
                    )

                    # Convert cells with wrap_text to Paragraph objects for proper wrapping
                    for row, col in cells_with_wrap:
                        if row < len(table_data) and col < len(table_data[row]):
                            cell_value = table_data[row][col]
                            if cell_value:  # Only wrap non-empty cells
                                # Get cell font size (default to 8pt after our reduction)
                                cell_obj = next(
                                    (
                                        c
                                        for c in sheet.cells
                                        if c.row == row and c.column == col
                                    ),
                                    None,
                                )
                                font_size = (
                                    max(6, cell_obj.font_size - 2)
                                    if cell_obj and cell_obj.font_size
                                    else 8
                                )

                                from reportlab.lib.styles import ParagraphStyle
                                from reportlab.lib.enums import TA_LEFT

                                para_style = ParagraphStyle(
                                    "CellStyle",
                                    fontName=JAPANESE_FONT,
                                    fontSize=font_size,
                                    leading=font_size * 1.2,
                                    alignment=TA_LEFT,
                                )
                                table_data[row][col] = Paragraph(cell_value, para_style)

                    # Create table with explicit column widths
                    table = Table(table_data, colWidths=col_widths, repeatRows=0)

                    # Apply styling with span commands and selective borders
                    table_style = _create_table_style(
                        sheet, span_commands, cells_border_info
                    )
                    table.setStyle(table_style)

                    # Calculate if table needs scaling to fit on one page
                    from reportlab.pdfgen import canvas
                    from reportlab.platypus import KeepInFrame

                    temp_canvas = canvas.Canvas(BytesIO())
                    table_width, table_height = table.wrapOn(
                        temp_canvas, page_width, A4[1]
                    )

                    available_height = A4[1] - 1.5 * inch  # Margins + title space

                    # If table is too large, wrap in KeepInFrame to force it to fit
                    if table_height > available_height:
                        scale = available_height / table_height
                        logger.info(
                            f"Table needs scaling: {table_height:.0f}pt > {available_height:.0f}pt (scale={scale:.1%})"
                        )
                        # Use KeepInFrame with mode='shrink' to scale content proportionally
                        frame_content = KeepInFrame(
                            page_width, available_height, [table], mode="shrink"
                        )
                        story.append(frame_content)
                        logger.info(f"Table wrapped in KeepInFrame to fit on one page")
                    else:
                        # Table fits naturally
                        story.append(table)
                else:
                    # Empty sheet
                    empty_text = Paragraph("<i>Empty sheet</i>", styles["Normal"])
                    story.append(empty_text)

                # Add page break between sheets (except last)
                if idx < len(workbook.sheets) - 1:
                    story.append(PageBreak())

            # Build PDF
            doc.build(story)

            # Get bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Successfully generated PDF ({len(pdf_bytes)} bytes)")

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise ConversionFailed(f"Failed to generate PDF: {str(e)}")


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


__all__ = [
    "PDFGenerator",
    "get_pdf_generator",
]
