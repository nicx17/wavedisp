"""
Grid drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

from PIL import Image

GRID_COLOR = (30, 30, 30)
_grid_mask = None


def _build_mask():
    mask = Image.new("L", (64, 64), 0)
    px = mask.load()
    for i in range(64):
        for line in range(0, 64, 8):
            px[line, i] = 255
            px[i, line] = 255
    return mask


def draw_layout_grid(fb):
    # Dim grey grid overlay
    global _grid_mask
    if _grid_mask is None:
        _grid_mask = _build_mask()
    fb.img.paste(GRID_COLOR, (0, 0), _grid_mask)
