"""
QR Code drawing mode for the LED matrix.
"""

import io
import time

import segno
from PIL import Image

_cached_qr_settings = None
_cached_qr_image = None


def get_qr_image(state):
    """Generates and caches the QR code image based on config state."""
    global _cached_qr_settings, _cached_qr_image

    fg = f"#{state.qr_color_fg['r']:02x}{state.qr_color_fg['g']:02x}{state.qr_color_fg['b']:02x}"
    bg = f"#{state.qr_color_bg['r']:02x}{state.qr_color_bg['g']:02x}{state.qr_color_bg['b']:02x}"

    current_settings = (
        state.qr_data,
        state.qr_error_correction,
        fg,
        bg,
        state.qr_size,
        state.qr_border,
        state.qr_use_micro,
        state.qr_size_mode,
    )

    if _cached_qr_settings == current_settings and _cached_qr_image is not None:
        return _cached_qr_image

    try:
        if state.qr_use_micro:
            try:
                qr = segno.make_micro(state.qr_data, error=state.qr_error_correction)
            except ValueError:
                # Fallback to standard QR if data is too large for Micro QR
                qr = segno.make(state.qr_data, error=state.qr_error_correction)
        else:
            qr = segno.make(state.qr_data, error=state.qr_error_correction)
        buff = io.BytesIO()
        # Always generate at scale=1 first so we know its base pixel size
        qr.save(buff, kind="png", scale=1, dark=fg, light=bg, border=state.qr_border)
        buff.seek(0)
        base_img = Image.open(buff).convert("RGB")
        base_w, base_h = base_img.size
        if state.qr_size_mode == "auto":
            # Auto-Fit: Max integer scale that fits entirely within the 64x64 matrix
            scale = max(1, min(64 // base_w, 64 // base_h))
            _cached_qr_image = base_img.resize(
                (base_w * scale, base_h * scale), Image.Resampling.NEAREST
            )
        elif state.qr_size_mode == "stretch":
            # Stretch to Fill: Exactly 64x64 (Warning: might cause unequal module sizes)
            _cached_qr_image = base_img.resize((64, 64), Image.Resampling.NEAREST)
        else:
            # Manual Size
            size = max(10, state.qr_size)
            _cached_qr_image = base_img.resize((size, size), Image.Resampling.NEAREST)

    except Exception as e:
        print(f"QR Generation Error: {e}")
        # Create a fallback error image
        _cached_qr_image = Image.new("RGB", (64, 64), bg)
        from PIL import ImageDraw

        draw = ImageDraw.Draw(_cached_qr_image)
        draw.line((0, 0, 64, 64), fill=fg, width=2)
        draw.line((0, 64, 64, 0), fill=fg, width=2)

    _cached_qr_settings = current_settings
    return _cached_qr_image


def draw_qrcode(fb, state):
    """Draws the QR code onto the framebuffer."""
    img = get_qr_image(state)
    # Fill background with QR's background color so quiet zones extend naturally
    bg_color = (state.qr_color_bg["r"], state.qr_color_bg["g"], state.qr_color_bg["b"])
    fb.draw_rect(0, 0, 64, 64, bg_color)
    if state.qr_size_mode == "auto":
        # Automatically center the image, ignoring manual offsets
        x = (64 - img.width) // 2
        y = (64 - img.height) // 2
    elif state.qr_size_mode == "stretch":
        # Force position to 0,0 for full screen, ignoring manual offsets
        x = 0
        y = 0
    else:
        # Manual mode uses user offsets
        x = state.qr_pos_x
        y = state.qr_pos_y

    # Wobulation (Jitter Anti-Aliasing)
    if getattr(state, "qr_wobble", False):
        # Shift rapidly in a 1-pixel circle (0,0) -> (1,0) -> (1,1) -> (0,1)
        cycle = int(time.time() * 40) % 4
        if cycle == 1:
            x += 1
        elif cycle == 2:
            x += 1
            y += 1
        elif cycle == 3:
            y += 1

    fb.img.paste(img, (x, y))
