"""
PDF data models.

This module defines the internal data structures for PDF generation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PDFCell:
    """
    Represents a single cell in a PDF table.
    
    Attributes:
        value: Cell content
        font_name: Font family name
        font_size: Font size in points
        font_bold: Whether text is bold
        font_italic: Whether text is italic
        font_color: Font color (RGB tuple)
        bg_color: Background color (RGB tuple)
        alignment: Text alignment (LEFT, CENTER, RIGHT)
        has_border: Whether cell has borders
    """
    
    value: Any
    font_name: str = "Helvetica"
    font_size: float = 10.0
    font_bold: bool = False
    font_italic: bool = False
    font_color: tuple[float, float, float] = (0.0, 0.0, 0.0)
    bg_color: tuple[float, float, float] | None = None
    alignment: str = "LEFT"
    has_border: bool = True


@dataclass
class PDFTable:
    """
    Represents a table in a PDF page.
    
    Attributes:
        data: 2D list of cell values
        cells: 2D list of PDFCell objects with formatting
        col_widths: List of column widths
    """
    
    data: list[list[Any]]
    cells: list[list[PDFCell]] | None = None
    col_widths: list[float] | None = None


@dataclass
class PDFPage:
    """
    Represents a single page in a PDF document.
    
    Attributes:
        title: Page title (typically sheet name)
        table: Table data for this page
        page_size: Page size tuple (width, height) in points
    """
    
    title: str
    table: PDFTable
    page_size: tuple[float, float] = (595.0, 842.0)  # A4 size


@dataclass
class PDFDocument:
    """
    Represents a PDF document.
    
    Attributes:
        pages: List of pages in the document
        filename: Output PDF filename
    """
    
    pages: list[PDFPage]
    filename: str


__all__ = [
    "PDFCell",
    "PDFTable",
    "PDFPage",
    "PDFDocument",
]
