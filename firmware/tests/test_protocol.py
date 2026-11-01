import asyncio
import unittest

import fakes
from fakes import Cfg, Clock, FakeBeam, FakeMotor, make_store
from feeder import Feeder
from protocol import Dispatcher, Session, parse


def build():
    store, path = make_store()
    cfg = Cfg()
    feeder = Feeder(FakeMotor(), FakeBeam(), store, cfg, now_ms=Clock())
    events = []
    return Dispatcher(feeder, store, cfg, events.append), feeder, store, events


class ParseTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse("feed 2"), (None, "FEED", ["2"]))
        self.assertEqual(parse("@7 FEED 2\r\n"), ("7", "FEED", ["2"]))
        self.assertEqual(parse("  ping "), (None, "PING", []))

    def test_empty(self):
        for line in ("", "   ", "@5"):
            with self.assertRaises(ValueError):
                parse(line)


class UsbTest(unittest.TestCase):
    def setUp(self):
        self.d, self.feeder, self.store, self.events = build()
        self.usb = Session(trusted=True)

    def test_basic_answers(self):
        self.assertEqual(self.d.handle("PING", self.usb), "OK pong")
        self.assertEqual(self.d.handle("VERSION", self.usb), "OK fw=0.1 proto=1")
        self.assertEqual(self.d.handle("@3 STATUS", self.usb),
                         "@3 OK k=0 portions=47 remaining=47 busy=0 state=ok last=none")

    def test_errors(self):
        self.assertEqual(self.d.handle("NOPE", self.usb), "ERR syntax unknown command")
        self.assertTrue(self.d.handle("FEED x", self.usb).startswith("ERR syntax"))
        self.assertTrue(self.d.handle("", self.usb).startswith("ERR syntax"))
        self.assertTrue(self.d.handle("FEED 11", self.usb).startswith("ERR limit"))
        self.assertEqual(self.d.handle("@9 FEED 11", self.usb)[:12], "@9 ERR limit")

    def test_feed_over_usb(self):
        async def go():
            answer = self.d.handle("@1 FEED 2", self.usb)
            await self.feeder.task
            return answer
        self.assertEqual(asyncio.run(go()), "@1 OK accepted 2")
        self.assertEqual(self.events[-1], "EVENT done fed=2 missed=0")
        self.assertEqual(self.feeder.k, 2)

    def test_feed_default_is_one(self):
        async def go():
            answer = self.d.handle("FEED", self.usb)
            await self.feeder.task
            return answer
        self.assertEqual(asyncio.run(go()), "OK accepted 1")

    def test_zero_disc_jog(self):
        self.assertEqual(self.d.handle("DISC 59", self.usb), "OK")
        self.assertIn("state=uncertain", self.d.handle("STATUS", self.usb))
        self.assertTrue(self.d.handle("FEED", self.usb).startswith("ERR uncertain"))
        self.assertEqual(self.d.handle("ZERO", self.usb), "OK")
        self.assertIn("portions=59", self.d.handle("STATUS", self.usb))
        self.assertTrue(self.d.handle("DISC 0", self.usb).startswith("ERR syntax"))

    def test_settoken_over_usb(self):
        self.assertEqual(self.d.handle("SETTOKEN s3cret", self.usb), "OK")
        self.assertEqual(self.store["token"], "s3cret")
        self.assertTrue(self.d.handle("SETTOKEN", self.usb).startswith("ERR syntax"))
        self.assertTrue(self.d.handle("SETTOKEN " + "x" * 33, self.usb).startswith("ERR syntax"))


class RobustTest(unittest.TestCase):
    def test_unexpected_error_is_answered(self):
        d, feeder, store, events = build()

        def boom():
            raise KeyError("x")
        feeder.status = boom
        self.assertEqual(d.handle("@4 STATUS", Session(trusted=True)), "@4 ERR internal KeyError")
        self.assertEqual(d.handle("PING", Session(trusted=True)), "OK pong")


class BleAuthTest(unittest.TestCase):
    def setUp(self):
        self.d, self.feeder, self.store, self.events = build()
        self.ble = Session(trusted=False)

    def test_open_commands_without_login(self):
        self.assertEqual(self.d.handle("PING", self.ble), "OK pong")
        self.assertTrue(self.d.handle("VERSION", self.ble).startswith("OK fw="))

    def test_everything_else_needs_login(self):
        for cmd in ("STATUS", "FEED", "STOP", "ZERO", "JOG 5", "DISC 59"):
            self.assertTrue(self.d.handle(cmd, self.ble).startswith("ERR auth"), cmd)
        self.assertEqual(self.feeder.k, 0)

    def test_no_token_set(self):
        self.assertTrue(self.d.handle("AUTH abc", self.ble).startswith("ERR auth"))
        self.assertFalse(self.ble.authed)

    def test_login(self):
        self.store.update(token="s3cret")
        self.assertTrue(self.d.handle("AUTH wrong", self.ble).startswith("ERR auth"))
        self.assertTrue(self.d.handle("AUTH", self.ble).startswith("ERR auth"))
        self.assertEqual(self.d.handle("@2 AUTH s3cret", self.ble), "@2 OK")
        self.assertTrue(self.d.handle("STATUS", self.ble).startswith("OK k=0"))

    def test_login_is_per_connection(self):
        self.store.update(token="s3cret")
        self.d.handle("AUTH s3cret", self.ble)
        other = Session(trusted=False)
        self.assertTrue(self.d.handle("STATUS", other).startswith("ERR auth"))

    def test_settoken_not_over_ble(self):
        self.store.update(token="s3cret")
        self.d.handle("AUTH s3cret", self.ble)
        self.assertTrue(self.d.handle("SETTOKEN new", self.ble).startswith("ERR auth"))
        self.assertEqual(self.store["token"], "s3cret")


if __name__ == "__main__":
    unittest.main()
