"""
Stand-in for hzeller's `rgbmatrix` module, for running WaveDisp without a panel.

Enabled with WAVEDISP_EMULATE_MATRIX=true. Everything renders exactly as on the
Pi; the output is visible through the dashboard's live preview (/api/stream).
"""

import time


class RGBMatrixOptions:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        self.rows = 32
        self.cols = 32
        self.chain_length = 1
        self.parallel = 1
        self.hardware_mapping = "regular"
        self.gpio_slowdown = 1
        self.drop_privileges = True
        self.brightness = 100


class FrameCanvas:
    def __init__(self):
        self.brightness = 100

    def SetImage(self, image, offset_x=0, offset_y=0, unsafe=True):
        if image.mode != "RGB":
            raise ValueError("Only RGB images are supported")

    def Clear(self):
        pass


class RGBMatrix:
    REFRESH_HZ = 200

    def __init__(self, options=None):
        self.options = options or RGBMatrixOptions()
        self._brightness = 100
        self._last_swap = 0.0

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        # Mirrors the real binding: uint8 conversion, then clamped to 1..100.
        if not 0 <= value <= 255:
            raise OverflowError("value too large to convert to uint8_t")
        self._brightness = min(100, max(1, int(value)))

    def CreateFrameCanvas(self):
        return FrameCanvas()

    def SwapOnVSync(self, canvas):
        # The real call blocks until the next panel refresh.
        wait = self._last_swap + 1.0 / self.REFRESH_HZ - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_swap = time.monotonic()
        return canvas

    def Clear(self):
        pass
