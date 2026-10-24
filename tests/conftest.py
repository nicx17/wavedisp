import multiprocessing
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.channels import FrameChannel, SnapshotChannel
from backend.config import defaults, validate_config
from backend.state import StateStore


class SaveRecorder:
    def __init__(self):
        self.saves = []

    def __call__(self, state):
        self.saves.append(state)


@pytest.fixture
def saves():
    return SaveRecorder()


@pytest.fixture
def channels():
    ctx = multiprocessing.get_context("fork")
    return SnapshotChannel(ctx), FrameChannel(ctx)


@pytest.fixture
def store(channels, saves):
    initial = validate_config(defaults())
    return StateStore(initial, channels[0], save_delay=0.01, save_fn=saves)
