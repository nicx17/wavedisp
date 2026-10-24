"""
Bad_Apple drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import os
import time

import numpy as np
from PIL import Image

bad_apple_data = None
bad_apple_missing = False
start_time_bad_apple = 0


FPS = 30


def reset():
    """Restart playback from the first frame (called on mode entry)."""
    global start_time_bad_apple
    start_time_bad_apple = 0


def _load():
    global bad_apple_data, bad_apple_missing
    if bad_apple_data is None and not bad_apple_missing:
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "bad_apple.bin"
        )
        try:
            with open(data_path, "rb") as f:
                bad_apple_data = f.read()
        except FileNotFoundError:
            print(
                "Bad Apple data file is missing. Run scripts/generate_bad_apple.py "
                "to create backend/bad_apple.bin."
            )
            bad_apple_missing = True
        except Exception as exc:
            print(f"Failed to load Bad Apple data: {exc}")
            bad_apple_missing = True
    return bad_apple_data


def frame_index(now):
    global start_time_bad_apple
    data = _load()
    total_frames = len(data) // 512 if data else 0
    if total_frames == 0:
        return None
    if start_time_bad_apple == 0:
        start_time_bad_apple = now
    return int((now - start_time_bad_apple) * FPS) % total_frames


def frame_key(state, ctx):
    idx = frame_index(ctx.now)
    return -1 if idx is None else idx  # missing data file: static blank frame


def draw(fb, state, ctx):
    draw_bad_apple(fb, state, ctx.now)


def draw_bad_apple(fb, state, now=None):
    frame_idx = frame_index(time.time() if now is None else now)
    if frame_idx is None:
        return

    offset = frame_idx * 512
    frame_bytes = bad_apple_data[offset : offset + 512]

    invert = getattr(state, "badapple_invert", False)

    frame = np.unpackbits(np.frombuffer(frame_bytes, dtype=np.uint8)).reshape(64, 64)
    if invert:
        frame = 1 - frame
    mask = Image.fromarray((frame * 255).astype(np.uint8), mode="L")
    fb.img.paste((255, 255, 255), mask=mask)
