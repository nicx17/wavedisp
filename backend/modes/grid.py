"""
Grid drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement


def draw_layout_grid(fb):
    # Dim grey grid overlay
    for x in range(0, 64, 8):
        for y in range(64):
            fb.set_pixel(x, y, (30, 30, 30))
    for y in range(0, 64, 8):
        for x in range(64):
            fb.set_pixel(x, y, (30, 30, 30))
