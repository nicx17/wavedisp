"""
Rendering utilities.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import glob
import os

from PIL import Image, ImageDraw, ImageFont

from backend.settings import PROJECT_ROOT, env

# Global rendering buffers to prevent garbage collection overhead
global_img = Image.new("RGB", (64, 64), (0, 0, 0))
global_draw = ImageDraw.Draw(global_img)


class Framebuffer:
    def __init__(self):
        self.img = global_img
        self.draw = global_draw

    def clear(self):
        self.draw.rectangle([0, 0, 63, 63], fill=(0, 0, 0))

    def set_pixel(self, x, y, color):
        self.draw.point((x, y), fill=color)

    def draw_line(self, x1, y1, x2, y2, color, width=1):
        self.draw.line((x1, y1, x2, y2), fill=color, width=width)

    def draw_circle(self, x, y, r, color):
        self.draw.ellipse([x - r, y - r, x + r, y + r], outline=color)

    def draw_filled_circle(self, x, y, r, color):
        self.draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def draw_rect(self, x, y, w, h, color):
        self.draw.rectangle([x, y, x + w - 1, y + h - 1], fill=color)

    def draw_text(self, x, y, text, font, color):
        self.draw.text((x, y), text, font=font, fill=color)


def get_framebuffer():
    fb = Framebuffer()
    fb.clear()
    return fb


def get_text_width(draw, text, font):
    try:
        return int(draw.textbbox((0, 0), text, font=font)[2])
    except Exception:
        return int(draw.textlength(text, font=font))


def draw_text_thick(fb, pos, text, font, color, thickness):
    cx, cy = pos
    for tx in range(thickness):
        fb.draw_text(cx + tx, cy, text, font, color)


def draw_centered_in_box(fb, box_x, box_w, cy, text, font, color, thickness):
    actual_w = get_text_width(fb.draw, text, font)
    cx = box_x + (box_w - actual_w) // 2
    draw_text_thick(fb, (cx, cy), text, font, color, thickness)


def draw_time_segments(
    fb,
    state,
    font,
    h_str,
    m_str,
    s_str,
    ms_str,
    ampm_str,
    pos_x,
    pos_y,
    c_h,
    c_m,
    c_s,
    c_ms,
    ms_pos,
    show_hh=True,
    show_mm=True,
    show_ss=True,
    show_colons=True,
):
    """Draw shared clock/stopwatch time layout without per-frame nested closures."""
    layout = getattr(state, "clock_layout", "single")
    thickness = state.clock_thickness
    fixed_2d_w = get_text_width(fb.draw, "00", font)
    col_w = get_text_width(fb.draw, ":", font)
    ms_w = get_text_width(fb.draw, f".{ms_str}", font) if ms_str else 0
    am_w = get_text_width(fb.draw, ampm_str, font) if ampm_str else 0

    y = pos_y - state.clock_size
    colon_color = (150, 150, 150)

    if layout == "manual":
        if show_hh:
            draw_centered_in_box(
                fb,
                getattr(state, "pos_hh_x", 4),
                fixed_2d_w,
                getattr(state, "pos_hh_y", 36) - state.clock_size,
                h_str,
                font,
                c_h,
                thickness,
            )
        if show_mm:
            draw_centered_in_box(
                fb,
                getattr(state, "pos_mm_x", 26),
                fixed_2d_w,
                getattr(state, "pos_mm_y", 36) - state.clock_size,
                m_str,
                font,
                c_m,
                thickness,
            )
        if show_ss:
            draw_centered_in_box(
                fb,
                getattr(state, "pos_ss_x", 48),
                fixed_2d_w,
                getattr(state, "pos_ss_y", 36) - state.clock_size,
                s_str,
                font,
                c_s,
                thickness,
            )
        return

    if layout == "stacked":
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
            draw_centered_in_box(fb, curr_x, fixed_2d_w, y, h_str, font, c_h, thickness)
            curr_x += fixed_2d_w + state.gap_x
            if show_mm and show_colons:
                draw_text_thick(fb, (curr_x, y - 1), ":", font, colon_color, thickness)
                curr_x += col_w + state.gap_x
        if show_mm:
            draw_centered_in_box(fb, curr_x, fixed_2d_w, y, m_str, font, c_m, thickness)

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
            draw_centered_in_box(
                fb, curr_x, fixed_2d_w, bot_y, s_str, font, c_s, thickness
            )
            curr_x += fixed_2d_w + state.gap_x
        if ampm_str:
            draw_text_thick(
                fb, (curr_x, bot_y), ampm_str, font, (200, 200, 200), thickness
            )
            curr_x += am_w + state.gap_x
        if ms_str:
            draw_text_thick(fb, (curr_x, bot_y), f".{ms_str}", font, c_ms, thickness)
        return

    total_w = 0
    if show_hh:
        total_w += fixed_2d_w
    if show_mm:
        total_w += fixed_2d_w
    if show_ss:
        total_w += fixed_2d_w

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
        draw_centered_in_box(fb, x, fixed_2d_w, y, h_str, font, c_h, thickness)
        x += fixed_2d_w + state.gap_x
        if show_mm and show_colons:
            draw_text_thick(fb, (x, y - 1), ":", font, colon_color, thickness)
            x += col_w + state.gap_x

    if show_mm:
        draw_centered_in_box(fb, x, fixed_2d_w, y, m_str, font, c_m, thickness)
        x += fixed_2d_w + state.gap_x
        if show_ss and show_colons:
            draw_text_thick(fb, (x, y - 1), ":", font, colon_color, thickness)
            x += col_w + state.gap_x

    if show_ss:
        draw_centered_in_box(fb, x, fixed_2d_w, y, s_str, font, c_s, thickness)
        x += fixed_2d_w + state.gap_x

    if ampm_str:
        draw_text_thick(fb, (x, y), ampm_str, font, (200, 200, 200), thickness)
        x += am_w + state.gap_x

    if ms_str:
        if ms_pos == "inline":
            draw_text_thick(fb, (x, y), f".{ms_str}", font, c_ms, thickness)
        elif ms_pos == "above":
            ms_x = max(0, min(pos_x + (total_w - ms_w) // 2, 64 - ms_w))
            draw_text_thick(
                fb,
                (ms_x, y - state.clock_size - state.gap_y),
                f".{ms_str}",
                font,
                c_ms,
                thickness,
            )
        elif ms_pos == "below":
            ms_x = max(0, min(pos_x + (total_w - ms_w) // 2, 64 - ms_w))
            draw_text_thick(
                fb,
                (ms_x, y + state.clock_size + state.gap_y),
                f".{ms_str}",
                font,
                c_ms,
                thickness,
            )


# In-memory font cache
_font_cache = {}
_sys_fonts = None


def get_font(size, font_name="ttf"):
    """
    Cached font loader. Prevents massive disk I/O and glob searches
    during the 60fps rendering loop.
    """
    global _sys_fonts
    cache_key = f"{font_name}_{size}"

    if cache_key in _font_cache:
        return _font_cache[cache_key]

    # 1. Handle BDF fonts natively via PIL conversion
    if font_name.endswith(".bdf"):
        custom_fonts_dir = env("RGB_MATRIX_FONTS_DIR", "")
        paths_to_check = [
            PROJECT_ROOT.parent / "rpi-rgb-led-matrix" / "fonts" / font_name,
            PROJECT_ROOT / "rpi-rgb-led-matrix" / "fonts" / font_name,
        ]
        if custom_fonts_dir:
            paths_to_check.insert(0, os.path.join(custom_fonts_dir, font_name))

        bdf_path = None
        for p in paths_to_check:
            if p and os.path.exists(p):
                bdf_path = p
                break

        if bdf_path:
            pil_path = f"/tmp/{font_name}.pil"
            if not os.path.exists(pil_path):
                from PIL import BdfFontFile

                try:
                    with open(bdf_path, "rb") as fp:
                        bdf_compiler = BdfFontFile.BdfFontFile(fp)
                        bdf_compiler.save(pil_path)
                except Exception:
                    pass

            if os.path.exists(pil_path):
                try:
                    font = ImageFont.load(pil_path)
                    _font_cache[cache_key] = font
                    return font
                except Exception:
                    pass

    # 2. Try local TTF fonts folder
    if font_name != "ttf" and font_name.endswith(".ttf"):
        local_path = os.path.join(os.path.dirname(__file__), "fonts", font_name)
        if os.path.exists(local_path):
            try:
                font = ImageFont.truetype(local_path, size)
                _font_cache[cache_key] = font
                return font
            except Exception:
                pass

    # 2. Try standard system paths
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    ]

    # 3. Cache system fonts list lazily if needed
    if _sys_fonts is None:
        _sys_fonts = glob.glob("/usr/share/fonts/truetype/**/*.ttf", recursive=True)

    paths.extend(_sys_fonts)

    for p in paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, size)
                _font_cache[cache_key] = font
                return font
            except Exception:
                pass

    # Fallback
    fallback = ImageFont.load_default()
    _font_cache[cache_key] = fallback
    return fallback
