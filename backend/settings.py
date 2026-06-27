"""
Runtime settings for WaveDisp.

Values come from environment variables, with optional .env loading for local
development and Raspberry Pi deployments.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def env(name, default):
    return os.getenv(name, default)


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_path(value):
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path
