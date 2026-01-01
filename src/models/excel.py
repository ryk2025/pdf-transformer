"""
Excel data models.

This module defines the internal data structures for parsed Excel files.
"""

from dataclasses import dataclass
from typing import Any

from src.models import FileFormat


@dataclass
class ExcelCell:
    """
    Represents a single cell in an Excel sheet.

    Attributes:
        value: Cell value (can be str, int, float, bool, or None)
        row: Row index (0-based)
        column: Column index (0-based)
        font_name: Font family name
        font_size: Font size in points
        font_bold: Whether text is bold
        font_italic: Whether text is italic
        font_color: Font color (RGB hex string)
        bg_color: Background color (RGB hex string)
        alignment_horizontal: Horizontal alignment (left, center, right)
        alignment_vertical: Vertical alignment (top, center, bottom)
        has_border: Whether cell has borders
    """

    value: Any
    row: int
    column: int
    font_name: str = "Arial"
    font_size: float = 11.0
    font_bold: bool = False
    font_italic: bool = False
    font_color: str = "000000"
    bg_color: str | None = None
    alignment_horizontal: str = "left"
    alignment_vertical: str = "top"
    has_border: bool = False
    border_style: str = (
        "thin"  # Border style: thin, medium, thick, dotted, dashed, etc.
    )
    border_left: str | None = (
        None  # Left border style (thin, medium, thick, dotted, dashed, etc.)
    )
    border_right: str | None = None  # Right border style
    border_top: str | None = None  # Top border style
    border_bottom: str | None = None  # Bottom border style
    text_rotation: int = (
        0  # Text rotation in degrees (0, 90, 180, 270, or 255 for vertical)
    )
    wrap_text: bool = False  # Whether text should wrap within the cell
    row_span: int = 1  # Number of rows this cell spans (for merged cells)
    col_span: int = 1  # Number of columns this cell spans (for merged cells)
    number_format: str = (
        "General"  # Excel number format code (e.g., 'd', 'yyyy-mm-dd', '0.00')
    )


@dataclass
class ExcelSheet:
    """
    Represents a single sheet in an Excel workbook.

    Attributes:
        name: Sheet name
        cells: List of cells in the sheet
        max_row: Maximum row index
        max_column: Maximum column index
    """

    name: str
    cells: list[ExcelCell]
    max_row: int
    max_column: int
    column_widths: dict[int, float] | None = (
        None  # Column index -> width in Excel units
    )
    row_heights: dict[int, float] | None = None  # Row index -> height in points


@dataclass
class ExcelWorkbook:
    """
    Represents an Excel workbook.

    Attributes:
        sheets: List of sheets in the workbook
        filename: Original filename
        format: File format (xlsx or xls)
    """

    sheets: list[ExcelSheet]
    filename: str
    format: FileFormat


__all__ = [
    "ExcelCell",
    "ExcelSheet",
    "ExcelWorkbook",
]
