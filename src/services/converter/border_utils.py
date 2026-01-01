"""
Border styling utilities for PDF generation.

This module handles border style conversions and applications.
"""

from typing import Any


class BorderStyler:
    """Helper class for managing border styles in PDF generation."""

    @staticmethod
    def get_line_params(
        border_style: str | None, scale: float = 1.0
    ) -> tuple[float, list[int] | None]:
        """
        Get line width and dash pattern for a border style.

        Args:
            border_style: Excel border style name
            scale: Scale factor to apply to line width

        Returns:
            Tuple of (line_width, dash_pattern)
        """
        if not border_style:
            return 0.5 * scale, None

        style_map = {
            "thin": (0.5, None),
            "medium": (1.0, None),
            "thick": (1.5, None),
            "dotted": (0.5, [1, 2]),  # 1pt on, 2pt off
            "dashed": (0.5, [3, 2]),  # 3pt on, 2pt off
        }

        line_width, dash_pattern = style_map.get(border_style, (0.5, None))
        return line_width * scale, dash_pattern

    @staticmethod
    def add_border_command(
        commands: list[Any],
        cell_pos: tuple[int, int],
        border_side: str,
        border_style: str | None,
        color,
        scale: float = 1.0,
    ) -> None:
        """
        Add a border command to the style commands list.

        Args:
            commands: List of style commands to append to
            cell_pos: Cell position (col, row)
            border_side: Side of border ("left", "right", "top", "bottom")
            border_style: Excel border style name
            color: Border color
            scale: Scale factor for line width
        """
        if not border_style:
            return

        line_width, dash_pattern = BorderStyler.get_line_params(border_style, scale)

        side_map = {
            "left": "LINEBEFORE",
            "right": "LINEAFTER",
            "top": "LINEABOVE",
            "bottom": "LINEBELOW",
        }

        command_type = side_map.get(border_side)
        if not command_type:
            return

        if dash_pattern:
            commands.append(
                (
                    command_type,
                    cell_pos,
                    cell_pos,
                    line_width,
                    color,
                    None,
                    dash_pattern,
                )
            )
        else:
            commands.append((command_type, cell_pos, cell_pos, line_width, color))

    @staticmethod
    def apply_cell_borders(
        commands: list[Any],
        cells_border_info: dict[tuple[int, int], dict[str, str | None]],
        color,
        scale: float = 1.0,
    ) -> None:
        """
        Apply borders to cells based on border info.

        Args:
            commands: List of style commands to append to
            cells_border_info: Dict mapping (row, col) to border info
            color: Border color
            scale: Scale factor for line width
        """
        for (row, col), border_info in cells_border_info.items():
            cell_pos = (col, row)

            for side in ["left", "right", "top", "bottom"]:
                BorderStyler.add_border_command(
                    commands, cell_pos, side, border_info.get(side), color, scale
                )


__all__ = ["BorderStyler"]
