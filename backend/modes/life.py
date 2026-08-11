"""
Life drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import numpy as np
from PIL import Image

life_board = np.random.randint(0, 2, (64, 64), dtype=np.uint8)


def update_life():
    global life_board
    neighbors = sum(
        np.roll(np.roll(life_board, dy, axis=0), dx, axis=1)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx != 0 or dy != 0
    )
    new_board = ((life_board == 1) & ((neighbors == 2) | (neighbors == 3))) | (
        (life_board == 0) & (neighbors == 3)
    )
    changes = int(np.count_nonzero(new_board != life_board))
    life_board = new_board.astype(np.uint8)
    return changes


def draw_game_of_life(fb, frame_count, state):
    global life_board
    update_interval = max(1, int(20 - state.life_speed))
    if frame_count % update_interval == 0:
        changes = update_life()
        if changes < 3:
            life_board = np.random.randint(0, 2, (64, 64), dtype=np.uint8)

    lc = state.life_color
    mask = Image.fromarray((life_board * 255).astype(np.uint8), mode="L")
    fb.img.paste((lc["r"], lc["g"], lc["b"]), mask=mask)
