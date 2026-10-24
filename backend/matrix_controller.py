"""
Matrix render process.

ARCHITECTURE OVERVIEW:
This module runs in a dedicated child process (started by `start_matrix_process`),
isolated from the FastAPI process so that request handling never competes with the
frame loop for the GIL. It receives render settings from the main process through a
shared-memory `SnapshotChannel` and returns the latest frame through a
`FrameChannel` for the dashboard preview.

FRAME SKIPPING:
Each mode reports a `frame_key` (see backend/modes/__init__.py). A frame is only
drawn and pushed to the panel when (config version, effective brightness, mode,
frame key) changes. The hzeller driver keeps refreshing the last swapped canvas on
its own real-time thread, so skipping a frame is invisible.

BRIGHTNESS & FADES:
hzeller applies brightness when pixels are written (SetImage), not to what is
already on the panel, so brightness changes and fades only take effect on a redraw.
Mode changes fade out over a few frames, switch, and fade back in.

HARDWARE:
When `gpio_slowdown` or `hardware_mapping` change, the RGBMatrix is deleted and
recreated. If the new settings fail, the previous ones are restored.
"""

# pylint: disable=too-many-instance-attributes,broad-exception-caught

import signal
import time
import traceback
import types

from backend.modes import (
    TICK_HZ,
    FrameContext,
    alarm,
    bad_apple,
    clock,
    draw_mode,
    life,
    qrcode_mode,
    rain,
    smiley,
    spotify_mode,
    stopwatch,
    warning,
)
from backend.modes.grid import draw_layout_grid
from backend.rendering_utils import get_framebuffer
from backend.settings import env_bool

TARGET_FPS = 120
STREAM_FPS = 15
FADE_SECONDS = 0.2

OFF_MODE = types.SimpleNamespace(
    draw=lambda fb, state, ctx: None, frame_key=lambda s, c: 0
)
MODES = {
    "off": OFF_MODE,
    "clock": clock,
    "stopwatch": stopwatch,
    "warning": warning,
    "smiley": smiley,
    "alarm": alarm,
    "rain": rain,
    "life": life,
    "badapple": bad_apple,
    "qrcode": qrcode_mode,
    "draw": draw_mode,
    "spotify": spotify_mode,
}


def load_driver():
    """Return the (RGBMatrix, RGBMatrixOptions) classes to use."""
    if env_bool("WAVEDISP_EMULATE_MATRIX", False):
        from backend import matrix_emulator as driver  # pylint: disable=import-outside-toplevel
    else:
        import rgbmatrix as driver  # pylint: disable=import-outside-toplevel,import-error
    return driver.RGBMatrix, driver.RGBMatrixOptions


class _ErrorLog:
    """Prints each distinct error at most once per `interval` seconds."""

    def __init__(self, interval=30.0):
        self.interval = interval
        self._last = {}

    def report(self, where, exc):
        key = (where, type(exc).__name__, str(exc))
        now = time.monotonic()
        if now - self._last.get(key, -self.interval) >= self.interval:
            self._last[key] = now
            print(f"[matrix] Error in {where}: {exc!r}")
            traceback.print_exc()


