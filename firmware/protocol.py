"""Befehlszeilen verstehen und beantworten, siehe PROTOCOL.md. Reines Python, gilt fuer USB und BLE gleich."""
from feeder import FeedError


class Session:
    """Eine Verbindung. USB ist vertraut, BLE muss sich mit AUTH anmelden."""

    def __init__(self, trusted):
        self.trusted = trusted
        self.authed = trusted


def parse(line):
    """Gibt (id oder None, Befehl, Argumente) zurueck, wirft ValueError bei leerer Zeile."""
    parts = line.strip().split()
    if not parts:
        raise ValueError("empty")
    req_id = None
    if parts[0].startswith("@"):
        req_id = parts[0][1:]
        parts = parts[1:]
        if not parts:
            raise ValueError("empty")
    return req_id, parts[0].upper(), parts[1:]


def _same(a, b):
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= ord(x) ^ ord(y)
    return diff == 0


class Dispatcher:
    OPEN = ("PING", "VERSION", "AUTH")

    def __init__(self, feeder, store, cfg, emit):
        self.feeder = feeder
        self.store = store
        self.cfg = cfg
        self.emit = emit

    def handle(self, line, session):
        """Fuehrt einen Befehl aus und gibt die Antwortzeile zurueck."""
        try:
            req_id, cmd, args = parse(line)
        except ValueError:
            return "ERR syntax empty line"
        prefix = "@%s " % req_id if req_id is not None else ""
        try:
            answer = self._run(cmd, args, session)
        except FeedError as e:
            answer = "ERR %s %s" % (e.code, e.text) if e.text else "ERR %s" % e.code
        except Exception as e:   # ein Fehler im Befehl darf die Verbindung nicht beenden
            answer = "ERR internal %s" % type(e).__name__
        return prefix + answer

    def _int(self, args, default=None):
        if not args:
            if default is None:
                raise FeedError("syntax", "number expected")
            return default
        try:
            return int(args[0])
        except ValueError:
            raise FeedError("syntax", "number expected")

    def _run(self, cmd, args, session):
        if not session.authed and cmd not in self.OPEN:
            raise FeedError("auth", "send AUTH first")
        if cmd == "PING":
            return "OK pong"
        if cmd == "VERSION":
            return "OK fw=%s proto=%d" % (self.cfg.FW_VERSION, self.cfg.PROTO_VERSION)
        if cmd == "AUTH":
            token = self.store["token"]
            if not token:
                raise FeedError("auth", "no token set, use SETTOKEN over USB")
            if not args or not _same(args[0], token):
                raise FeedError("auth", "wrong token")
            session.authed = True
            return "OK"
        if cmd == "STATUS":
            return "OK " + self.feeder.status()
        if cmd == "FEED":
            n = self._int(args, 1)
            self.feeder.feed(n, self.emit)
            return "OK accepted %d" % n
        if cmd == "STOP":
            self.feeder.stop()
            return "OK"
        if cmd == "ZERO":
            self.feeder.zero()
            return "OK"
        if cmd == "JOG":
            self.feeder.jog(self._int(args), self.emit)
            return "OK"
        if cmd == "DISC":
            self.feeder.set_portions(self._int(args))
            return "OK"
        if cmd == "SETTOKEN":
            if not session.trusted:
                raise FeedError("auth", "only over USB")
            if not args or len(args[0]) > 32:
                raise FeedError("syntax", "token of 1 to 32 characters")
            self.store.update(token=args[0])
            return "OK"
        raise FeedError("syntax", "unknown command")
