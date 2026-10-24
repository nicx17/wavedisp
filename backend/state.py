"""
Authoritative runtime state for WaveDisp.

ARCHITECTURE OVERVIEW:
`StateStore` owns the config dict in the main process. The API, the scheduler and
the Spotify poller all mutate it through the methods below, which:

1. validate the result against `StoredConfig` (invalid writes are rejected whole),
2. bump `version` so dashboards can detect changes made elsewhere,
3. publish a render snapshot to the matrix process through shared memory,
4. request a debounced save to disk.

The store's lock is never held during disk I/O or while waiting on the render
process, so a slow SD card cannot stall API requests or the display.
"""

import copy
import threading
import time

from backend.config import (
    NON_PRESET_KEYS,
    PRESET_SLOTS,
    PUBLIC_KEYS,
    READ_ONLY_KEYS,
    DebouncedSaver,
    defaults,
    preset_payload,
    sanitize_config,
    save_config,
    validate_config,
)

# Keys the renderer never reads; leaving them out keeps snapshots small.
RENDER_EXCLUDED_KEYS = NON_PRESET_KEYS | {k for k in PUBLIC_KEYS if k.startswith("ui_")}


class ConfigError(ValueError):
    """A write was rejected; the message is safe to show to API clients."""


class StateStore:
    def __init__(self, initial, channel=None, save_delay=0.5, save_fn=save_config):
        self._lock = threading.RLock()
        self._state = initial
        self._version = 1
        self._spotify_image = b""
        self._channel = channel
        self.saver = DebouncedSaver(self.stored_snapshot, save_delay, save_fn)
        self._publish()

    # ----- reads -------------------------------------------------------------

    @property
    def version(self):
        return self._version

    def get(self, key, default=None):
        with self._lock:
            return copy.deepcopy(self._state.get(key, default))

    def stored_snapshot(self):
        """Full config including private keys, for persistence."""
        with self._lock:
            return copy.deepcopy(self._state)

    def public_config(self):
        """Config as exposed by GET /api/config (no secrets)."""
        with self._lock:
            return copy.deepcopy({k: self._state[k] for k in PUBLIC_KEYS})

    @property
    def spotify_image(self):
        return self._spotify_image

    # ----- writes ------------------------------------------------------------

    def patch(self, changes):
        """Apply a partial public config update. Raises ConfigError."""
        unknown = set(changes) - PUBLIC_KEYS
        if unknown:
            raise ConfigError(f"Unknown config keys: {', '.join(sorted(unknown))}")
        read_only = set(changes) & READ_ONLY_KEYS
        with self._lock:
            # Echoing back an unchanged read-only value (full-config clients) is fine.
            if any(changes[k] != self._state[k] for k in read_only):
                raise ConfigError(
                    f"Read-only config keys: {', '.join(sorted(read_only))}"
                )
            merged = dict(self._state)
            merged.update(changes)
            self._commit(self._validate(merged))
            return self._version

    def replace(self, public_config):
        """Replace the whole public config (POST /api/config)."""
        changes = {k: v for k, v in public_config.items() if k not in READ_ONLY_KEYS}
        return self.patch(changes)

    def stopwatch(self, action):
        with self._lock:
            state = dict(self._state)
            now = time.time()
            if action == "start":
                if state["sw_state"] != "running":
                    state["sw_start_time"] = now
                    state["sw_state"] = "running"
            elif action == "stop":
                if state["sw_state"] == "running":
                    state["sw_elapsed"] += max(0.0, now - state["sw_start_time"])
                    state["sw_state"] = "stopped"
            elif action == "reset":
                state["sw_elapsed"] = 0.0
                state["sw_start_time"] = 0.0
                state["sw_state"] = "stopped"
            else:
                raise ConfigError(f"Unknown stopwatch action: {action}")
            self._commit(self._validate(state))
            return self._version

    def save_preset(self, slot):
        self._check_slot(slot)
        with self._lock:
            presets = dict(self._state["presets"])
            presets[slot] = preset_payload(self._state)
            state = dict(self._state)
            state["presets"] = presets
            self._commit(state)
            return self._version

    def load_preset(self, slot):
        """Apply a stored preset. Returns False when the slot is empty."""
        self._check_slot(slot)
        with self._lock:
            preset = self._state["presets"].get(slot) or {}
            if not preset:
                return False
            # Settings missing from older presets fall back to defaults, and values
            # that no longer validate are reset instead of rejecting the preset.
            candidate = defaults()
            candidate.update(preset_payload(preset))
            candidate.update({k: self._state[k] for k in NON_PRESET_KEYS})
            self._commit(sanitize_config(candidate))
            return True

    def set_spotify_link(self, client_id, client_secret, linked):
        with self._lock:
            state = dict(self._state)
            state["spotify_client_id"] = client_id
            state["spotify_client_secret"] = client_secret
            state["spotify_linked"] = linked
            if not linked:
                self._spotify_image = b""
            self._commit(self._validate(state))
            return self._version

    def set_spotify_image(self, image_bytes):
        """Album art is display-only: published, but never written to disk."""
        with self._lock:
            self._spotify_image = image_bytes
            self._version += 1
            self._publish()

    # ----- internals ---------------------------------------------------------

    @staticmethod
    def _check_slot(slot):
        if slot not in PRESET_SLOTS:
            raise ConfigError(f"Invalid preset slot: {slot}")

    @staticmethod
    def _validate(state):
        try:
            return validate_config(state)
        except ValueError as exc:  # pydantic.ValidationError subclasses ValueError
            raise ConfigError(str(exc)) from exc

    def _commit(self, new_state):
        self._state = new_state
        self._version += 1
        self._publish()
        self.saver.request()

    def _publish(self):
        if self._channel is None:
            return
        snapshot = {
            k: v for k, v in self._state.items() if k not in RENDER_EXCLUDED_KEYS
        }
        snapshot["spotify_image_bytes"] = self._spotify_image
        snapshot["_version"] = self._version
        self._channel.publish(snapshot)
