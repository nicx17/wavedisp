"""
Shared-memory channels between the API process and the matrix render process.

ARCHITECTURE OVERVIEW:
All config writers (API, scheduler, Spotify poller) live in the main process, and
the render process only ever reads config. So instead of a multiprocessing.Manager
(where every dict access is a socket round-trip to a third process), each direction
is a single-writer "latest value wins" mailbox in shared memory:

- SnapshotChannel: main -> render. A pickled dict of render settings.
- FrameChannel:    render -> main. Raw RGB bytes of the last drawn frame, used by
                   the MJPEG preview stream.

Readers poll a sequence counter, which is a plain shared-memory read (~2us), and
only take the lock and copy bytes when the counter has moved.
"""

import multiprocessing
import pickle
import time

FRAME_BYTES = 64 * 64 * 3


class _Mailbox:
    def __init__(self, ctx, capacity):
        self.capacity = capacity
        self._buf = ctx.RawArray("B", capacity)
        self._len = ctx.RawValue("L", 0)
        self._seq = ctx.RawValue("Q", 0)
        self._lock = ctx.Lock()

    @property
    def seq(self):
        return self._seq.value

    def write(self, data):
        size = len(data)
        if size > self.capacity:
            raise ValueError(f"payload of {size} bytes exceeds {self.capacity}")
        with self._lock:
            memoryview(self._buf).cast("B")[:size] = data
            self._len.value = size
            self._seq.value += 1

    def read(self):
        """Return (seq, bytes) of the latest payload."""
        with self._lock:
            size = self._len.value
            return self._seq.value, bytes(memoryview(self._buf).cast("B")[:size])


class SnapshotChannel:
    """
    Publishes render-settings snapshots from the main process.

    pickle is safe here: the buffer is anonymous shared memory created by the main
    process before forking the renderer, so only our own two processes can write it.
    """

    def __init__(self, ctx=None, capacity=512 * 1024):
        self._box = _Mailbox(ctx or multiprocessing, capacity)

    @property
    def seq(self):
        return self._box.seq

    def publish(self, snapshot):
        self._box.write(pickle.dumps(snapshot, protocol=pickle.HIGHEST_PROTOCOL))

    def receive(self):
        seq, data = self._box.read()
        return seq, (pickle.loads(data) if data else None)


class FrameChannel:
    """Carries the latest rendered frame back to the main process."""

    def __init__(self, ctx=None):
        ctx = ctx or multiprocessing
        self._box = _Mailbox(ctx, FRAME_BYTES)
        self._written_at = ctx.RawValue("d", 0.0)

    @property
    def seq(self):
        return self._box.seq

    @property
    def written_at(self):
        return self._written_at.value

    def write(self, rgb_bytes):
        self._box.write(rgb_bytes)
        self._written_at.value = time.time()

    def read(self):
        return self._box.read()
