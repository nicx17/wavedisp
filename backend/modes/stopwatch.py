"""
Stopwatch drawing mode for the LED matrix.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name

import time

from backend.rendering_utils import draw_time_segments, get_font


def draw_stopwatch(fb, font, state, now):
    """Draws the stopwatch onto the framebuffer."""
    ttf_font = get_font(state.clock_size, state.font_file)

    elapsed = getattr(state, "sw_elapsed", 0.0)
    if getattr(state, "sw_state", "stopped") == "running":
        start_time = getattr(state, "sw_start_time", 0.0)
        if start_time > 0:
            elapsed += time.time() - start_time

    sw_h_val = int(elapsed // 3600)
    sw_m_val = int((elapsed % 3600) // 60)
    sw_s_val = int(elapsed % 60)
    sw_ms_val = int((elapsed % 1) * 1000)

    show_h = getattr(state, "sw_show_hours", False) or sw_h_val > 0
    sw_h_str = f"{sw_h_val:02d}" if show_h else ""
    sw_m_str = f"{sw_m_val:02d}"
    sw_s_str = f"{sw_s_val:02d}"
    sw_ms_str = f"{sw_ms_val:03d}"

    sw_c_h = (state.color_sw_h["r"], state.color_sw_h["g"], state.color_sw_h["b"])
    sw_c_m = (state.color_sw_m["r"], state.color_sw_m["g"], state.color_sw_m["b"])
    sw_c_s = (state.color_sw_s["r"], state.color_sw_s["g"], state.color_sw_s["b"])
    sw_c_ms = (state.color_sw_ms["r"], state.color_sw_ms["g"], state.color_sw_ms["b"])

    sw_px = getattr(state, "sw_pos_x", 4)
    sw_py = getattr(state, "sw_pos_y", 50)

    draw_time_segments(
        fb,
        state,
        ttf_font,
        sw_h_str,
        sw_m_str,
        sw_s_str,
        sw_ms_str,
        "",
        sw_px,
        sw_py,
        sw_c_h,
        sw_c_m,
        sw_c_s,
        sw_c_ms,
        getattr(state, "sw_ms_position", "inline"),
        show_hh=bool(sw_h_str),
    )