class Renderer:
    def __init__(self, snapshots, frames, driver=None):
        self.snapshots = snapshots
        self.frames = frames
        self.RGBMatrix, self.RGBMatrixOptions = driver or load_driver()
        self.fb = get_framebuffer()
        self.errors = _ErrorLog()

        self.state = None
        self.snapshot_seq = -1
        self._receive_snapshot()

        self.options = self.RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 1
        self.options.parallel = 1
        self.options.drop_privileges = False
        self.hw = None
        self.failed_hw = None
        self.matrix = None
        self.canvas = None
        self._apply_hardware(self.state.gpio_slowdown, self.state.hardware_mapping)

        self.current_mode = self.state.mode
        self.mode_started = time.time()
        self.level = 0.0  # fade level, 0 = dark, 1 = full brightness
        self.last_now = self.mode_started
        self.last_key = None
        self.last_tick = 0
        self.stream_pending = False
        self.last_stream = 0.0
        self.frames_drawn = 0

    # ----- setup -------------------------------------------------------------

    def _receive_snapshot(self):
        seq = self.snapshots.seq
        if seq == self.snapshot_seq:
            return False
        seq, snapshot = self.snapshots.receive()
        if snapshot is not None:
            self.state = types.SimpleNamespace(**snapshot)
            self.snapshot_seq = seq
        return True

    def _create_matrix(self, slowdown, mapping):
        self.options.gpio_slowdown = slowdown
        self.options.hardware_mapping = mapping
        self.matrix = self.RGBMatrix(options=self.options)
        self.canvas = self.matrix.CreateFrameCanvas()
        self.hw = (slowdown, mapping)

    def _apply_hardware(self, slowdown, mapping):
        target = (slowdown, mapping)
        if target in (self.hw, self.failed_hw):
            return
        previous = self.hw
        # The C++ matrix owns GPIO/DMA; it must be released before re-creating.
        self.canvas = None
        self.matrix = None
        try:
            self._create_matrix(slowdown, mapping)
            self.failed_hw = None
        except Exception as exc:
            if previous is None:
                raise
            self.errors.report("hardware re-init", exc)
            # Remember the failure so we don't retry (and re-init) every frame.
            self.failed_hw = target
            self._create_matrix(*previous)
        self.last_key = None

    # ----- frame loop --------------------------------------------------------

    def _update_fade(self, now):
        dt = max(0.0, now - self.last_now)
        self.last_now = now
        step = dt / FADE_SECONDS
        target_mode = self.state.mode
        if target_mode != self.current_mode:
            self.level = max(0.0, self.level - step)
            if self.level == 0.0:
                self.current_mode = target_mode
                self.mode_started = now
                self.last_tick = 0
                bad_apple.reset()
        else:
            self.level = min(1.0, self.level + step)
        return max(1, round(self.state.brightness * self.level))

    def step(self, now=None):
        """Render one loop iteration. Returns True when a new frame was pushed."""
        now = time.time() if now is None else now
        self._receive_snapshot()
        state = self.state
        self._apply_hardware(state.gpio_slowdown, state.hardware_mapping)

        brightness = self._update_fade(now)
        mode = MODES.get(self.current_mode, OFF_MODE)
        tick = int((now - self.mode_started) * TICK_HZ)
        ctx = FrameContext(now=now, tick=tick, steps=max(1, tick - self.last_tick))

        try:
            mode_key = mode.frame_key(state, ctx)
        except Exception as exc:
            self.errors.report(f"{self.current_mode}.frame_key", exc)
            mode_key = None
        key = (self.snapshot_seq, brightness, self.current_mode, mode_key)
        if mode_key is not None and key == self.last_key:
            return False

        self.fb.clear()
        try:
            if state.show_grid:
                draw_layout_grid(self.fb)
            mode.draw(self.fb, state, ctx)
        except Exception as exc:
            self.errors.report(f"{self.current_mode}.draw", exc)
            self.fb.clear()

        if self.matrix.brightness != brightness:
            self.matrix.brightness = brightness
        self.canvas.SetImage(self.fb.img)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

        self.last_key = key
        self.last_tick = tick
        self.stream_pending = True
        self.frames_drawn += 1
        return True

    def publish_preview(self, now):
        if self.stream_pending and now - self.last_stream >= 1.0 / STREAM_FPS:
            self.frames.write(self.fb.img.tobytes())
            self.last_stream = now
            self.stream_pending = False

    def run(self):
        frame_time = 1.0 / TARGET_FPS
        try:
            while True:
                started = time.monotonic()
                now = time.time()
                try:
                    self.step(now)
                    self.publish_preview(now)
                except Exception as exc:
                    self.errors.report("frame", exc)
                    time.sleep(0.1)
                remaining = frame_time - (time.monotonic() - started)
                if remaining > 0:
                    time.sleep(remaining)
        finally:
            if self.matrix is not None:
                self.matrix.Clear()


def _raise_exit(signum, frame):  # pylint: disable=unused-argument
    raise SystemExit(0)


def start_matrix_process(snapshots, frames):
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Let parent handle KeyboardInterrupt
    signal.signal(signal.SIGTERM, _raise_exit)  # Clear the panel on shutdown
    Renderer(snapshots, frames).run()
