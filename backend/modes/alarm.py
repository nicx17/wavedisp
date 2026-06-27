"""
Alarm drawing mode.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement


def draw_alarm(fb, frame_count, state):
    """Draws the alarm mode onto the framebuffer."""
    alarm_speed = max(1, 10 - getattr(state, "alarm_speed", 5))
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
        (255, 255, 255),
    ]
    color = colors[(frame_count // alarm_speed) % len(colors)]

    fb.draw_rect(0, 0, 64, 64, color)
