"""
Color utilities for Excel to PDF conversion.

This module provides color conversion and manipulation functions.
"""

# Theme colors (standard Office color theme)
THEME_COLORS = {
    0: "FFFFFF",  # background 1 (white)
    1: "000000",  # text 1 (black)
    2: "E7E6E6",  # background 2 (light gray)
    3: "44546A",  # text 2 (dark blue gray)
    4: "5B9BD5",  # accent 1 (blue)
    5: "ED7D31",  # accent 2 (orange)
    6: "A5A5A5",  # accent 3 (gray)
    7: "FFC000",  # accent 4 (gold)
    8: "4472C4",  # accent 5 (blue)
    9: "70AD47",  # accent 6 (green)
}


def hex_to_rgb(hex_color: str | None) -> str:
    """
    Convert hex color to RGB hex string.

    Args:
        hex_color: Hex color string (may include alpha channel)

    Returns:
        6-character RGB hex string
    """
    if not hex_color:
        return "000000"

    # Remove alpha channel if present (ARGB -> RGB)
    if len(hex_color) == 8:
        hex_color = hex_color[2:]

    # Ensure 6 characters
    if len(hex_color) != 6:
        return "000000"

    return hex_color


def apply_tint(rgb_hex: str, tint: float) -> str:
    """
    Apply tint to RGB color following Excel's tint algorithm.

    Args:
        rgb_hex: RGB hex string (6 characters)
        tint: Tint value (-1.0 to 1.0)

    Returns:
        Tinted RGB hex string
    """
    rgb = [int(rgb_hex[i : i + 2], 16) for i in (0, 2, 4)]

    if tint < 0:
        # For negative tint, darken: RGB' = RGB * (1 + tint)
        rgb = [int(c * (1 + tint)) for c in rgb]
    else:
        # For positive tint, lighten: RGB' = RGB + (255 - RGB) * tint
        rgb = [int(c + (255 - c) * tint) for c in rgb]

    return "".join([f"{c:02X}" for c in rgb])


def get_color_from_color_object(color_obj) -> str | None:
    """
    Extract RGB color from openpyxl Color object.

    Handles RGB, theme, and indexed colors.

    Args:
        color_obj: openpyxl Color object

    Returns:
        RGB hex string or None if color cannot be determined
    """
    if not color_obj:
        return None

    # Try direct RGB first
    if hasattr(color_obj, "rgb") and color_obj.rgb:
        rgb_val = color_obj.rgb
        if isinstance(rgb_val, str) and len(rgb_val) >= 6:
            return hex_to_rgb(rgb_val)

    # Try theme color
    if hasattr(color_obj, "theme") and color_obj.theme is not None:
        theme_color = THEME_COLORS.get(color_obj.theme, "FFFFFF")
        tint = color_obj.tint if hasattr(color_obj, "tint") and color_obj.tint else 0
        if tint != 0:
            return apply_tint(theme_color, tint)
        return theme_color

    # Indexed colors not currently supported
    return None


def hex_to_rgb_tuple(hex_color: str) -> tuple[float, float, float]:
    """
    Convert hex color to RGB tuple (0-1 range for ReportLab).

    Args:
        hex_color: Hex color string (6 characters)

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


__all__ = [
    "THEME_COLORS",
    "hex_to_rgb",
    "apply_tint",
    "get_color_from_color_object",
    "hex_to_rgb_tuple",
]
