import time

import pytest

from backend.state import ConfigError


def snapshot(channels):
    return channels[0].receive()[1]


def wait_for(predicate, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


def test_patch_publishes_and_bumps_version(store, channels):
    v0 = store.version
    v1 = store.patch({"mode": "rain"})
    assert v1 > v0
    snap = snapshot(channels)
    assert snap["mode"] == "rain"
    assert snap["_version"] == v1


def test_snapshot_omits_secrets_and_unused_keys(store, channels):
    store.set_spotify_link("id", "s3cret", True)
    snap = snapshot(channels)
    for key in ("spotify_client_secret", "spotify_client_id", "presets", "schedules"):
        assert key not in snap
    assert not any(k.startswith("ui_") for k in snap)
    assert "spotify_image_bytes" in snap


def test_patch_rejects_unknown_and_invalid(store):
    with pytest.raises(ConfigError, match="Unknown"):
        store.patch({"nope": 1})
    with pytest.raises(ConfigError):
        store.patch({"brightness": 1000})
    assert store.get("brightness") == 100


def test_invalid_patch_is_atomic(store):
    with pytest.raises(ConfigError):
        store.patch({"mode": "rain", "brightness": 1000})
    assert store.get("mode") == "clock"


def test_read_only_keys(store):
    with pytest.raises(ConfigError, match="Read-only"):
        store.patch({"spotify_linked": True})
    # Echoing the current value back (full-config clients) is allowed.
    store.patch({"spotify_linked": False, "mode": "life"})
    assert store.get("mode") == "life"


def test_public_config_hides_secret(store):
    store.set_spotify_link("id", "s3cret", True)
    public = store.public_config()
    assert "spotify_client_secret" not in public
    assert public["spotify_client_id"] == "id"


def test_preset_round_trip_keeps_device_state(store):
    store.patch({"mode": "rain", "brightness": 40})
    store.save_preset("slot_1")
    store.patch({"mode": "life", "brightness": 90, "preset_names": {"slot_1": "Night"}})
    store.set_spotify_link("id", "s3cret", True)

    assert store.load_preset("slot_1") is True
    assert store.get("mode") == "rain"
    assert store.get("brightness") == 40
    # Device-level keys are not part of presets.
    assert store.get("preset_names")["slot_1"] == "Night"
    assert store.get("spotify_client_secret") == "s3cret"
    assert store.get("presets")["slot_1"]["mode"] == "rain"


def test_load_preset_with_stale_values_is_sanitized(store):
    presets = store.get("presets")
    presets["slot_2"] = {"mode": "warning", "brightness": 9000, "removed_key": 1}
    store.patch({"presets": presets})
    assert store.load_preset("slot_2") is True
    assert store.get("mode") == "warning"
    assert store.get("brightness") == 100


def test_empty_and_invalid_slots(store):
    assert store.load_preset("slot_3") is False
    with pytest.raises(ConfigError):
        store.load_preset("slot_11")
    with pytest.raises(ConfigError):
        store.save_preset("../etc")


def test_stopwatch(store):
    store.stopwatch("start")
    assert store.get("sw_state") == "running"
    time.sleep(0.02)
    store.stopwatch("stop")
    elapsed = store.get("sw_elapsed")
    assert elapsed >= 0.02
    store.stopwatch("stop")  # stopping twice must not double-count
    assert store.get("sw_elapsed") == elapsed
    store.stopwatch("reset")
    assert store.get("sw_elapsed") == 0.0
    with pytest.raises(ConfigError):
        store.stopwatch("explode")


def test_unlink_clears_album_art(store):
    store.set_spotify_image(b"\x01" * (64 * 64 * 3))
    assert store.spotify_image
    store.set_spotify_link("", "", False)
    assert store.spotify_image == b""


def test_album_art_is_not_persisted(store, saves):
    store.set_spotify_image(b"\x01" * 12)
    time.sleep(0.05)
    assert saves.saves == []


def test_saves_are_debounced_and_reflect_latest_state(store, saves):
    for b in (10, 20, 30):
        store.patch({"brightness": b})
    assert wait_for(lambda: saves.saves)
    time.sleep(0.05)
    assert len(saves.saves) == 1
    assert saves.saves[-1]["brightness"] == 30


def test_flush_writes_pending_save(store, saves):
    store.saver._delay = 60  # pylint: disable=protected-access
    store.patch({"brightness": 55})
    store.saver.flush()
    assert saves.saves[-1]["brightness"] == 55
    store.saver.flush()  # nothing pending: no extra write
    assert len(saves.saves) == 1
