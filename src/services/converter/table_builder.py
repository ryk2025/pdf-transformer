"""
Table building utilities for PDF generation.

This module handles the conversion of Excel sheets to PDF table structures.
"""

from typing import Any

from src.models.excel import ExcelSheet
from src.services.converter.formatting_utils import format_cell_value


def sheet_to_table_data(
    sheet: ExcelSheet,
) -> tuple[
    list[list[str]],
    list[tuple[str, tuple[int, int], tuple[int, int]]],
    dict[tuple[int, int], dict[str, str | None]],
    set[tuple[int, int]],
]:
    """
    Convert Excel sheet to 2D table data with span information.

    Creates a compact table containing only the used range.

    Args:
        sheet: Excel sheet

    Returns:
        Tuple of (data, span_commands, cells_border_info, cells_with_wrap) where:
        - data is 2D list of cell values as strings
        - span_commands is list of ReportLab SPAN commands for merged cells
        - cells_border_info is dict mapping (row, col) to border info
        - cells_with_wrap is set of (row, col) tuples for cells that need wrapping
    """
    if not sheet.cells:
        return [[""]], [], {}, set()

    # Determine used range
    max_content_row = max(cell.row + cell.row_span - 1 for cell in sheet.cells)
    max_content_col = max(cell.column + cell.col_span - 1 for cell in sheet.cells)

    actual_rows = max_content_row + 1
    actual_cols = max_content_col + 1

    # Initialize grid
    data = [[""] * actual_cols for _ in range(actual_rows)]

    cells_border_info: dict[tuple[int, int], dict[str, str | None]] = {}
    span_commands: list[tuple[str, tuple[int, int], tuple[int, int]]] = []
    cells_with_wrap: set[tuple[int, int]] = set()

    # Fill grid with cell values
    for cell in sheet.cells:
        if 0 <= cell.row < actual_rows and 0 <= cell.column < actual_cols:
            # Format value
            text_value = format_cell_value(cell.value, cell.number_format)

            # Handle vertical text
            if cell.text_rotation in (255, 90):
                text_value = "\n".join(list(text_value))

            data[cell.row][cell.column] = text_value

            # Track wrap text
            if cell.wrap_text:
                cells_with_wrap.add((cell.row, cell.column))

            # Handle merged cells
            if cell.row_span > 1 or cell.col_span > 1:
                end_row = min(cell.row + cell.row_span - 1, actual_rows - 1)
                end_col = min(cell.column + cell.col_span - 1, actual_cols - 1)

                span_commands.append(
                    ("SPAN", (cell.column, cell.row), (end_col, end_row))
                )

                # Apply borders to all cells in span
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
                # Single cell borders
                if cell.has_border:
                    cells_border_info[(cell.row, cell.column)] = {
                        "left": cell.border_left,
                        "right": cell.border_right,
                        "top": cell.border_top,
                        "bottom": cell.border_bottom,
                    }

    return data, span_commands, cells_border_info, cells_with_wrap


__all__ = ["sheet_to_table_data"]
