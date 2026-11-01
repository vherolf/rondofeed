import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config as real_config  # noqa: E402
from store import Store  # noqa: E402


class Cfg:
    """Die Werte aus config.py, im Test mit kurzen Wartezeiten."""

    def __init__(self, **kw):
        for key in dir(real_config):
            if key.isupper():
                setattr(self, key, getattr(real_config, key))
        self.BEAM_SETTLE_MS = 0
        self.BEAM_TIMEOUT_MS = 10
        self.MIN_GAP_MS = 0
        for key, value in kw.items():
            setattr(self, key, value)


class FakeMotor:
    def __init__(self):
        self.moves = []
        self.fail = False
        self.hold = None   # asyncio.Event, haelt die Fahrt an

    async def move(self, steps):
        if self.hold is not None:
            await self.hold.wait()
        if self.fail:
            raise RuntimeError("motor")
        self.moves.append(steps)


class FakeBeam:
    def __init__(self, pattern=None):
        self.count = 0
        self.pattern = pattern if pattern is not None else [2]   # Unterbrechungen je Portion, 0 = keine
        self.calls = 0

    def clear(self):
        self.count = 0

    async def wait(self, timeout_ms):
        n = self.pattern[min(self.calls, len(self.pattern) - 1)]
        self.calls += 1
        self.count = n
        return n > 0


class Clock:
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t


def make_store(**kw):
    path = os.path.join(tempfile.mkdtemp(), "state.json")
    store = Store(path)
    if kw:
        store.update(**kw)
    return store, path
