"""
Global Configuration State Manager for WaveDisp.

ARCHITECTURE OVERVIEW:
This module provides the default configuration state.
Persistence is handled through save_config, and API interaction uses save_debounced.
State is passed between processes using multiprocessing.Manager().dict().
"""

import threading
import json
import os
from typing import Dict
from pydantic import BaseModel
from backend.settings import env, resolve_path

CONFIG_FILE = resolve_path(env("WAVEDISP_CONFIG_FILE", "backend/config.json"))


class ColorModel(BaseModel):
    r: int
    g: int
    b: int


class ConfigModel(BaseModel):
    mode: str
    brightness: int
    show_grid: bool
    gpio_slowdown: int
    hardware_mapping: str

    # Clock
    color_h: ColorModel
    color_m: ColorModel
    color_s: ColorModel
    color_ms: ColorModel
    pos_x: int
    pos_y: int
    show_hh: bool
    show_mm: bool
    show_ss: bool
    show_colons: bool
    pos_hh_x: int
    pos_hh_y: int
    pos_mm_x: int
    pos_mm_y: int
    pos_ss_x: int
    pos_ss_y: int
    font_file: str
    clock_size: int
    clock_thickness: int
    format_12h: bool
    show_ms: bool
    clock_layout: str
    ms_position: str
    gap_x: int
    gap_y: int

    # Stopwatch
    show_stopwatch: bool
    sw_pos_x: int
    sw_pos_y: int
    sw_show_hours: bool
    sw_ms_position: str
    color_sw_h: ColorModel
    color_sw_m: ColorModel
    color_sw_s: ColorModel
    color_sw_ms: ColorModel
    sw_state: str
    sw_start_time: float
    sw_elapsed: float

    # Warning
    warning_color: ColorModel
    warning_thickness: int
    warning_blink_speed: int
    warning_size: int

    # Smiley
    smiley_face_color: ColorModel
    smiley_cheek_color: ColorModel
    smiley_eye_color: ColorModel
    smiley_tongue_color: ColorModel

    # Rain
    rain_color: ColorModel
    rain_speed: int

    # Life
    life_color: ColorModel
    life_speed: int

    # Alarm
    alarm_speed: int

    # Bad Apple
    badapple_invert: bool

    # QR Code
    qr_data: str
    qr_error_correction: str
    qr_color_fg: ColorModel
    qr_color_bg: ColorModel
    qr_pos_x: int
    qr_pos_y: int
    qr_size: int
    qr_border: int
    qr_use_micro: bool
    qr_wobble: bool
    qr_size_mode: str

    # Draw Mode
    draw_data: Dict[str, str]
    draw_color_bg: ColorModel

    # Spotify
    spotify_client_id: str
    spotify_client_secret: str
    spotify_linked: bool

    # Presets
    presets: Dict[str, dict]
    preset_names: Dict[str, str]

    # UI Theme
    ui_light_bg: str
    ui_light_panel: str
    ui_light_accent: str
    ui_light_text: str
    ui_dark_bg: str
    ui_dark_panel: str
    ui_dark_accent: str
    ui_dark_text: str
    ui_light_border: str
    ui_dark_border: str


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
    "presets": {
        "slot_1": {},
        "slot_2": {},
        "slot_3": {},
        "slot_4": {},
        "slot_5": {},
        "slot_6": {},
        "slot_7": {},
        "slot_8": {},
        "slot_9": {},
        "slot_10": {},
    },
    "preset_names": {
        "slot_1": "Slot 1",
        "slot_2": "Slot 2",
        "slot_3": "Slot 3",
        "slot_4": "Slot 4",
        "slot_5": "Slot 5",
        "slot_6": "Slot 6",
        "slot_7": "Slot 7",
        "slot_8": "Slot 8",
        "slot_9": "Slot 9",
        "slot_10": "Slot 10",
    },
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
}


def load_config():
    data = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            data.update(saved_data)
        except Exception as e:
            print("Failed to load config:", e)
    return data


def save_config(state_dict):
    # Filter out private keys and non-serializable byte buffers
    data = {
        k: v
        for k, v in state_dict.items()
        if not k.startswith("_") and k != "spotify_image_bytes"
    }

    # Sanitize presets to ensure no bytes or private variables are saved
    if "presets" in data:
        clean_presets = {}
        for slot, preset_data in data["presets"].items():
            if isinstance(preset_data, dict):
                clean_presets[slot] = {
                    k: v
                    for k, v in preset_data.items()
                    if not k.startswith("_") and k != "spotify_image_bytes"
                }
        data["presets"] = clean_presets
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


_save_timer = None


def save_debounced(state_dict, delay=0.5):
    global _save_timer
    if _save_timer is not None:
        _save_timer.cancel()
    _save_timer = threading.Timer(delay, save_config, args=(dict(state_dict),))
    _save_timer.start()
