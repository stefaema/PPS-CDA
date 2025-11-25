#src/utils/svg_generator.py

def generate_rect_svg(x: int, y: int, width: int, height: int, stroke: str = "white", stroke_width: int = 2, fill: str = "none") -> str:
    """Generates an SVG rectangle element as a string."""
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" stroke="{stroke}" stroke-width="{stroke_width}" fill="{fill}" vector-effect="non-scaling-stroke" />'

def generate_line_svg(x1: int, y1: int, x2: int, y2: int, stroke: str = "white", stroke_width: int = 2, dotted: bool = False) -> str:
    """Generates an SVG line element as a string."""
    dasharray = " stroke-dasharray='10,5'" if dotted else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}" {dasharray} vector-effect="non-scaling-stroke" />'

def get_color(color: str, transparency: float) -> str:
    """
    Converts a hex color code to an rgba() string with specified transparency.

    Args:
        color: The hex color string (e.g., '#21ba45').
        transparency: The alpha value (e.g., 0.2).

    Returns:
        The CSS rgba() string (e.g., 'rgba(33, 186, 69, 0.2)').
    """
    # 1. Strip the '#' if present
    hex_color = color.lstrip('#')

    # 2. Convert the 6 hex digits into R, G, B decimal values
    # Each slice is 2 characters (0-2 for R, 2-4 for G, 4-6 for B)
    # The int(..., 16) function handles the hex to decimal conversion
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # 3. Format the final rgba() string
    return f"rgba({r}, {g}, {b}, {transparency})"
