"""
Rain drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import random


class RainDrop:
    def __init__(self):
        self.x = random.randint(0, 63)
        self.y = random.randint(-64, 0)
        self.length = random.randint(10, 25)
        self.speed = random.uniform(1.0, 3.0)


rain_drops = [RainDrop() for _ in range(40)]


def draw_matrix_rain(fb, state):
    rc = state.rain_color
    mult = state.rain_speed / 10.0

    for drop in rain_drops:
        drop.y += drop.speed * mult
        if drop.y - drop.length > 64:
            drop.y = random.randint(-30, 0)
            drop.x = random.randint(0, 63)
            drop.speed = random.uniform(1.0, 3.0)
            drop.length = random.randint(10, 25)

        tail_start = max(0, int(drop.y - drop.length))
        tail_end = min(64, int(drop.y))
        for y in range(tail_start, tail_end):
            intensity = int(((y - (drop.y - drop.length)) / drop.length) * 255)
            intensity = max(0, min(255, intensity))
            r = int((rc["r"] / 255.0) * intensity)
            g = int((rc["g"] / 255.0) * intensity)
            b = int((rc["b"] / 255.0) * intensity)
            fb.set_pixel(drop.x, y, (r, g, b))

        head_y = int(drop.y)
        if 0 <= head_y < 64:
            fb.set_pixel(drop.x, head_y, (255, 255, 255))
