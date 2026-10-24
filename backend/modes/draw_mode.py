"""
Freehand drawing mode for the LED matrix.
"""

from PIL import Image

_cached_key = None
_cached_layer = None


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


def render_layer(draw_data, bg_color):
    """Render background + pixels into a standalone 64x64 image."""
    layer = Image.new("RGB", (64, 64), bg_color)
    px = layer.load()
    for x, y, color in parse_draw_pixels(draw_data):
        px[x, y] = color
    return layer


def frame_key(state, ctx):
    return 0


def draw_canvas(fb, state):
    global _cached_key, _cached_layer
    # draw_data format: {"x,y": "#RRGGBB"}
    draw_data = getattr(state, "draw_data", {})
    bg_color = (
        state.draw_color_bg["r"],
        state.draw_color_bg["g"],
        state.draw_color_bg["b"],
    )
    # Snapshots are replaced wholesale on every config change, so identity of the
    # dict is a reliable (and O(1)) change check.
    key = (id(draw_data), bg_color)
    if key != _cached_key or _cached_layer is None:
        _cached_key = key
        _cached_layer = render_layer(draw_data, bg_color)

    # The layer is opaque, so it replaces anything drawn underneath (e.g. the grid),
    # matching the previous behaviour of filling the background first.
    fb.img.paste(_cached_layer, (0, 0))


def draw(fb, state, ctx):
    draw_canvas(fb, state)
