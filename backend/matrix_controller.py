"""
Core matrix controller loop and hardware memory manager.

ARCHITECTURE OVERVIEW:
This module runs in a dedicated background thread (started by `start_matrix_thread`), completely isolated from the FastAPI application thread.
It polls the global `config_state` in a thread-safe manner using `state_lock` to determine what to draw next.

MEMORY MANAGEMENT & HARDWARE:
The hzeller `rgbmatrix` library interacts directly with Raspberry Pi hardware (GPIO, DMA, PWM).
When hardware-specific settings change (like `gpio_slowdown` or `hardware_mapping`), the underlying C++ pointer (`RGBMatrix`) MUST be deleted and recreated.
This script automatically detects when these properties drift from the active settings and safely triggers `del matrix` and `del offscreen_canvas` before re-initializing to prevent segmentation faults and kernel panics.

FRAME PACING:
Instead of manual `time.sleep()`, frame pacing is naturally regulated by `SwapOnVSync()`, which blocks until the LED matrix has finished refreshing its DMA buffers. This prevents screen tearing and stuttering.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import time
import types
import threading
import queue
import io
import signal
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from backend.rendering_utils import get_framebuffer
from backend.modes.clock import draw_clock
from backend.modes.warning import draw_warning
from backend.modes.smiley import draw_smiley
from backend.modes.alarm import draw_alarm
from backend.modes.rain import draw_matrix_rain
from backend.modes.life import draw_game_of_life
from backend.modes.bad_apple import draw_bad_apple
from backend.modes.grid import draw_layout_grid
from backend.modes.qrcode_mode import draw_qrcode
from backend.modes.draw_mode import draw_canvas
from backend.modes.spotify_mode import draw_spotify

import backend.modes.bad_apple as bad_apple_mod

# --- STREAM WORKER THREAD ---
stream_queue = queue.Queue(maxsize=2)


def stream_worker(shared_state):
    while True:
        try:
            img = stream_queue.get()
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            # Write bytes to IPC manager (blocks this thread, but not matrix loop)
            shared_state["_framebuffer_bytes"] = buf.getvalue()
        except Exception:
            pass


# --- MAIN LOOP ---
def matrix_loop(shared_state, shared_lock):
    with shared_lock:
        initial_slowdown = shared_state.get("gpio_slowdown", 2)
        initial_mapping = shared_state.get("hardware_mapping", "regular")

    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = initial_mapping
    options.gpio_slowdown = initial_slowdown
    options.drop_privileges = False

    matrix = RGBMatrix(options=options)
    offscreen_canvas = matrix.CreateFrameCanvas()

    current_slowdown = initial_slowdown
    current_mapping = initial_mapping

    current_mapping = initial_mapping

    current_mode = ""
    frame_count = 0
    fb = get_framebuffer()

    # Target 120 FPS
    target_frame_time = 1.0 / 120.0

    # Cache for IPC optimization
    local_last_updated = 0.0
    state_snapshot = None

    # Start the JPEG streaming background thread
    threading.Thread(target=stream_worker, args=(shared_state,), daemon=True).start()

    while True:
        loop_start = time.time()

        # Ultra-fast IPC check (fetching a single float without full dictionary copy)
        remote_last_updated = shared_state.get("_last_updated", 1.0)

        # Only perform the expensive full dictionary IPC serialization if config changed
        if remote_last_updated != local_last_updated or state_snapshot is None:
            with shared_lock:
                state_snapshot = types.SimpleNamespace(**shared_state.copy())
            local_last_updated = remote_last_updated

        target_mode = getattr(state_snapshot, "mode", "clock")
        target_brightness = getattr(state_snapshot, "brightness", 100)
        target_slowdown = getattr(state_snapshot, "gpio_slowdown", 2)
        target_mapping = getattr(state_snapshot, "hardware_mapping", "regular")

        if current_slowdown != target_slowdown or current_mapping != target_mapping:
            del offscreen_canvas
            del matrix

            options.gpio_slowdown = target_slowdown
            options.hardware_mapping = target_mapping

            matrix = RGBMatrix(options=options)
            offscreen_canvas = matrix.CreateFrameCanvas()

            current_slowdown = target_slowdown
            current_mapping = target_mapping

        if current_mode != target_mode and current_mode != "":
            for b in range(matrix.brightness, -1, -5):
                matrix.brightness = max(0, b)
                time.sleep(0.01)
            current_mode = target_mode
            bad_apple_mod.start_time_bad_apple = 0  # Reset bad apple timer
            for b in range(0, target_brightness + 1, 5):
                matrix.brightness = min(target_brightness, b)
                time.sleep(0.01)
        elif current_mode == "":
            current_mode = target_mode

        if matrix.brightness != target_brightness:
            matrix.brightness = target_brightness

        fb.clear()

        if getattr(state_snapshot, "show_grid", False):
            draw_layout_grid(fb)

        if current_mode == "clock":
            draw_clock(fb, None, state_snapshot, time.localtime())
        elif current_mode == "warning":
            draw_warning(fb, frame_count, state_snapshot)
        elif current_mode == "smiley":
            draw_smiley(fb, frame_count, state_snapshot)
        elif current_mode == "alarm":
            draw_alarm(fb, frame_count, state_snapshot)
        elif current_mode == "rain":
            draw_matrix_rain(fb, state_snapshot)
        elif current_mode == "life":
            draw_game_of_life(fb, frame_count, state_snapshot)
        elif current_mode == "badapple":
            draw_bad_apple(fb, state_snapshot)
        elif current_mode == "qrcode":
            draw_qrcode(fb, state_snapshot)
        elif current_mode == "draw":
            draw_canvas(fb, state_snapshot)
        elif current_mode == "spotify":
            draw_spotify(fb, state_snapshot)

        # Stream Framebuffer to Web UI at ~12 FPS
        if frame_count % 10 == 0:
            if not stream_queue.full():
                # Pass a fast copy of the raw image bytes to the background thread
                stream_queue.put(fb.img.copy())

        # Push to Hardware
        offscreen_canvas.SetImage(fb.img.convert("RGB"))
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        frame_count += 1

        # Frame Limiting
        elapsed = time.time() - loop_start
        if elapsed < target_frame_time:
            time.sleep(target_frame_time - elapsed)


def start_matrix_process(shared_state, shared_lock):
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Let parent handle KeyboardInterrupt
    matrix_loop(shared_state, shared_lock)
