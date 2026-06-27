"""
Rendering utilities.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import os
import glob
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
        self.draw.rectangle([0, 0, 64, 64], fill=(0, 0, 0))

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
