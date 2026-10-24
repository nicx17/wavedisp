"""
Configuration schema, defaults and persistence for WaveDisp.

ARCHITECTURE OVERVIEW:
`PublicConfig` is the schema the API exposes and accepts. `StoredConfig` adds the
private keys that are persisted but never returned to clients (the Spotify client
secret). Every config that enters the system (config.json at boot, presets when
they are loaded, API writes) passes through these models, so the render process can
trust the values it receives.

`sanitize_config` is the lenient path used for data already on disk: invalid keys
fall back to their defaults instead of failing, so a stale or hand-edited
config.json can never stop the service from booting.
"""

import copy
import json
import os
import threading
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from backend.settings import env, resolve_path

CONFIG_FILE = resolve_path(env("WAVEDISP_CONFIG_FILE", "backend/config.json"))

MODES = (
    "off",
    "clock",
    "stopwatch",
    "warning",
    "smiley",
    "alarm",
    "rain",
    "life",
    "badapple",
    "qrcode",
    "draw",
    "spotify",
)
PRESET_SLOTS = tuple(f"slot_{i}" for i in range(1, 11))

Mode = Literal[MODES]
Slot = Literal[PRESET_SLOTS]
Position = Annotated[int, Field(ge=-64, le=128)]
Gap = Annotated[int, Field(ge=-16, le=32)]
Channel = Annotated[int, Field(ge=0, le=255)]
CssColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{3,8}$")]
# Bare file names only: font_file ends up in filesystem paths.
FontFile = Annotated[
    str, StringConstraints(pattern=r"^(ttf|[A-Za-z0-9_-]+\.(bdf|ttf))$", max_length=64)
]
DrawCoord = Annotated[str, StringConstraints(pattern=r"^\d{1,2},\d{1,2}$")]
HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]
MsPosition = Literal["inline", "above", "below"]


class ColorModel(BaseModel):
    r: Channel
    g: Channel
    b: Channel


class ScheduleModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Annotated[str, Field(max_length=64)] = ""
    time: Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
    days: Annotated[list[Annotated[int, Field(ge=0, le=6)]], Field(max_length=7)]
    preset_slot: Slot
    enabled: bool = True


class PublicConfig(BaseModel):
    mode: Mode
    brightness: Annotated[int, Field(ge=1, le=100)]
    show_grid: bool
    gpio_slowdown: Annotated[int, Field(ge=0, le=5)]
    hardware_mapping: Literal[
        "regular", "adafruit-hat", "adafruit-hat-pwm", "regular-pi1"
    ]

    # Clock
    color_h: ColorModel
    color_m: ColorModel
    color_s: ColorModel
    color_ms: ColorModel
    pos_x: Position
    pos_y: Position
    show_hh: bool
    show_mm: bool
    show_ss: bool
    show_colons: bool
    pos_hh_x: Position
    pos_hh_y: Position
    pos_mm_x: Position
    pos_mm_y: Position
    pos_ss_x: Position
    pos_ss_y: Position
    font_file: FontFile
    clock_size: Annotated[int, Field(ge=4, le=64)]
    clock_thickness: Annotated[int, Field(ge=1, le=8)]
    format_12h: bool
    show_ms: bool
    clock_layout: Literal["single", "stacked", "manual"]
    ms_position: MsPosition
    gap_x: Gap
    gap_y: Gap

    # Stopwatch
    show_stopwatch: bool
    sw_pos_x: Position
    sw_pos_y: Position
    sw_show_hours: bool
    sw_ms_position: MsPosition
    color_sw_h: ColorModel
    color_sw_m: ColorModel
    color_sw_s: ColorModel
    color_sw_ms: ColorModel
    sw_state: Literal["running", "stopped"]
    sw_start_time: Annotated[float, Field(ge=0)]
    sw_elapsed: Annotated[float, Field(ge=0)]

    # Warning
    warning_color: ColorModel
    warning_thickness: Annotated[int, Field(ge=1, le=20)]
    warning_blink_speed: Annotated[int, Field(ge=0, le=100)]
    warning_size: Annotated[int, Field(ge=4, le=64)]

    # Smiley
    smiley_face_color: ColorModel
    smiley_cheek_color: ColorModel
    smiley_eye_color: ColorModel
    smiley_tongue_color: ColorModel

    # Rain
    rain_color: ColorModel
    rain_speed: Annotated[int, Field(ge=1, le=100)]

    # Life
    life_color: ColorModel
    life_speed: Annotated[int, Field(ge=0, le=20)]

    # Alarm
    alarm_speed: Annotated[int, Field(ge=0, le=10)]

    # Bad Apple
    badapple_invert: bool

    # QR Code
    qr_data: Annotated[str, Field(max_length=2048)]
    qr_error_correction: Literal["L", "M", "Q", "H"]
    qr_color_fg: ColorModel
    qr_color_bg: ColorModel
    qr_pos_x: Position
    qr_pos_y: Position
    qr_size: Annotated[int, Field(ge=1, le=64)]
    qr_border: Annotated[int, Field(ge=0, le=10)]
    qr_use_micro: bool
    qr_wobble: bool
    qr_size_mode: Literal["auto", "stretch", "manual"]

    # Draw Mode
    draw_data: Annotated[dict[DrawCoord, HexColor], Field(max_length=64 * 64)]
    draw_color_bg: ColorModel

    # Spotify (read-only through the config API; see READ_ONLY_KEYS)
    spotify_client_id: Annotated[str, Field(max_length=256)]
    spotify_linked: bool

    # Presets
    presets: dict[Slot, dict]
    preset_names: dict[Slot, Annotated[str, Field(max_length=32)]]

    # UI Theme
    ui_light_bg: CssColor
    ui_light_panel: CssColor
    ui_light_accent: CssColor
    ui_light_text: CssColor
    ui_dark_bg: CssColor
    ui_dark_panel: CssColor
    ui_dark_accent: CssColor
    ui_dark_text: CssColor
    ui_light_border: CssColor
    ui_dark_border: CssColor

    # Scheduling
    schedules: Annotated[list[ScheduleModel], Field(max_length=100)]


