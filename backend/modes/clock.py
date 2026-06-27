"""
Clock drawing mode for the LED matrix.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name

import time
from backend.rendering_utils import get_font


def draw_clock(fb, font, state, now):
    """Draws the clock onto the framebuffer."""
    ttf_font = get_font(state.clock_size, state.font_file)

    layout = getattr(state, "clock_layout", "single")

    def _draw_time(
        h_str, m_str, s_str, ms_str, ampm_str, pos_x, pos_y, c_h, c_m, c_s, c_ms, ms_pos
    ):
        def get_w(text, f):
            try:
                return int(fb.draw.textbbox((0, 0), text, font=f)[2])
            except Exception:
                return int(fb.draw.textlength(text, font=f))

        # Use fixed maximum widths for layout anchoring to prevent jitter
        fixed_2d_w = get_w("00", ttf_font)
        col_w = get_w(":", ttf_font)
        ms_w = get_w(f".{ms_str}", ttf_font) if ms_str else 0
        am_w = get_w(ampm_str, ttf_font) if ampm_str else 0

        y = pos_y - state.clock_size
        colon_color = (150, 150, 150)

        def draw_text_thick(pos, text, f, color):
            cx, cy = pos
            for tx in range(state.clock_thickness):
                fb.draw_text(cx + tx, cy, text, f, color)

        def draw_centered_in_box(box_x, box_w, cy, text, f, color):
            actual_w = get_w(text, f)
            cx = box_x + (box_w - actual_w) // 2
            draw_text_thick((cx, cy), text, f, color)

        show_hh = getattr(state, "show_hh", True) and bool(h_str)
        show_mm = getattr(state, "show_mm", True)
        show_ss = getattr(state, "show_ss", True)
        show_colons = getattr(state, "show_colons", True)

        if layout == "manual":
            # Manual independent positioning for each segment
            if show_hh:
                draw_centered_in_box(
                    getattr(state, "pos_hh_x", 4),
                    fixed_2d_w,
                    getattr(state, "pos_hh_y", 36) - state.clock_size,
                    h_str,
                    ttf_font,
                    c_h,
                )
            if show_mm:
                draw_centered_in_box(
                    getattr(state, "pos_mm_x", 26),
                    fixed_2d_w,
                    getattr(state, "pos_mm_y", 36) - state.clock_size,
                    m_str,
                    ttf_font,
                    c_m,
                )
            if show_ss:
                draw_centered_in_box(
                    getattr(state, "pos_ss_x", 48),
                    fixed_2d_w,
                    getattr(state, "pos_ss_y", 36) - state.clock_size,
                    s_str,
                    ttf_font,
                    c_s,
                )

        elif layout == "stacked":
            # HH:MM
            top_w = 0
            if show_hh:
                top_w += fixed_2d_w
            if show_mm:
                top_w += fixed_2d_w
            if show_hh and show_mm and show_colons:
                top_w += col_w + (state.gap_x * 2)
            elif show_hh and show_mm:
                top_w += state.gap_x

            top_x = max(0, min(pos_x, 64 - top_w))
            curr_x = top_x

            if show_hh:
                draw_centered_in_box(curr_x, fixed_2d_w, y, h_str, ttf_font, c_h)
                curr_x += fixed_2d_w + state.gap_x
                if show_mm and show_colons:
                    draw_text_thick((curr_x, y - 1), ":", ttf_font, colon_color)
                    curr_x += col_w + state.gap_x
            if show_mm:
                draw_centered_in_box(curr_x, fixed_2d_w, y, m_str, ttf_font, c_m)

            # SS.ms
            bot_w = 0
            if show_ss:
                bot_w += fixed_2d_w
            if ms_str:
                bot_w += state.gap_x + ms_w
            if am_w:
                bot_w += state.gap_x + am_w

            bot_x = max(0, min(top_x + (top_w - bot_w) // 2, 64 - bot_w))
            bot_y = y + state.clock_size + state.gap_y
            curr_x = bot_x

            if show_ss:
                draw_centered_in_box(curr_x, fixed_2d_w, bot_y, s_str, ttf_font, c_s)
                curr_x += fixed_2d_w + state.gap_x
            if ampm_str:
                draw_text_thick((curr_x, bot_y), ampm_str, ttf_font, (200, 200, 200))
                curr_x += am_w + state.gap_x
            if ms_str:
                draw_text_thick((curr_x, bot_y), f".{ms_str}", ttf_font, c_ms)

        else:
            # HH:MM:SS
            total_w = 0
            if show_hh:
                total_w += fixed_2d_w
            if show_mm:
                total_w += fixed_2d_w
            if show_ss:
                total_w += fixed_2d_w

            # Gaps and Colons
            if show_hh and show_mm:
                total_w += (col_w + (state.gap_x * 2)) if show_colons else state.gap_x
            if show_mm and show_ss:
                total_w += (col_w + (state.gap_x * 2)) if show_colons else state.gap_x

            if ampm_str:
                total_w += am_w + state.gap_x
            if ms_str and ms_pos == "inline":
                total_w += ms_w + state.gap_x

            x = max(0, min(pos_x, 64 - total_w))

            if show_hh:
                draw_centered_in_box(x, fixed_2d_w, y, h_str, ttf_font, c_h)
                x += fixed_2d_w + state.gap_x
                if show_mm:
                    if show_colons:
                        draw_text_thick((x, y - 1), ":", ttf_font, colon_color)
                        x += col_w + state.gap_x

            if show_mm:
                draw_centered_in_box(x, fixed_2d_w, y, m_str, ttf_font, c_m)
                x += fixed_2d_w + state.gap_x
                if show_ss:
                    if show_colons:
                        draw_text_thick((x, y - 1), ":", ttf_font, colon_color)
                        x += col_w + state.gap_x

            if show_ss:
                draw_centered_in_box(x, fixed_2d_w, y, s_str, ttf_font, c_s)
                x += fixed_2d_w + state.gap_x

            if ampm_str:
                draw_text_thick((x, y), ampm_str, ttf_font, (200, 200, 200))
                x += am_w + state.gap_x

            if ms_str:
                if ms_pos == "inline":
                    draw_text_thick((x, y), f".{ms_str}", ttf_font, c_ms)
                elif ms_pos == "above":
                    ms_x = max(0, min(pos_x + (total_w - ms_w) // 2, 64 - ms_w))
                    draw_text_thick(
                        (ms_x, y - state.clock_size - state.gap_y),
                        f".{ms_str}",
                        ttf_font,
                        c_ms,
                    )
                elif ms_pos == "below":
                    ms_x = max(0, min(pos_x + (total_w - ms_w) // 2, 64 - ms_w))
                    draw_text_thick(
                        (ms_x, y + state.clock_size + state.gap_y),
                        f".{ms_str}",
                        ttf_font,
                        c_ms,
                    )

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

    _draw_time(
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
    )

    # -- DRAW STOPWATCH (IF ENABLED) --
    if getattr(state, "show_stopwatch", False):
        elapsed = getattr(state, "sw_elapsed", 0.0)
        if getattr(state, "sw_state", "stopped") == "running":
            start_time = getattr(state, "sw_start_time", 0.0)
            if start_time > 0:
                elapsed += time.time() - start_time

        sw_h_val = int(elapsed // 3600)
        sw_m_val = int((elapsed % 3600) // 60)
        sw_s_val = int(elapsed % 60)
        sw_ms_val = int((elapsed % 1) * 1000)

        # Default to minutes, seconds, ms. Hours only if toggled or exceeded.
        show_h = getattr(state, "sw_show_hours", False) or sw_h_val > 0
        sw_h_str = f"{sw_h_val:02d}" if show_h else ""
        sw_m_str = f"{sw_m_val:02d}"
        sw_s_str = f"{sw_s_val:02d}"
        sw_ms_str = f"{sw_ms_val:03d}"

        sw_c_h = (state.color_sw_h["r"], state.color_sw_h["g"], state.color_sw_h["b"])
        sw_c_m = (state.color_sw_m["r"], state.color_sw_m["g"], state.color_sw_m["b"])
        sw_c_s = (state.color_sw_s["r"], state.color_sw_s["g"], state.color_sw_s["b"])
        sw_c_ms = (
            state.color_sw_ms["r"],
            state.color_sw_ms["g"],
            state.color_sw_ms["b"],
        )

        sw_px = getattr(state, "sw_pos_x", 4)
        sw_py = getattr(state, "sw_pos_y", 50)

        _draw_time(
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
        )
