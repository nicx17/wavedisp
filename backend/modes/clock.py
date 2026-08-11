"""
Clock drawing mode for the LED matrix.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name

import time

from backend.rendering_utils import draw_time_segments, get_font


def draw_clock(fb, font, state, now):
    """Draws the clock onto the framebuffer."""
    ttf_font = get_font(state.clock_size, state.font_file)

    # -- DRAW NORMAL CLOCK --
    h_str = time.strftime("%I" if state.format_12h else "%H", now).lstrip("0") or "0"
    m_str = time.strftime("%M", now)
    s_str = time.strftime("%S", now)
    ms_str = f"{(time.time() % 1) * 1000:03.0f}" if state.show_ms else ""
    ampm_str = time.strftime("%p", now) if state.format_12h else ""

    c_h = (state.color_h["r"], state.color_h["g"], state.color_h["b"])
    c_m = (state.color_m["r"], state.color_m["g"], state.color_m["b"])
    c_s = (state.color_s["r"], state.color_s["g"], state.color_s["b"])
    cms_dict = getattr(state, "color_ms", state.color_s)
    c_ms = (cms_dict["r"], cms_dict["g"], cms_dict["b"])

    draw_time_segments(
        fb,
        state,
        ttf_font,
        h_str,
        m_str,
        s_str,
        ms_str,
        ampm_str,
        state.pos_x,
        state.pos_y,
        c_h,
        c_m,
        c_s,
        c_ms,
        getattr(state, "ms_position", "inline"),
        show_hh=getattr(state, "show_hh", True) and bool(h_str),
        show_mm=getattr(state, "show_mm", True),
        show_ss=getattr(state, "show_ss", True),
        show_colons=getattr(state, "show_colons", True),
    )