class StoredConfig(PublicConfig):
    spotify_client_secret: Annotated[str, Field(max_length=256)]


# Kept for backwards compatibility with code importing the old name.
ConfigModel = PublicConfig

PUBLIC_KEYS = frozenset(PublicConfig.model_fields)
STORED_KEYS = frozenset(StoredConfig.model_fields)
# Only changed through the dedicated /api/spotify/* endpoints.
READ_ONLY_KEYS = frozenset({"spotify_client_id", "spotify_linked"})
# Device-level state that belongs to the device, not to a preset.
NON_PRESET_KEYS = frozenset(
    {
        "presets",
        "preset_names",
        "schedules",
        "spotify_client_id",
        "spotify_client_secret",
        "spotify_linked",
    }
)


DEFAULT_CONFIG = {
    "mode": "clock",
    "brightness": 100,
    "show_grid": False,
    "gpio_slowdown": 2,
    "hardware_mapping": "regular",
    "color_h": {"r": 0, "g": 255, "b": 255},
    "color_m": {"r": 0, "g": 200, "b": 255},
    "color_s": {"r": 255, "g": 0, "b": 100},
    "color_ms": {"r": 255, "g": 100, "b": 0},
    "pos_x": 4,
    "pos_y": 36,
    "show_hh": True,
    "show_mm": True,
    "show_ss": True,
    "show_colons": True,
    "pos_hh_x": 4,
    "pos_hh_y": 36,
    "pos_mm_x": 26,
    "pos_mm_y": 36,
    "pos_ss_x": 48,
    "pos_ss_y": 36,
    "font_file": "7x14B.bdf",
    "clock_size": 14,
    "clock_thickness": 1,
    "format_12h": False,
    "show_ms": False,
    "clock_layout": "single",
    "ms_position": "inline",
    "gap_x": 2,
    "gap_y": 2,
    "show_stopwatch": False,
    "sw_pos_x": 4,
    "sw_pos_y": 50,
    "sw_show_hours": False,
    "sw_ms_position": "inline",
    "color_sw_h": {"r": 0, "g": 255, "b": 255},
    "color_sw_m": {"r": 0, "g": 200, "b": 255},
    "color_sw_s": {"r": 255, "g": 0, "b": 100},
    "color_sw_ms": {"r": 255, "g": 100, "b": 0},
    "sw_state": "stopped",
    "sw_start_time": 0.0,
    "sw_elapsed": 0.0,
    "warning_color": {"r": 255, "g": 200, "b": 0},
    "warning_thickness": 3,
    "warning_blink_speed": 50,
    "warning_size": 44,
    "smiley_face_color": {"r": 255, "g": 200, "b": 0},
    "smiley_cheek_color": {"r": 200, "g": 50, "b": 0},
    "smiley_eye_color": {"r": 255, "g": 255, "b": 255},
    "smiley_tongue_color": {"r": 255, "g": 50, "b": 50},
    "rain_color": {"r": 0, "g": 255, "b": 0},
    "rain_speed": 10,
    "life_color": {"r": 0, "g": 255, "b": 255},
    "life_speed": 10,
    "alarm_speed": 5,
    "badapple_invert": False,
    "qr_data": "https://github.com/nicx17",
    "qr_error_correction": "L",
    "qr_color_fg": {"r": 255, "g": 255, "b": 255},
    "qr_color_bg": {"r": 0, "g": 0, "b": 0},
    "qr_pos_x": 0,
    "qr_pos_y": 0,
    "qr_size": 58,
    "qr_border": 1,
    "qr_use_micro": False,
    "qr_wobble": False,
    "qr_size_mode": "auto",
    "draw_data": {},
    "draw_color_bg": {"r": 0, "g": 0, "b": 0},
    "spotify_client_id": "",
    "spotify_client_secret": "",
    "spotify_linked": False,
    "presets": {slot: {} for slot in PRESET_SLOTS},
    "preset_names": {slot: f"Slot {slot[5:]}" for slot in PRESET_SLOTS},
    "ui_light_bg": "#ffde00",
    "ui_light_panel": "#f4f4f0",
    "ui_light_accent": "#ffde00",
    "ui_light_text": "#000000",
    "ui_dark_bg": "#000000",
    "ui_dark_panel": "#000000",
    "ui_dark_accent": "#ffde00",
    "ui_dark_text": "#ffde00",
    "ui_light_border": "#000000",
    "ui_dark_border": "#ffde00",
    "schedules": [],
}


