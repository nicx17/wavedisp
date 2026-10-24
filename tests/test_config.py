import copy

import pytest
from pydantic import ValidationError

from backend.config import (
    DEFAULT_CONFIG,
    PUBLIC_KEYS,
    STORED_KEYS,
    defaults,
    migrate_legacy,
    preset_payload,
    sanitize_config,
    validate_config,
)


def test_defaults_are_valid():
    assert validate_config(defaults()) == validate_config(DEFAULT_CONFIG)


def test_defaults_cover_every_field():
    assert set(DEFAULT_CONFIG) == STORED_KEYS


def test_secret_is_not_public():
    assert "spotify_client_secret" in STORED_KEYS
    assert "spotify_client_secret" not in PUBLIC_KEYS


def test_defaults_copy_is_deep():
    d = defaults()
    d["color_h"]["r"] = 1
    assert DEFAULT_CONFIG["color_h"]["r"] == 0


@pytest.mark.parametrize(
    "key,value",
    [
        ("brightness", 0),
        ("brightness", 500),
        ("mode", "nope"),
        ("hardware_mapping", "bogus"),
        ("font_file", "../../etc/passwd.bdf"),
        ("font_file", "/abs/path.ttf"),
        ("color_h", {"r": 256, "g": 0, "b": 0}),
        ("gpio_slowdown", -1),
        ("draw_data", {"1,1": "red"}),
        ("draw_data", {"../x": "#ffffff"}),
        ("schedules", [{"time": "25:00", "days": [0], "preset_slot": "slot_1"}]),
        ("schedules", [{"time": "08:00", "days": [7], "preset_slot": "slot_1"}]),
        ("presets", {"slot_99": {}}),
    ],
)
def test_validation_rejects(key, value):
    with pytest.raises(ValidationError):
        validate_config(dict(defaults(), **{key: value}))


@pytest.mark.parametrize(
    "font", ["7x14B.bdf", "10x20.bdf", "ttf", "PressStart2P.ttf", "RubikMonoOne.ttf"]
)
def test_dashboard_fonts_are_accepted(font):
    assert validate_config(dict(defaults(), font_file=font))["font_file"] == font


def test_schedule_extra_fields_survive():
    sched = {
        "id": "1786307017182",
        "preset_slot": "slot_3",
        "enabled": True,
        "time": "23:00",
        "days": [0, 1, 2, 3, 4, 5, 6],
    }
    assert validate_config(dict(defaults(), schedules=[sched]))["schedules"] == [sched]


def test_sanitize_resets_only_bad_keys():
    data = dict(defaults(), brightness=999, mode="rain", qr_data="hello")
    clean = sanitize_config(data)
    assert clean["brightness"] == DEFAULT_CONFIG["brightness"]
    assert clean["mode"] == "rain"
    assert clean["qr_data"] == "hello"


def test_sanitize_drops_unknown_keys():
    clean = sanitize_config({"saved": True, "mode": "life"})
    assert "saved" not in clean
    assert clean["mode"] == "life"


def test_sanitize_prefers_fallback_then_default():
    fallback = dict(defaults(), brightness=20)
    assert sanitize_config({"brightness": -5}, fallback=fallback)["brightness"] == 20
    bad_fallback = dict(defaults(), brightness=-1)
    assert sanitize_config({}, fallback=bad_fallback)["brightness"] == 100


def test_legacy_stopwatch_overlay_migrates():
    data = {
        "mode": "clock",
        "show_stopwatch": True,
        "presets": {"slot_1": {"mode": "clock", "show_stopwatch": True}},
    }
    migrate_legacy(data)
    assert data["mode"] == "stopwatch"
    assert data["presets"]["slot_1"]["mode"] == "stopwatch"


def test_preset_payload_excludes_device_state():
    state = dict(defaults(), spotify_client_secret="s3cret", spotify_linked=True)
    payload = preset_payload(state)
    for key in ("presets", "schedules", "spotify_client_secret", "spotify_linked"):
        assert key not in payload
    assert payload["mode"] == "clock"


def test_preset_payload_is_a_copy():
    state = defaults()
    payload = preset_payload(state)
    payload["color_h"]["r"] = 9
    assert state["color_h"]["r"] == 0


def test_validation_does_not_alias_input():
    data = copy.deepcopy(DEFAULT_CONFIG)
    out = validate_config(data)
    out["color_h"]["r"] = 42
    assert data["color_h"]["r"] == 0
