"""Regression tests for turn-then-advance, replacing orbit/localizing control."""
import unittest

from controller import Controller
from fly import Fly


class AlignmentTests(unittest.TestCase):
    def test_turn_in_place_then_advance_for_both_neural_signs(self):
        for left, right in [(0.21, 0.2), (0.2, 0.21)]:
            controller = Controller()
            controller.choose_turn_rate(0.8, left, right, 0)
            turn = controller.choose_turn_rate(0.8, left, right, 1)
            self.assertEqual(controller.mode, 'ALIGNING')
            self.assertEqual(controller.speed_scale, 0)
            self.assertGreater(turn * (left - right), 0)
            self.assertEqual(controller.motor_decoder.applied_gain, 100)
            fly = Fly(400, 300)
            fly.move(turn, 0.1, controller.speed_scale)
            self.assertEqual((fly.x, fly.y), (400, 300))
            self.assertNotEqual(fly.heading, 0)
            controller.choose_turn_rate(0.8, 0.2, 0.2, 2)
            controller.choose_turn_rate(0.8, 0.2, 0.2, 2.3)
            self.assertEqual(controller.mode, 'APPROACHING')
            fly.move(controller.turn_rate, 0.1, controller.speed_scale)
            self.assertAlmostEqual(fly.applied_speed, 30)

    def test_odor_loss_restores_search(self):
        controller = Controller()
        controller.choose_turn_rate(0.8, 0.21, 0.2, 0)
        controller.choose_turn_rate(0.8, 0.21, 0.2, 1)
        controller.choose_turn_rate(0, 0.21, 0.2, 2)
        self.assertEqual(controller.mode, 'SEARCHING')
        self.assertEqual(controller.speed_scale, 1)

    def test_high_increasing_odor_does_not_attenuate_steering(self):
        controller = Controller()
        controller.choose_turn_rate(0.8, 0.21, 0.2, 0)
        controller.choose_turn_rate(0.9, 0.21, 0.2, 0.1)
        self.assertEqual(controller.mode, 'ALIGNING')
        self.assertEqual(controller.motor_decoder.applied_gain, 100)

    def test_equal_neural_activity_advances_without_inventing_turn(self):
        controller = Controller()
        for step in range(30):
            self.assertEqual(controller.choose_turn_rate(0.8, 0.2, 0.2, step / 10), 0)
            self.assertEqual(controller.mode, 'APPROACHING')
