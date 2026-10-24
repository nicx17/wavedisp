"""
Drawing modes.

Every mode module exposes `draw(fb, state, ctx)` and `frame_key(state, ctx)`.
`frame_key` returns a hashable value that changes exactly when the mode's output
would change (or None for "changes every frame"). The render loop skips drawing,
and skips pushing to the panel, while the key and config version are unchanged,
which is what lets a clock idle at ~1 redraw per second instead of 120.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,bare-except,invalid-name,global-statement

from dataclasses import dataclass

# Animation speeds were originally tuned in frames of a 120 FPS loop. Animations now
# count these virtual ticks instead of real frames, so their speed no longer depends
# on how fast the Pi happens to render.
TICK_HZ = 120


@dataclass(slots=True)
class FrameContext:
    now: float  # wall-clock time.time() for this frame
    tick: int  # TICK_HZ ticks since the current mode became active
    steps: int  # ticks elapsed since this mode last drew (>= 1)
