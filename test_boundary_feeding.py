import math
import unittest

from boundary import BoundaryAvoidance
from controller import Controller
from fly import Fly


class BoundaryFeedingTests(unittest.TestCase):
    def test_edges_and_corners_turn_smoothly_and_remain_inside(self):
        for x, y, heading in [(790, 300, 0), (10, 300, math.pi),
                               (400, 10, -math.pi / 2), (400, 590, math.pi / 2),
                               (790, 590, math.pi / 4)]:
            fly = Fly(x, y, heading=heading)
            avoidance = BoundaryAvoidance()
            entered_interior = False
            for _ in range(180):
                old_heading = fly.heading
                turn = avoidance.apply(fly, 800, 600, 0, 1 / 60)
                fly.move(turn, 1 / 60)
                fly.keep_inside(800, 600)
                delta = (fly.heading - old_heading + math.pi) % math.tau - math.pi
                self.assertLessEqual(abs(delta), 3 / 60 + 1e-10)
                self.assertTrue(10 <= fly.x <= 790 and 10 <= fly.y <= 590)
                entered_interior |= 20 < fly.x < 780 and 20 < fly.y < 580
            self.assertTrue(entered_interior)

    def test_no_boundary_influence_in_center(self):
        avoidance = BoundaryAvoidance()
        self.assertEqual(avoidance.apply(Fly(400, 300), 800, 600, -0.4, 0.1), -0.4)
        self.assertFalse(avoidance.active)

    def test_feeding_requires_dwell_then_stops_and_exits_on_odor_loss(self):
        controller = Controller()
        controller.choose_turn_rate(0.94, 0.21, 0.2, 0)
        controller.choose_turn_rate(0.94, 0.21, 0.2, 0.3)
        self.assertEqual(controller.mode, 'ALIGNING')
        controller.choose_turn_rate(0.94, 0.21, 0.2, 0.5)
        self.assertEqual(controller.mode, 'FEEDING')
        self.assertEqual(controller.speed_scale, 0)
        self.assertGreater(controller.turn_rate, 0)
        self.assertLess(controller.turn_rate, 0.2)
        controller.choose_turn_rate(0, 0, 0, 0.6)
        self.assertEqual(controller.mode, 'SEARCHING')
        self.assertEqual(controller.speed_scale, 1)

    def test_feeding_timeout_resumes_approach(self):
        controller = Controller()
        for now in [0, 0.5]:
            controller.choose_turn_rate(0.94, 0, 0, now)
        self.assertEqual(controller.mode, 'FEEDING')
        controller.choose_turn_rate(0.94, 0, 0, 1.6)
        self.assertEqual(controller.mode, 'APPROACHING')
        self.assertGreater(controller.speed_scale, 0)

    def test_rapidly_rising_odor_does_not_trigger_feeding(self):
        controller = Controller()
        for index in range(11):
            controller.choose_turn_rate(0.5 + 0.05 * index, 0, 0, index * 0.1)
        self.assertEqual(controller.mode, 'APPROACHING')
