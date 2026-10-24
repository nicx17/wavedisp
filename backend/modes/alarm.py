"""
Alarm drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

COLORS = (
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (255, 255, 255),
)


def color_index(frame_count, state):
    alarm_speed = max(1, 10 - getattr(state, "alarm_speed", 5))
    return (frame_count // alarm_speed) % len(COLORS)


def frame_key(state, ctx):
    return color_index(ctx.tick, state)


def draw(fb, state, ctx):
    draw_alarm(fb, ctx.tick, state)


def draw_alarm(fb, frame_count, state):
    """Draws the alarm mode onto the framebuffer."""
    fb.draw_rect(0, 0, 64, 64, COLORS[color_index(frame_count, state)])
