"""
Warning drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import math


def draw_warning(fb, frame_count, state):
    # Sharp strobe blink (ON/OFF) instead of sine wave, but with a dim OFF state
    pulse_val = (
        1.0 if math.sin(frame_count * (state.warning_blink_speed / 10.0)) > 0 else 0.1
    )
    r = int(state.warning_color["r"] * pulse_val)
    g = int(state.warning_color["g"] * pulse_val)
    b = int(state.warning_color["b"] * pulse_val)
    color = (r, g, b)

    size = getattr(state, "warning_size", 44)
    thick = max(1, state.warning_thickness)

    cx, cy = 32, 32

    # Outer Equilateral Triangle (Centered by Bounding Box)
    H = size * math.sqrt(3) / 2
    W = size

    out_top = (cx, cy - H / 2)
    out_bl = (cx - W / 2, cy + H / 2)
    out_br = (cx + W / 2, cy + H / 2)

    fb.draw.polygon([out_top, out_bl, out_br], fill=color)

    # Inner Triangle (Inset perpendicularly by `thick`)
    H_in = H - 3 * thick
    if H_in > 0:
        W_in = H_in * 2 / math.sqrt(3)
        in_top = (cx, cy - H / 2 + 2 * thick)
        in_bl = (cx - W_in / 2, cy + H / 2 - thick)
        in_br = (cx + W_in / 2, cy + H / 2 - thick)
        fb.draw.polygon([in_top, in_bl, in_br], fill=(0, 0, 0))

        # Exclamation Point mathematically centered inside the inner triangle
        bar_w = max(1, int(W_in * 0.1))

        bar_top = in_top[1] + H_in * 0.2
        bar_bot = in_bl[1] - H_in * 0.35
        fb.draw.rectangle(
            [cx - bar_w / 2, bar_top, cx + bar_w / 2, bar_bot], fill=color
        )

        dot_top = in_bl[1] - H_in * 0.25
        dot_bot = in_bl[1] - H_in * 0.1
        fb.draw.ellipse([cx - bar_w / 2, dot_top, cx + bar_w / 2, dot_bot], fill=color)
