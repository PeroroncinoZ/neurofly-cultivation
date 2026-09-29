"""Behavioral checks for temporal modulation and swept capture."""
import math
import random
import unittest
from types import SimpleNamespace

from collision import movement_touches_fruit
from controller import Controller
from fly import Fly


class TemporalNavigationTests(unittest.TestCase):
    def test_trend_modulates_magnitude_but_never_direction(self):
        for left, right in [(0.205, 0.2), (0.2, 0.205)]:
            turns = []
            for start in [0.3, 0.4, 0.5]:
                controller = Controller()
                controller.choose_turn_rate(start, left, right, 0)
                turns.append(controller.choose_turn_rate(0.4, left, right, 0.1))
            self.assertLess(abs(turns[0]), abs(turns[1]))
            self.assertLess(abs(turns[1]), abs(turns[2]))
            self.assertTrue(all(turn * (left - right) > 0 for turn in turns))
        controller = Controller()
        controller.choose_turn_rate(0.5, 0.2, 0.2, 0)
        self.assertEqual(controller.choose_turn_rate(0.4, 0.2, 0.2, 0.1), 0)

    def test_trend_initialization_smoothing_and_decay(self):
        controller = Controller()
        controller.choose_turn_rate(0.4, 0, 0, 0)
        self.assertEqual(controller.smoothed_odor_change, 0)
        controller.choose_turn_rate(0.5, 0, 0, 0.1)
        first = controller.smoothed_odor_change
        self.assertGreater(first, 0)
        self.assertLess(first, 1)
        controller.choose_turn_rate(0.5, 0, 0, 0.2)
        self.assertGreater(controller.smoothed_odor_change, 0)
        self.assertLess(controller.smoothed_odor_change, first)

    def test_high_odor_slows_but_does_not_stop_and_search_restores_speed(self):
        controller = Controller(rng=random.Random(0))
        speeds = []
        for index, odor in enumerate([0.65, 0.8, 0.95]):
            controller.choose_turn_rate(odor, 0, 0, index)
            fly = Fly(400, 300)
            fly.move(0, 0.1, controller.speed_scale)
            speeds.append(fly.applied_speed)
            self.assertAlmostEqual(fly.x - 400, fly.applied_speed * 0.1)
        self.assertEqual(speeds[0], 180)
        self.assertTrue(speeds[0] > speeds[1] == speeds[2] > 0)
        self.assertAlmostEqual(speeds[2], 30)
        controller.choose_turn_rate(0, 0, 0, 4)
        self.assertEqual(controller.mode, 'SEARCHING')
        self.assertEqual(controller.speed_scale, 1)
        self.assertEqual(controller.smoothed_odor_change, 0)

    def test_swept_capture_crossing_tangent_miss_and_stationary(self):
        fruit = SimpleNamespace(x=100, y=100, radius=12, capture_radius=22)
        self.assertTrue(movement_touches_fruit((0, 100), (200, 100), 10, fruit))
        self.assertTrue(movement_touches_fruit((0, 122), (200, 122), 10, fruit))
        self.assertFalse(movement_touches_fruit((0, 123), (200, 123), 10, fruit))
        self.assertFalse(movement_touches_fruit((0, 100), (50, 100), 10, fruit))
        self.assertTrue(movement_touches_fruit((100, 100), (100, 100), 10, fruit))
        self.assertFalse(movement_touches_fruit((0, 0), (0, 0), 10, fruit))


if __name__ == '__main__':
    unittest.main()
