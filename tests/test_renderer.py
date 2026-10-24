import pytest

from backend import matrix_emulator
from backend.matrix_controller import FADE_SECONDS, MODES, Renderer
from backend.scheduler import due_preset


class CountingMatrix(matrix_emulator.RGBMatrix):
    REFRESH_HZ = 1_000_000  # don't sleep in tests
    created = 0
    fail_mapping = None

    def __init__(self, options=None):
        if options is not None and options.hardware_mapping == self.fail_mapping:
            raise RuntimeError("bad mapping")
        type(self).created += 1
        super().__init__(options)


@pytest.fixture
def renderer(store, channels):
    CountingMatrix.created = 0
    CountingMatrix.fail_mapping = None
    driver = (CountingMatrix, matrix_emulator.RGBMatrixOptions)
    r = Renderer(channels[0], channels[1], driver=driver)
    return r


def settle(r, start, mode_seconds=1.0):
    """Run frames until any boot fade has finished."""
    t = start
    while t < start + mode_seconds:
        r.step(t)
        t += 1 / 120
    return t


def test_static_clock_redraws_once_per_second(renderer):
    t = settle(renderer, 1000.0)
    t = float(int(t) + 1)  # align to a second boundary
    drawn = sum(renderer.step(t + i / 120) for i in range(120))
    assert drawn == 1


def test_clock_with_ms_redraws_every_frame(store, renderer):
    store.patch({"show_ms": True})
    t = settle(renderer, 1000.0)
    assert all(renderer.step(t + i / 120) for i in range(10))


def test_config_change_forces_redraw(store, renderer):
    t = settle(renderer, 1000.3)
    assert renderer.step(t) is False
    store.patch({"color_h": {"r": 1, "g": 2, "b": 3}})
    assert renderer.step(t + 0.001) is True


@pytest.mark.parametrize("mode", sorted(MODES))
def test_every_mode_renders(store, renderer, mode):
    store.patch({"mode": mode})
    t = settle(renderer, 2000.0, mode_seconds=FADE_SECONDS * 3)
    assert renderer.current_mode == mode
    for i in range(30):
        renderer.step(t + i / 120)


def test_mode_change_fades_out_then_in(store, renderer):
    t = settle(renderer, 1000.0)
    assert renderer.matrix.brightness == 100
    store.patch({"mode": "rain"})
    levels = []
    for i in range(int(FADE_SECONDS * 2 * 120) + 10):
        renderer.step(t + i / 120)
        levels.append((renderer.current_mode, renderer.matrix.brightness))
    switch = next(i for i, (m, _) in enumerate(levels) if m == "rain")
    # Brightness drops to the minimum before the switch and recovers after.
    assert levels[switch - 1][0] == "clock"
    assert min(b for _, b in levels[:switch]) <= 5
    assert levels[-1] == ("rain", 100)


def test_draw_errors_do_not_crash(store, renderer, monkeypatch):
    def boom(*_args):
        raise RuntimeError("draw failed")

    monkeypatch.setattr(MODES["clock"], "draw", boom)
    t = settle(renderer, 1000.0)
    assert renderer.step(t + 1) is True  # frame still pushed (blank)
    assert renderer.fb.img.getbbox() is None


def test_hardware_change_recreates_matrix(store, renderer):
    t = settle(renderer, 1000.0)
    assert CountingMatrix.created == 1
    store.patch({"gpio_slowdown": 4})
    renderer.step(t)
    assert CountingMatrix.created == 2
    assert renderer.hw == (4, "regular")


def test_failed_hardware_change_restores_previous(store, renderer):
    t = settle(renderer, 1000.0)
    CountingMatrix.fail_mapping = "adafruit-hat"
    store.patch({"hardware_mapping": "adafruit-hat"})
    renderer.step(t)
    assert renderer.hw == (2, "regular")
    renderer.step(t + 0.01)  # no retry storm on every frame
    assert CountingMatrix.created == 2


def test_preview_is_throttled_and_latest(renderer, channels):
    frames = channels[1]
    t = settle(renderer, 1000.0)
    renderer.publish_preview(t)
    seq = frames.seq
    renderer.publish_preview(t + 0.001)
    assert frames.seq == seq
    renderer.stream_pending = True
    renderer.publish_preview(t + 0.1)
    assert frames.seq == seq + 1
    assert frames.read()[1] == renderer.fb.img.tobytes()


def test_scheduler_matching():
    from datetime import datetime

    monday_8 = datetime(2026, 10, 19, 8, 0)
    schedules = [
        {"time": "08:00", "days": [1], "preset_slot": "slot_1"},
        {"time": "08:00", "days": [0], "preset_slot": "slot_2", "enabled": False},
        {"time": "08:00", "days": [0, 6], "preset_slot": "slot_3"},
    ]
    assert due_preset(schedules, monday_8) == "slot_3"
    assert due_preset(schedules, datetime(2026, 10, 19, 8, 1)) is None
