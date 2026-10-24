"""
Spotify Album Art Mode
"""

from PIL import Image


def draw_spotify(fb, state):
    """Draws the album art onto the framebuffer."""
    img_bytes = getattr(state, "spotify_image_bytes", b"")
    if img_bytes:
        try:
            img = Image.frombytes("RGB", (64, 64), img_bytes)
            fb.img.paste(img, (0, 0))
        except Exception:
            pass


def frame_key(state, ctx):
    # New album art arrives as a new config version, which forces a redraw.
    return 0


def draw(fb, state, ctx):
    draw_spotify(fb, state)
