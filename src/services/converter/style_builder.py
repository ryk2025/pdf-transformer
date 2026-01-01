"""
Table styling utilities for PDF generation.

This module handles the creation of ReportLab TableStyle objects.
"""

from typing import Any

from reportlab.lib import colors
from reportlab.platypus import TableStyle

from src.models.excel import ExcelSheet
from src.services.converter.border_utils import BorderStyler
from src.services.converter.color_utils import hex_to_rgb_tuple


class TableStyleBuilder:
    """Builder for creating TableStyle objects from Excel sheet formatting."""

    def __init__(
        self,
        japanese_font: str = "HeiseiMin-W3",
        japanese_font_bold: str = "HeiseiKakuGo-W5",
    ):
        """
        Initialize the style builder.

        Args:
            japanese_font: Font name for regular text
            japanese_font_bold: Font name for bold text
        """
        self.japanese_font = japanese_font
        self.japanese_font_bold = japanese_font_bold

    def build_table_style(
        self,
        sheet: ExcelSheet,
        span_commands: list[tuple[str, tuple[int, int], tuple[int, int]]],
        cells_border_info: dict[tuple[int, int], dict[str, str | None]],
        scale: float = 1.0,
    ) -> TableStyle:
        """
        Create ReportLab TableStyle from Excel sheet formatting.

        Args:
            sheet: Excel sheet with formatting information
            span_commands: List of SPAN commands for merged cells
            cells_border_info: Dict mapping (row, col) to border info
            scale: Scale factor for fonts and borders

        Returns:
            TableStyle object
        """
        commands: list[Any] = [
            ("FONTNAME", (0, 0), (-1, -1), self.japanese_font),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            # Add cell padding to prevent text from touching borders
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]

        # Add span commands
        commands.extend(span_commands)

        # Apply borders
        BorderStyler.apply_cell_borders(
            commands, cells_border_info, colors.black, scale
        )

        # Apply cell-specific formatting
        self._apply_cell_formatting(commands, sheet, scale)

        return TableStyle(commands)

    def _apply_cell_formatting(
        self, commands: list[Any], sheet: ExcelSheet, scale: float
    ) -> None:
        """Apply cell-specific formatting to style commands."""
        for cell in sheet.cells:
            if 0 <= cell.row < sheet.max_row and 0 <= cell.column < sheet.max_column:
                start_pos = (cell.column, cell.row)

                # Calculate end position for merged cells
                if cell.row_span > 1 or cell.col_span > 1:
                    end_row = min(cell.row + cell.row_span - 1, sheet.max_row - 1)
                    end_col = min(cell.column + cell.col_span - 1, sheet.max_column - 1)
                    end_pos = (end_col, end_row)
                else:
                    end_pos = start_pos

                # Font styling
                if cell.font_bold:
                    commands.append(
                        ("FONTNAME", start_pos, end_pos, self.japanese_font_bold)
                    )

                # Font size: scale with table scale for visual consistency
                if cell.font_size:
                    try:
                        scaled_size = max(6, int(round(float(cell.font_size) * scale)))
                    except Exception:
                        scaled_size = max(6, int(round(10 * scale)))
                    commands.append(("FONTSIZE", start_pos, end_pos, scaled_size))

                # Font color
                if cell.font_color:
                    rgb = hex_to_rgb_tuple(cell.font_color)
                    commands.append(
                        ("TEXTCOLOR", start_pos, end_pos, colors.Color(*rgb))
                    )

                # Background color
                if cell.bg_color:
                    rgb = hex_to_rgb_tuple(cell.bg_color)
                    commands.append(
                        ("BACKGROUND", start_pos, end_pos, colors.Color(*rgb))
                    )

                # Alignment
                if cell.alignment_horizontal:
                    align_map = {"left": "LEFT", "center": "CENTER", "right": "RIGHT"}
                    alignment = align_map.get(cell.alignment_horizontal, "LEFT")
                    commands.append(("ALIGN", start_pos, end_pos, alignment))

                if cell.alignment_vertical:
                    valign_map = {
                        "top": "TOP",
                        "center": "MIDDLE",
                        "middle": "MIDDLE",
                        "bottom": "BOTTOM",
                    }
                    valignment = valign_map.get(cell.alignment_vertical, "TOP")
                    commands.append(("VALIGN", start_pos, end_pos, valignment))

                # Reduce top padding for bullet list items to avoid a blank line before content
                try:
                    val = (
                        str(cell.value)
                        if getattr(cell, "value", None) is not None
                        else None
                    )
                except Exception:
                    val = None

                if isinstance(val, str):
                    vstrip = val.strip()
                    # For multi-line list items, set small top padding and stick content to the top
                    if "\n" in val:
                        commands.append(("TOPPADDING", start_pos, end_pos, 2))
                        commands.append(("VALIGN", start_pos, end_pos, "TOP"))


__all__ = ["TableStyleBuilder"]
