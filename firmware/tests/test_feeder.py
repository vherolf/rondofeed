import asyncio
import unittest

import fakes
from feeder import Feeder, FeedError
from fakes import Cfg, Clock, FakeBeam, FakeMotor, make_store


def build(**kw):
    store_kw = kw.pop("store", {})
    cfg_kw = kw.pop("cfg", {})
    beam = kw.pop("beam", None) or FakeBeam()
    store, path = make_store(**store_kw)
    motor = FakeMotor()
    clock = Clock()
    feeder = Feeder(motor, beam, store, Cfg(**cfg_kw), now_ms=clock)
    events = []
    return feeder, motor, beam, store, path, clock, events


class PositionTest(unittest.TestCase):
    def test_target_rounds_the_sum(self):
        feeder = build()[0]
        self.assertEqual(feeder.target(0), 0)
        self.assertEqual(feeder.target(48), 6400)
        self.assertEqual(feeder.target(1), 133)
        self.assertEqual(feeder.target(2), 267)   # 266,67, nicht 2 x 133

    def test_all_portions_add_up_to_target(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build(cfg={"MAX_PER_REQUEST": 100, "MAX_PER_HOUR": 1000})
            for _ in range(5):
                feeder.feed(10, events.append)
                await feeder.task
                clock.t += 1000
            return feeder, motor
        feeder, motor = asyncio.run(go())
        self.assertEqual(feeder.k, 47)
        self.assertEqual(sum(motor.moves), feeder.target(47))
        self.assertEqual(feeder.remaining, 0)


class FeedTest(unittest.TestCase):
    def test_events_and_state(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build()
            feeder.feed(2, events.append)
            await feeder.task
            return feeder, store, events
        feeder, store, events = asyncio.run(go())
        self.assertEqual(events, ["EVENT fed 1 beams=2", "EVENT fed 2 beams=2", "EVENT done fed=2 missed=0"])
        self.assertEqual(store["k"], 2)
        self.assertFalse(store["dirty"])
        self.assertFalse(feeder.busy)
        self.assertEqual(feeder.last, "fed")

    def test_no_portion_is_reported_and_goes_on(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build(beam=FakeBeam([0, 1]))
            feeder.feed(2, events.append)
            await feeder.task
            return feeder, events
        feeder, events = asyncio.run(go())
        self.assertEqual(events, ["EVENT no_portion 1", "EVENT fed 2 beams=1", "EVENT done fed=1 missed=1"])
        self.assertEqual(feeder.k, 2)

    def test_retry_extra_tries_more_positions(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build(beam=FakeBeam([0, 0, 1]), cfg={"RETRY_EXTRA": 2})
            feeder.feed(1, events.append)
            await feeder.task
            return feeder, events
        feeder, events = asyncio.run(go())
        self.assertEqual(events, ["EVENT fed 1 beams=1", "EVENT done fed=1 missed=0"])
        self.assertEqual(feeder.k, 3)

    def test_empty_disc(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build(store={"k": 46})
            feeder.feed(3, events.append)
            await feeder.task
            return feeder, events
        feeder, events = asyncio.run(go())
        self.assertEqual(events, ["EVENT fed 1 beams=2", "EVENT error empty", "EVENT done fed=1 missed=0"])
        self.assertEqual(feeder.remaining, 0)
        with self.assertRaises(FeedError) as cm:
            feeder.feed(1, events.append)
        self.assertEqual(cm.exception.code, "empty")

    def test_motor_failure_makes_position_uncertain(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build()
            motor.fail = True
            feeder.feed(1, events.append)
            await feeder.task
            return feeder, store, events
        feeder, store, events = asyncio.run(go())
        self.assertEqual(events, ["EVENT error motor", "EVENT done fed=0 missed=0"])
        self.assertTrue(feeder.uncertain)
        self.assertTrue(store["dirty"])
        with self.assertRaises(FeedError) as cm:
            feeder.feed(1, events.append)
        self.assertEqual(cm.exception.code, "uncertain")

    def test_stop_after_current_portion(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build()
            motor.hold = asyncio.Event()
            feeder.feed(5, events.append)
            await asyncio.sleep(0)
            feeder.stop()
            motor.hold.set()
            await feeder.task
            return feeder, events
        feeder, events = asyncio.run(go())
        self.assertEqual(events, ["EVENT fed 1 beams=2", "EVENT done fed=1 missed=0"])
        self.assertEqual(feeder.k, 1)

    def test_busy(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build()
            motor.hold = asyncio.Event()
            feeder.feed(1, events.append)
            with self.assertRaises(FeedError) as cm:
                feeder.feed(1, events.append)
            code = cm.exception.code
            motor.hold.set()
            await feeder.task
            return code
        self.assertEqual(asyncio.run(go()), "busy")


class LimitsTest(unittest.TestCase):
    def test_per_request(self):
        feeder = build()[0]
        for n in (0, 11, -1):
            with self.assertRaises(FeedError) as cm:
                feeder.feed(n, print)
            self.assertEqual(cm.exception.code, "limit")

    def test_min_gap(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build(cfg={"MIN_GAP_MS": 500})
            feeder.feed(1, events.append)
            await feeder.task
            clock.t = 100
            with self.assertRaises(FeedError) as cm:
                feeder.feed(1, events.append)
            code = cm.exception.code
            clock.t = 600
            feeder.feed(1, events.append)
            await feeder.task
            return code
        self.assertEqual(asyncio.run(go()), "limit")

    def test_per_hour(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build(cfg={"MAX_PER_HOUR": 4})
            feeder.feed(3, events.append)
            await feeder.task
            clock.t = 1000
            with self.assertRaises(FeedError) as cm:
                feeder.feed(2, events.append)
            code = cm.exception.code
            clock.t = 3600001
            feeder.feed(2, events.append)
            await feeder.task
            return code
        self.assertEqual(asyncio.run(go()), "limit")


class StateTest(unittest.TestCase):
    def test_position_survives_restart(self):
        from store import Store

        async def go():
            feeder, motor, beam, store, path, clock, events = build()
            feeder.feed(3, events.append)
            await feeder.task
            return path
        path = asyncio.run(go())
        again = Feeder(FakeMotor(), FakeBeam(), Store(path), Cfg())
        self.assertEqual(again.k, 3)
        self.assertFalse(again.uncertain)

    def test_dirty_flag_means_uncertain_after_restart(self):
        feeder = build(store={"k": 5, "dirty": True})[0]
        self.assertTrue(feeder.uncertain)
        self.assertIn("state=uncertain", feeder.status())
        feeder.zero()
        self.assertFalse(feeder.uncertain)
        self.assertEqual(feeder.k, 0)

    def test_disc_change_needs_zero(self):
        feeder = build(store={"k": 5})[0]
        feeder.set_portions(59)
        self.assertEqual(feeder.portions, 59)
        self.assertTrue(feeder.uncertain)
        self.assertEqual(feeder.target(60), 6400)
        feeder.zero()
        self.assertFalse(feeder.uncertain)

    def test_jog_makes_uncertain(self):
        async def go():
            feeder, motor, beam, store, path, clock, events = build()
            feeder.jog(-20, events.append)
            await feeder.task
            return feeder, motor
        feeder, motor = asyncio.run(go())
        self.assertEqual(motor.moves, [-20])
        self.assertTrue(feeder.uncertain)

    def test_jog_limits(self):
        feeder = build()[0]
        for steps in (0, 801, -801):
            with self.assertRaises(FeedError):
                feeder.jog(steps, print)


if __name__ == "__main__":
    unittest.main()
