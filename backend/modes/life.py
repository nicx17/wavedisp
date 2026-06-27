"""
Life drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

import random

life_board = [[random.choice([0, 1]) for _ in range(64)] for _ in range(64)]


def update_life():
    global life_board
    new_board = [[0 for _ in range(64)] for _ in range(64)]
    changes = 0
    for y in range(64):
        for x in range(64):
            alive = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx = (x + dx) % 64
                    ny = (y + dy) % 64
                    alive += life_board[ny][nx]

            if life_board[y][x]:
                if alive in (2, 3):
                    new_board[y][x] = 1
                else:
                    changes += 1
            else:
                if alive == 3:
                    new_board[y][x] = 1
                    changes += 1
    life_board = new_board
    return changes


def draw_game_of_life(fb, frame_count, state):
    global life_board
    update_interval = max(1, int(20 - state.life_speed))
    if frame_count % update_interval == 0:
        changes = update_life()
        if changes < 3:
            life_board = [[random.choice([0, 1]) for _ in range(64)] for _ in range(64)]

    lc = state.life_color
    for y in range(64):
        for x in range(64):
            if life_board[y][x]:
                fb.set_pixel(x, y, (lc["r"], lc["g"], lc["b"]))
