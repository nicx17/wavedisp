"""
Smiley drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement


def draw_smiley(fb, frame_count, state):
    face_c = state.smiley_face_color
    cheek_c = state.smiley_cheek_color
    eye_c = state.smiley_eye_color
    tongue_c = state.smiley_tongue_color
    face = (face_c["r"], face_c["g"], face_c["b"])
    face_dim = (int(face_c["r"] * 0.6), int(face_c["g"] * 0.6), int(face_c["b"] * 0.6))
    cheek = (cheek_c["r"], cheek_c["g"], cheek_c["b"])
    eye = (eye_c["r"], eye_c["g"], eye_c["b"])
    tongue = (tongue_c["r"], tongue_c["g"], tongue_c["b"])

    fb.draw.ellipse([4, 4, 59, 59], fill=face)
    fb.draw.ellipse([6, 6, 57, 57], fill=face_dim)

    fb.draw.ellipse([13, 34, 21, 42], fill=cheek)
    fb.draw.ellipse([43, 34, 51, 42], fill=cheek)

    # Eyes
    look_x = 0
    cycle = frame_count % 100
    if 20 <= cycle < 40:
        look_x = -2
    elif 60 <= cycle < 80:
        look_x = 2

    is_blinking = (frame_count % 60) > 55
    if is_blinking:
        fb.draw.rectangle([20, 24, 27, 25], fill=(0, 0, 0))
        fb.draw.rectangle([36, 24, 43, 25], fill=(0, 0, 0))
    else:
        fb.draw.ellipse([20, 18, 28, 30], fill=eye)
        fb.draw.ellipse([36, 18, 44, 30], fill=eye)

        # Pupils
        fb.draw.rectangle([23 + look_x, 24, 24 + look_x, 25], fill=(0, 0, 0))
        fb.draw.rectangle([39 + look_x, 24, 40 + look_x, 25], fill=(0, 0, 0))

    fb.draw.pieslice([15, 28, 49, 56], start=0, end=180, fill=(0, 0, 0))
    fb.draw.ellipse([22, 43, 42, 54], fill=tongue)
    fb.draw.rectangle([15, 28, 49, 39], fill=face_dim)
