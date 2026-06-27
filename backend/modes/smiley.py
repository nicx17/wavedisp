"""
Smiley drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement


def draw_smiley(fb, frame_count, state):
    face_c = state.smiley_face_color
    cheek_c = state.smiley_cheek_color
    eye_c = state.smiley_eye_color
    tongue_c = state.smiley_tongue_color

    # Base face (Dim fill, bright edge)
    for y in range(4, 60):
        for x in range(4, 60):
            dist = (x - 32) ** 2 + (y - 32) ** 2
            if dist < 28**2:
                if dist > 26**2:
                    fb.set_pixel(x, y, (face_c["r"], face_c["g"], face_c["b"]))
                else:
                    fb.set_pixel(
                        x,
                        y,
                        (
                            int(face_c["r"] * 0.6),
                            int(face_c["g"] * 0.6),
                            int(face_c["b"] * 0.6),
                        ),
                    )

    # Cheeks
    for y in range(35, 42):
        for x in range(12, 22):
            if (x - 17) ** 2 + (y - 38) ** 2 < 16:
                fb.set_pixel(x, y, (cheek_c["r"], cheek_c["g"], cheek_c["b"]))
        for x in range(42, 52):
            if (x - 47) ** 2 + (y - 38) ** 2 < 16:
                fb.set_pixel(x, y, (cheek_c["r"], cheek_c["g"], cheek_c["b"]))

    # Eyes
    look_x = 0
    cycle = frame_count % 100
    if 20 <= cycle < 40:
        look_x = -2
    elif 60 <= cycle < 80:
        look_x = 2

    is_blinking = (frame_count % 60) > 55
    if is_blinking:
        for x in range(20, 28):
            fb.set_pixel(x, 24, (0, 0, 0))
            fb.set_pixel(x, 25, (0, 0, 0))
        for x in range(36, 44):
            fb.set_pixel(x, 24, (0, 0, 0))
            fb.set_pixel(x, 25, (0, 0, 0))
    else:
        for y in range(18, 30):
            for x in range(20, 28):
                if (x - 24) ** 2 + ((y - 24) * 0.8) ** 2 < 12:
                    fb.set_pixel(x, y, (eye_c["r"], eye_c["g"], eye_c["b"]))
        for y in range(18, 30):
            for x in range(36, 44):
                if (x - 40) ** 2 + ((y - 24) * 0.8) ** 2 < 12:
                    fb.set_pixel(x, y, (eye_c["r"], eye_c["g"], eye_c["b"]))

        # Pupils
        for ox in [0, 1]:
            for oy in [0, 1]:
                fb.set_pixel(23 + look_x + ox, 24 + oy, (0, 0, 0))
                fb.set_pixel(39 + look_x + ox, 24 + oy, (0, 0, 0))

    # Mouth
    for x in range(16, 49):
        dx = x - 32
        y_top = int(38 + 0.04 * (dx**2))
        y_bot = int(48 - 0.04 * (dx**2))
        if y_bot > y_top:
            for y in range(y_top, y_bot):
                if y > y_bot - 3:
                    fb.set_pixel(x, y, (tongue_c["r"], tongue_c["g"], tongue_c["b"]))
                else:
                    fb.set_pixel(x, y, (0, 0, 0))
