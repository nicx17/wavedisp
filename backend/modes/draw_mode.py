"""
Freehand drawing mode for the LED matrix.
"""

_cached_draw_data = None
_cached_pixels = []


def parse_draw_pixels(draw_data):
    pixels = []
    for coord_str, hex_color in draw_data.items():
        try:
            x, y = map(int, coord_str.split(","))
            if 0 <= x < 64 and 0 <= y < 64:
                hex_color = hex_color.lstrip("#")
                if len(hex_color) == 6:
                    pixels.append(
                        (
                            x,
                            y,
                            (
                                int(hex_color[0:2], 16),
                                int(hex_color[2:4], 16),
                                int(hex_color[4:6], 16),
                            ),
                        )
                    )
        except Exception:
            pass
    return pixels


def draw_canvas(fb, state):
    global _cached_draw_data, _cached_pixels
    # Fill background
    bg_color = (
        state.draw_color_bg["r"],
        state.draw_color_bg["g"],
        state.draw_color_bg["b"],
    )
    fb.draw_rect(0, 0, 64, 64, bg_color)

    # Draw dictionary of pixels
    # draw_data format: {"x,y": "#RRGGBB"}
    draw_data = getattr(state, "draw_data", {})
    if draw_data is not _cached_draw_data:
        _cached_draw_data = draw_data
        _cached_pixels = parse_draw_pixels(draw_data)

    for x, y, color in _cached_pixels:
        fb.set_pixel(x, y, color)
