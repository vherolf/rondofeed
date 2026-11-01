"""Feed-Ablauf: Position, Grenzen, Lichtschranke. Reines Python, Motor und Sensor kommen von aussen."""
import asyncio
import time

_ticks_ms = getattr(time, "ticks_ms", lambda: int(time.monotonic() * 1000))
_ticks_diff = getattr(time, "ticks_diff", lambda a, b: a - b)


class FeedError(Exception):
    def __init__(self, code, text=""):
        Exception.__init__(self, code)
        self.code = code
        self.text = text


class Feeder:
    def __init__(self, motor, beam, store, cfg, now_ms=None):
        self.motor = motor
        self.beam = beam
        self.store = store
        self.cfg = cfg
        self.now_ms = now_ms or _ticks_ms
        self.busy = False
        self.last = "none"
        self.uncertain = bool(store["dirty"])  # Strom war weg, waehrend sich die Scheibe bewegte
        self._stop = False
        self._history = []   # (Zeit, Anzahl) der Feeds fuer das Stundenlimit
        self._last_start = None
        self.task = None

    # --- Position ---
    @property
    def k(self):
        return self.store["k"]

    @property
    def portions(self):
        return self.store["portions"]

    @property
    def remaining(self):
        return max(0, self.portions - self.k)

    def target(self, k):
        """Mikroschritte der Position k. Das Ziel wird summiert und gerundet, nicht jeder Schritt einzeln."""
        per_rev = self.cfg.MICROSTEPS_PER_REV
        return (2 * k * per_rev + (self.portions + 1)) // (2 * (self.portions + 1))

    def status(self):
        return "k=%d portions=%d remaining=%d busy=%d state=%s last=%s" % (
            self.k, self.portions, self.remaining, 1 if self.busy else 0,
            "uncertain" if self.uncertain else "ok", self.last)

    # --- Befehle ---
    def feed(self, n, emit):
        """Prueft die Grenzen und startet den Feed im Hintergrund. Wirft FeedError, wenn er abgelehnt wird."""
        cfg = self.cfg
        if self.busy:
            raise FeedError("busy", "a move is running")
        if self.uncertain:
            raise FeedError("uncertain", "align the disc and send ZERO")
        if n < 1 or n > cfg.MAX_PER_REQUEST:
            raise FeedError("limit", "1 to %d portions per request" % cfg.MAX_PER_REQUEST)
        if self.remaining < 1:
            raise FeedError("empty", "load the disc and send ZERO")
        now = self.now_ms()
        if self._last_start is not None and _ticks_diff(now, self._last_start) < cfg.MIN_GAP_MS:
            raise FeedError("limit", "too soon after the last request")
        self._history = [(t, c) for (t, c) in self._history if _ticks_diff(now, t) < 3600000]
        if sum(c for (_, c) in self._history) + n > cfg.MAX_PER_HOUR:
            raise FeedError("limit", "hourly limit reached")
        self._history.append((now, n))
        self._last_start = now
        self.busy = True
        self._stop = False
        self.task = asyncio.create_task(self._run(n, emit))
        return self.task

    def stop(self):
        self._stop = True

    def zero(self):
        if self.busy:
            raise FeedError("busy", "a move is running")
        self.store.update(k=0, dirty=False)
        self.uncertain = False

    def set_portions(self, portions):
        if self.busy:
            raise FeedError("busy", "a move is running")
        if portions < 1 or portions > 200:
            raise FeedError("syntax", "portions 1 to 200")
        self.store.update(portions=portions, k=0)
        self.uncertain = True   # die neue Scheibe muss erst ausgerichtet und mit ZERO bestaetigt werden

    def jog(self, steps, emit):
        if self.busy:
            raise FeedError("busy", "a move is running")
        if abs(steps) > self.cfg.JOG_MAX or steps == 0:
            raise FeedError("syntax", "steps must be 1 to %d" % self.cfg.JOG_MAX)
        self.busy = True
        self.task = asyncio.create_task(self._jog(steps, emit))
        return self.task

    # --- Ablauf ---
    async def _jog(self, steps, emit):
        try:
            await self.motor.move(steps)
            self.uncertain = True   # die Scheibe steht nicht mehr auf der gezaehlten Position
            self.store.update(dirty=True)
        except Exception:
            self.uncertain = True
            emit("EVENT error motor")
        finally:
            self.busy = False

    async def _advance(self):
        k = self.k
        steps = self.target(k + 1) - self.target(k)
        self.store.update(dirty=True)
        await self.motor.move(steps)
        self.store.update(k=k + 1, dirty=False)

    async def _one(self, i, emit):
        cfg = self.cfg
        for _ in range(1 + cfg.RETRY_EXTRA):
            if self.remaining < 1:
                return False
            self.beam.clear()
            await self._advance()
            if await self.beam.wait(cfg.BEAM_TIMEOUT_MS):
                await asyncio.sleep(cfg.BEAM_SETTLE_MS / 1000)
                emit("EVENT fed %d beams=%d" % (i, self.beam.count))
                return True
        emit("EVENT no_portion %d" % i)
        return False

    async def _run(self, n, emit):
        fed = missed = 0
        try:
            for i in range(1, n + 1):
                if self._stop:
                    break
                if self.remaining < 1:
                    emit("EVENT error empty")
                    break
                if await self._one(i, emit):
                    fed += 1
                    self.last = "fed"
                else:
                    missed += 1
                    self.last = "no_portion"
        except Exception:
            self.uncertain = True
            self.last = "error"
            emit("EVENT error motor")
        finally:
            self.busy = False
            self._stop = False
            emit("EVENT done fed=%d missed=%d" % (fed, missed))
