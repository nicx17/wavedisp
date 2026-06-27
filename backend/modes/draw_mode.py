"""
Freehand drawing mode for the LED matrix.
"""


def draw_canvas(fb, state):
    # Fill background
    bg_color = (
        state.draw_color_bg["r"],
        state.draw_color_bg["g"],
        state.draw_color_bg["b"],
    )
    fb.draw_rect(0, 0, 64, 64, bg_color)

    # Draw dictionary of pixels
    # draw_data format: {"x,y": "#RRGGBB"}
    for coord_str, hex_color in getattr(state, "draw_data", {}).items():
        try:
            x, y = map(int, coord_str.split(","))
            if 0 <= x < 64 and 0 <= y < 64:
                hex_color = hex_color.lstrip("#")
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    fb.set_pixel(x, y, (r, g, b))
        except Exception:
            pass
