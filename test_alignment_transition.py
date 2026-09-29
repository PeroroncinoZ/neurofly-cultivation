import unittest
from controller import Controller


class AlignmentTransitionTests(unittest.TestCase):
    def test_runtime_reproduction(self):
        controller = Controller()
        controller.mode = 'NEURAL_FOLLOWING'
        controller.motor_decoder.smoothed_difference = -0.00699
        controller.choose_turn_rate(0.712, 0.2, 0.20699, 0)
        self.assertAlmostEqual(controller.motor_decoder.smoothed_difference, -0.00699)
        self.assertEqual(controller.mode, 'ALIGNING')
        self.assertLessEqual(300 * controller.speed_scale, 15)
        self.assertLess(controller.turn_rate, 0)

    def test_alignment_requires_continuous_low_imbalance(self):
        controller = Controller()
        def step(now, difference, odor=0.712):
            # Seed the decoder filter to isolate state-transition timing.
            controller.motor_decoder.smoothed_difference = difference
            controller.choose_turn_rate(odor, 0.2 + difference, 0.2, now)
        step(0, 0.007)
        step(0.1, 0.001)
        step(0.2, 0.001)
        self.assertEqual(controller.mode, 'ALIGNING')
        step(0.3, 0.007)  # A renewed imbalance resets the confirmation timer.
        step(0.4, 0.001)
        step(0.6, 0.001)
        self.assertEqual(controller.mode, 'ALIGNING')
        step(0.7, 0.001)
        self.assertEqual(controller.mode, 'APPROACHING')
        step(0.8, 0.007)
        self.assertEqual(controller.mode, 'ALIGNING')

    def test_detectable_odor_retains_alignment_until_loss(self):
        controller = Controller()
        controller.motor_decoder.smoothed_difference = 0.007
        controller.choose_turn_rate(0.712, 0.207, 0.2, 0)
        controller.choose_turn_rate(0.69, 0.207, 0.2, 0.1)
        self.assertEqual(controller.mode, 'ALIGNING')
        controller.choose_turn_rate(0.64, 0.207, 0.2, 0.2)
        self.assertEqual(controller.mode, 'ALIGNING')
        controller.choose_turn_rate(0.69, 0.207, 0.2, 0.3)
        self.assertEqual(controller.mode, 'ALIGNING')
        controller.choose_turn_rate(0, 0.207, 0.2, 0.4)
        self.assertEqual(controller.mode, 'SEARCHING')
        self.assertIsNone(controller.aligned_since)

    def test_low_detectable_odor_can_trigger_alignment_with_hysteresis(self):
        controller = Controller()
        def step(now, difference):
            controller.motor_decoder.smoothed_difference = difference
            controller.choose_turn_rate(0.4, 0.2 + difference, 0.2, now)
        step(0, 0.007)
        self.assertEqual(controller.mode, 'ALIGNING')
        self.assertEqual(controller.speed_scale, 0)
        step(0.1, 0.0025)
        step(1, 0.0025)
        self.assertEqual(controller.mode, 'ALIGNING')
        step(1.1, 0.001)
        step(1.4, 0.001)
        self.assertEqual(controller.mode, 'APPROACHING')
        step(1.5, 0.0025)
        self.assertEqual(controller.mode, 'APPROACHING')
