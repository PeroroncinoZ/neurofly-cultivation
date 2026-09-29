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

    def test_crossed_dna02_output_turns_body_in_expected_direction(self):
        # Facing up: anatomical right is increasing screen x.
        for left, right, expected_sign in [(0.4692, 0.4576, 1),
                                           (0.4576, 0.4692, -1)]:
            with self.subTest(left=left, right=right):
                decoder = MotorDecoder()
                turn = decoder.decode(left, right, 10, odor_intensity=0.5645)
                self.assertAlmostEqual(turn, expected_sign * 1.11)
                fly = Fly(400, 300, heading=-math.pi / 2)
                fly.move(turn, 1 / 60)
                self.assertGreater(expected_sign * (fly.x - 400), 0)
                self.assertLess(fly.y, 300)

    def test_dna02_sign_gain_and_limit(self):
        for difference, expected in [(0.003, 0.25), (-0.003, -0.25),
                                     (0.01, 0.95), (-0.01, -0.95), (1, 3)]:
            decoder = MotorDecoder()
            actual = decoder.decode(difference, 0, 10)
            self.assertAlmostEqual(actual, expected)
            self.assertEqual(decoder.steering_difference, difference)

    def test_neural_turn_smoothing_is_time_based_and_symmetric(self):
        one_step, many_steps = MotorDecoder(), MotorDecoder()
        first = one_step.decode(0.01, 0, 0.15)
        self.assertGreater(first, 0)
        self.assertLess(first, 3)
        for _ in range(15):
            many_steps.decode(0.01, 0, 0.01)
        self.assertAlmostEqual(first, many_steps.turn_rate)
        opposite = MotorDecoder().decode(0, 0.01, 0.15)
        self.assertAlmostEqual(opposite, -first)
        decaying = one_step.decode(0.5, 0.5, 0.15)
        self.assertGreater(decaying, 0)
        self.assertLess(decaying, first)
        self.assertAlmostEqual(one_step.decode(0.5, 0.5, 10), 0)

    def test_single_frame_sign_flip_does_not_reverse_established_turn(self):
        decoder = MotorDecoder()
        self.assertGreater(decoder.decode(0.205, 0.2, 1), 0)
        self.assertGreater(decoder.decode(0.2, 0.205, 1 / 60), 0)
        self.assertLess(decoder.steering_difference, 0)
        self.assertGreater(decoder.smoothed_difference, 0)
        self.assertLess(decoder.decode(0.2, 0.205, 1), 0)

    def test_deadband_rejects_small_sign_changes(self):
        decoder = MotorDecoder()
        for index in range(60):
            self.assertEqual(decoder.decode(0.2, 0.2 + (-1) ** index * 0.0004), 0)
        self.assertGreater(decoder.decode(0.203, 0.2, 1), 0)

    def test_high_odor_reduces_gain_symmetrically(self):
        for left, right in [(0.2, 0.205), (0.205, 0.2)]:
            decoder = MotorDecoder()
            far = decoder.decode(left, right, 10, odor_intensity=0.75)
            self.assertEqual(decoder.applied_gain, 100)
            near = decoder.decode(left, right, 10, odor_intensity=0.95)
            self.assertAlmostEqual(decoder.applied_gain, 35)
            self.assertAlmostEqual(near, far * 0.35)
            self.assertEqual(decoder.steering_difference, left - right)

    def test_detected_odor_immediately_follows_even_with_equal_activity(self):
        controller = Controller(rng=random.Random(0))
        controller.choose_turn_rate(0, 0, 0, 0)
        controller.choose_turn_rate(0, 0, 0, 0.1)
        self.assertNotEqual(controller.turn_rate, 0)
        self.assertEqual(controller.choose_turn_rate(ODOR_THRESHOLD, 0.4, 0.4, 0.2), 0)
        self.assertEqual(controller.mode, 'NEURAL FOLLOWING')
        self.assertEqual(controller.choose_turn_rate(1, 0.4, 0.40001, 0.3), 0)
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
