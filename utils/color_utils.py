from typing import Dict, Tuple
import colorsys

def generate_color_palette(num_sources: int) -> Dict[str, str]:
    """Generate distinct colors for different calendar sources."""
    colors = {}
    for i in range(num_sources):
        hue = i / num_sources
        rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.95)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
        colors[f'source_{i}'] = hex_color
    return colors

def get_contrast_color(hex_color: str) -> str:
    """Calculate contrasting text color (black/white) for given background."""
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Calculate luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    return '#000000' if luminance > 0.5 else '#ffffff'