import unittest

import fakes  # noqa: F401
import motor_plan


class SegmentsTest(unittest.TestCase):
    def test_sum_is_exact(self):
        for steps in (1, 2, 5, 13, 59, 60, 61, 91, 133, 134, 800, 6400):
            plan = motor_plan.segments(steps, 300, 2000, 60, 6)
            self.assertEqual(sum(c for c, _ in plan), steps, steps)
            self.assertTrue(all(c >= 1 for c, _ in plan))

    def test_zero_and_negative(self):
        self.assertEqual(motor_plan.segments(0, 300, 2000, 60, 6), [])
        self.assertEqual(motor_plan.segments(-3, 300, 2000, 60, 6), [])

    def test_rates_in_range_and_symmetric(self):
        plan = motor_plan.segments(400, 300, 2000, 60, 6)
        rates = [r for _, r in plan]
        self.assertTrue(all(300 <= r <= 2000 for r in rates))
        self.assertEqual(rates, rates[::-1])
        self.assertEqual(max(rates), 2000)

    def test_short_move_runs_slowly(self):
        self.assertEqual(motor_plan.segments(8, 300, 2000, 60, 6), [(8, 300)])


if __name__ == "__main__":
    unittest.main()
