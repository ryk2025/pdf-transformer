"""
Cell formatting utilities for Excel to PDF conversion.

This module handles cell value formatting and styling.
"""

from datetime import datetime
from typing import Any


def format_cell_value(value: Any, number_format: str) -> str:
    """
    Format cell value according to Excel's number format.

    Args:
        value: The cell value (can be datetime, int, float, str, bool, or None)
        number_format: Excel number format code (e.g., 'd', 'yyyy-mm-dd', '0.00')

    Returns:
        Formatted string representation
    """
    if value is None or value == "":
        return ""

    # Handle datetime values
    if isinstance(value, datetime):
        format_map = {
            "d": lambda dt: str(dt.day),
            "dd": lambda dt: f"{dt.day:02d}",
            "m": lambda dt: str(dt.month),
            "mm": lambda dt: f"{dt.month:02d}",
            "mmm": lambda dt: dt.strftime("%b"),
            "mmmm": lambda dt: dt.strftime("%B"),
            "yy": lambda dt: dt.strftime("%y"),
            "yyyy": lambda dt: str(dt.year),
            "h": lambda dt: str(dt.hour % 12 or 12),
            "hh": lambda dt: f"{dt.hour % 12 or 12:02d}",
            "h:mm": lambda dt: f"{dt.hour % 12 or 12}:{dt.minute:02d}",
            "h:mm:ss": lambda dt: f"{dt.hour % 12 or 12}:{dt.minute:02d}:{dt.second:02d}",
        }

        # Check for exact match
        if number_format in format_map:
            return format_map[number_format](value)

        # Handle time formats
        if "h" in number_format.lower() or "s" in number_format.lower():
            return value.strftime("%H:%M:%S")
        elif number_format in ("General", "general", "@"):
            return value.strftime("%Y-%m-%d")
        elif "dd" in number_format.lower():
            return str(value.day)
        else:
            return value.strftime("%Y-%m-%d")

    return str(value)


def calculate_column_widths(
    sheet, num_columns: int, unit_to_points: float = 1.8
) -> list[float]:
    """
    Calculate column widths for PDF table based on Excel column widths.

    Args:
        sheet: Excel sheet with column width information
        num_columns: Number of columns in the table
        unit_to_points: Conversion factor from Excel units to points

    Returns:
        List of column widths in points
    """
    if not sheet.column_widths:
        return [64.0] * num_columns

    widths = []
    for col_idx in range(num_columns):
        width = sheet.column_widths.get(col_idx, 8.43)

        # Normalize narrow columns
        if width < 5.0:
            prev_width = (
                sheet.column_widths.get(col_idx - 1, 8.43) if col_idx > 0 else 8.43
            )
            next_width = (
                sheet.column_widths.get(col_idx + 1, 8.43)
                if col_idx < num_columns - 1
                else 8.43
            )
            width = (
                max(prev_width, next_width)
                if max(prev_width, next_width) >= 5.0
                else 8.43
            )

        widths.append(width * unit_to_points)

    return widths


def calculate_row_heights(
    sheet, num_rows: int, min_height: float = 12.0
) -> list[float]:
    """
    Calculate row heights for PDF table based on Excel row heights.

    Args:
        sheet: Excel sheet with row height information
        num_rows: Number of rows in the table
        min_height: Minimum row height in points

    Returns:
        List of row heights in points
    """
    if not sheet.row_heights:
        return [18.0] * num_rows

    heights = []
    for row_idx in range(num_rows):
        excel_height = sheet.row_heights.get(row_idx, 15.0)
        heights.append(max(excel_height, min_height))

    return heights


__all__ = [
    "format_cell_value",
    "calculate_column_widths",
    "calculate_row_heights",
]
