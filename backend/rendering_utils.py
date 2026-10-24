"""
Rendering utilities.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import glob
import os

from PIL import Image, ImageDraw, ImageFont

from backend.settings import PROJECT_ROOT, env, resolve_path

WIDTH = HEIGHT = 64

# Global rendering buffers to prevent garbage collection overhead
global_img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
global_draw = ImageDraw.Draw(global_img)


class Framebuffer:
    def __init__(self):
        self.img = global_img
        self.draw = global_draw
        # Direct pixel access is ~10x faster than ImageDraw.point per pixel.
        self.pixels = global_img.load()

    def clear(self):
        self.img.paste((0, 0, 0), (0, 0, WIDTH, HEIGHT))

    def set_pixel(self, x, y, color):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.pixels[x, y] = color

    def draw_line(self, x1, y1, x2, y2, color, width=1):
        self.draw.line((x1, y1, x2, y2), fill=color, width=width)

    def draw_circle(self, x, y, r, color):
        self.draw.ellipse([x - r, y - r, x + r, y + r], outline=color)

    def draw_filled_circle(self, x, y, r, color):
        self.draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def draw_rect(self, x, y, w, h, color):
        self.draw.rectangle([x, y, x + w - 1, y + h - 1], fill=color)

    def draw_text(self, x, y, text, font, color):
        stamp = _text_stamp(font, text)
        if stamp is not None:
            mask, left, top = stamp
            self.img.paste(color, (x + left, y + top), mask)


def get_framebuffer():
    fb = Framebuffer()
    fb.clear()
    return fb


# Text is re-rendered with identical arguments every frame (the same digits, in the
# same font), so both measurements and glyph masks are memoised. Font objects are
# cached forever by get_font, which keeps the keys stable.
_width_cache = {}
_stamp_cache = {}
_TEXT_CACHE_LIMIT = 4096


def get_text_width(draw, text, font):
    key = (font, text)
    width = _width_cache.get(key)
    if width is None:
        try:
            width = int(draw.textbbox((0, 0), text, font=font)[2])
        except Exception:
            width = int(draw.textlength(text, font=font))
        if len(_width_cache) >= _TEXT_CACHE_LIMIT:
            _width_cache.clear()
        _width_cache[key] = width
    return width


def _text_stamp(font, text):
    """Return (mask, dx, dy) for `text`, or None when it has no visible ink."""
    key = (font, text)
    if key in _stamp_cache:
        return _stamp_cache[key]

    left, top, right, bottom = global_draw.textbbox((0, 0), text, font=font)
    stamp = None
    if right > left and bottom > top:
        mask = Image.new("L", (right - left, bottom - top), 0)
        ImageDraw.Draw(mask).text((-left, -top), text, font=font, fill=255)
        stamp = (mask, left, top)

    if len(_stamp_cache) >= _TEXT_CACHE_LIMIT:
        _stamp_cache.clear()
    _stamp_cache[key] = stamp
    return stamp


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

# Compiled BDF fonts (.pil/.pbm) live in a private directory rather than /tmp, where
# a predictable path written by a root process is a symlink-attack target.
FONT_CACHE_DIR = resolve_path(env("WAVEDISP_FONT_CACHE_DIR", "backend/.font_cache"))


def _compiled_bdf_path(font_name, bdf_path):
    pil_path = FONT_CACHE_DIR / f"{font_name}.pil"
    if not pil_path.exists():
        from PIL import BdfFontFile

        try:
            FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(bdf_path, "rb") as fp:
                BdfFontFile.BdfFontFile(fp).save(str(pil_path))
        except Exception as exc:
            print(f"Failed to compile BDF font {font_name}: {exc}")
    return pil_path


def get_font(size, font_name="ttf"):
    """
    Cached font loader. Prevents massive disk I/O and glob searches
    during the rendering loop.
    """
    global _sys_fonts
    # Config validation already restricts font names; basename is defence in depth.
    font_name = os.path.basename(font_name)
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
            pil_path = _compiled_bdf_path(font_name, bdf_path)
            if pil_path.exists():
                try:
                    font = ImageFont.load(str(pil_path))
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

    # 3. Try standard system paths
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    ]

    # Cache system fonts list lazily if needed
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