def defaults():
    """Return a fresh deep copy of the defaults (safe to mutate)."""
    return copy.deepcopy(DEFAULT_CONFIG)


def validate_config(data):
    """Strictly validate a complete stored config. Raises ValidationError."""
    return StoredConfig(**data).model_dump()


def sanitize_config(data, fallback=None):
    """
    Leniently coerce `data` into a valid stored config.

    Unknown keys are dropped, and every key that fails validation is reset to its
    value in `fallback` (the defaults when omitted). Never raises.
    """
    base = fallback if fallback is not None else DEFAULT_CONFIG
    merged = copy.deepcopy(base)
    merged.update({k: copy.deepcopy(v) for k, v in data.items() if k in STORED_KEYS})

    used_fallback = set()
    for _ in range(3):
        try:
            return validate_config(merged)
        except ValidationError as exc:
            for key in {err["loc"][0] for err in exc.errors() if err["loc"]}:
                # Try the fallback value first, then the factory default.
                if key in used_fallback or key not in base:
                    merged[key] = copy.deepcopy(DEFAULT_CONFIG[key])
                else:
                    print(f"[config] Invalid value for '{key}', reverting it.")
                    merged[key] = copy.deepcopy(base[key])
                    used_fallback.add(key)
    return validate_config(defaults())


def preset_payload(state):
    """Extract the part of a config that belongs in a preset."""
    return {k: copy.deepcopy(v) for k, v in state.items() if k not in NON_PRESET_KEYS}


def migrate_legacy(data):
    """In-place upgrades for configs written by older versions."""
    # Stopwatch used to be an overlay on the clock; it is now its own mode.
    if data.get("mode") == "clock" and data.get("show_stopwatch") is True:
        data["mode"] = "stopwatch"
    for preset in (data.get("presets") or {}).values():
        if (
            isinstance(preset, dict)
            and preset.get("mode") == "clock"
            and preset.get("show_stopwatch") is True
        ):
            preset["mode"] = "stopwatch"
    return data


def load_config():
    saved = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if not isinstance(saved, dict):
                raise TypeError("config root is not an object")
        except Exception as e:
            print("Failed to load config:", e)
            saved = {}
    return sanitize_config(migrate_legacy(saved))


_write_lock = threading.Lock()


def save_config(state_dict):
    """Atomically write the config to disk (temp file + fsync + rename)."""
    data = {k: v for k, v in state_dict.items() if k in STORED_KEYS}
    with _write_lock:
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            temp_file = CONFIG_FILE.with_suffix(CONFIG_FILE.suffix + ".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, CONFIG_FILE)
        except Exception as e:
            print("Failed to save config:", e)


class DebouncedSaver:
    """
    Coalesces bursts of changes into a single SD card write.

    `snapshot_fn` is called when the timer fires, so the write always reflects the
    latest state rather than the state at the time the save was requested.
    """

    def __init__(self, snapshot_fn, delay=0.5, save_fn=save_config):
        self._snapshot_fn = snapshot_fn
        self._save_fn = save_fn
        self._delay = delay
        self._lock = threading.Lock()
        self._timer = None

    def request(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._delay, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self):
        with self._lock:
            self._timer = None
        self._save_fn(self._snapshot_fn())

    def flush(self):
        """Write immediately if a save is pending (used on shutdown)."""
        with self._lock:
            pending = self._timer is not None
            if pending:
                self._timer.cancel()
                self._timer = None
        if pending:
            self._save_fn(self._snapshot_fn())
