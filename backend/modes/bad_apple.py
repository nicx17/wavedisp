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


def draw_bad_apple(fb, state):
    global bad_apple_data, bad_apple_missing, start_time_bad_apple
    if bad_apple_missing:
        return

    if bad_apple_data is None:
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
            return
        except Exception as exc:
            print(f"Failed to load Bad Apple data: {exc}")
            bad_apple_missing = True
            return

    total_frames = len(bad_apple_data) // 512
    if total_frames == 0:
        return

    if start_time_bad_apple == 0:
        start_time_bad_apple = time.time()

    frame_idx = int((time.time() - start_time_bad_apple) * 30) % total_frames

    offset = frame_idx * 512
    frame_bytes = bad_apple_data[offset : offset + 512]

    invert = getattr(state, "badapple_invert", False)

    frame = np.unpackbits(np.frombuffer(frame_bytes, dtype=np.uint8)).reshape(64, 64)
    if invert:
        frame = 1 - frame
    mask = Image.fromarray((frame * 255).astype(np.uint8), mode="L")
    fb.img.paste((255, 255, 255), mask=mask)
