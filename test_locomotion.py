"""Regression tests for heading locomotion and the bilateral neural boundary."""
import math
import random
import unittest
from types import SimpleNamespace

from brain.brain_interface import BrainInterface
from brain.motor_decoder import MotorDecoder
from controller import Controller, ODOR_THRESHOLD
from fly import Fly
from senses import antenna_positions, sense_fruit


class LocomotionTests(unittest.TestCase):
    def test_forward_motion_and_turn(self):
        fly = Fly(100, 100, heading=math.pi / 2, speed=12.5)
        fly.move(0, 0.2)
        self.assertAlmostEqual(fly.x, 100)
        self.assertAlmostEqual(fly.y, 102.5)
        fly.move(-math.pi, 0.5)
        self.assertAlmostEqual(fly.heading, 0)
        self.assertAlmostEqual(fly.x, 106.25)
        self.assertIsInstance(fly.x, float)

    def test_wall_reflects_heading_and_clamps_body(self):
        fly = Fly(789, 300, speed=100)
        fly.move(0, 0.1)
        self.assertEqual(fly.keep_inside(800, 600), (True, False))
        self.assertEqual(fly.x, 790.0)
        self.assertAlmostEqual(fly.heading, math.pi)
        fly.move(0, 0.1)
        self.assertLess(fly.x, 790)

    def test_dna02_sign_gain_and_limit(self):
        decoder = MotorDecoder()
        self.assertAlmostEqual(decoder.decode(0.2, 0.3), 0.8)
        self.assertAlmostEqual(decoder.decode(0.3, 0.2), -0.8)
        self.assertEqual(decoder.decode(0, 1), 3)
        self.assertEqual(decoder.decode(1, 0), -3)

    def test_detected_odor_immediately_follows_even_with_equal_activity(self):
        controller = Controller(rng=random.Random(0))
        controller.choose_turn_rate(0, 0, 0, 0)
        controller.choose_turn_rate(0, 0, 0, 0.1)
        self.assertNotEqual(controller.turn_rate, 0)
        self.assertEqual(controller.choose_turn_rate(ODOR_THRESHOLD, 0.4, 0.4, 0.2), 0)
        self.assertEqual(controller.mode, 'NEURAL FOLLOWING')
        self.assertAlmostEqual(controller.choose_turn_rate(1, 0.4, 0.40001, 0.3), 0.00008)
        controller.choose_turn_rate(0, 0.4, 0.4, 0.4)
        self.assertEqual(controller.mode, 'SEARCHING')

    def test_search_turns_are_smooth_and_forward_speed_is_preserved(self):
        controller = Controller(rng=random.Random(0))
        fly = Fly(400, 300, speed=10)
        controller.choose_turn_rate(0, 0, 0, 0)
        turn = controller.choose_turn_rate(0, 0, 0, 0.01)
        self.assertGreater(turn, 0)
        self.assertLess(turn, controller.search_target)
        fly.move(turn, 0.01)
        self.assertAlmostEqual(math.hypot(fly.x - 400, fly.y - 300), 0.1)

    def test_antennae_rotate_and_sample_anatomical_sides(self):
        fly = Fly(100, 100)
        self.assertEqual(antenna_positions(fly), ((110, 85), (110, 115)))
        fruit = SimpleNamespace(x=110, y=85, odor_strength=1)
        samples = sense_fruit(fly, fruit, noise_amount=0)
        self.assertGreater(samples['left_odor'], samples['right_odor'])
        fly.heading = math.pi / 2
        left, right = antenna_positions(fly)
        for actual, expected in zip(left + right, (115, 110, 85, 110)):
            self.assertAlmostEqual(actual, expected)

    def test_real_pair_and_bilateral_input_isolation(self):
        brain = BrainInterface()
        brain.update(0.8, 0.2)
        for side, expected in [('left', 0.8), ('right', 0.2)]:
            for root_id in brain.input_ids_by_side[side]:
                self.assertEqual(brain.state['external_inputs'][root_id], expected)
        brain.state['activations'][720575940629327659] = 0.25
        brain.state['activations'][720575940604737708] = 0.75
        debug = brain.get_debug_values()
        self.assertEqual(debug['dna02_left'], 0.25)
        self.assertEqual(debug['dna02_right'], 0.75)
        self.assertEqual(debug['dna02_difference'], 0.5)
        brain.update(0, 0)
        self.assertTrue(all(value == 0 for value in brain.state['external_inputs'].values()))


if __name__ == '__main__':
    unittest.main()
