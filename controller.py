"""Choose angular velocity using odor detection and neural motor activity."""

import math
import random

from brain.motor_decoder import MotorDecoder

ODOR_THRESHOLD = 0.03
SEARCH_MIN_SECONDS = 0.5
SEARCH_MAX_SECONDS = 1.5
SEARCH_MAX_TURN_RATE = 1.5
SEARCH_SMOOTHING_SECONDS = 0.35


class Controller:
    def __init__(self, odor_threshold=ODOR_THRESHOLD, motor_decoder=None, rng=None):
        self.odor_threshold = odor_threshold
        self.motor_decoder = motor_decoder if motor_decoder is not None else MotorDecoder()
        self.rng = rng if rng is not None else random
        self.mode = "SEARCHING"
        self.turn_rate = 0.0
        self.search_target = 0.0
        self.search_until = 0.0
        self.previous_time = None

    def choose_turn_rate(self, odor_input, left_output, right_output, now):
        """Return radians/second; no position or odor gradient enters steering."""
        elapsed = 0.0 if self.previous_time is None else max(0.0, now - self.previous_time)
        self.previous_time = now
        neural_turn = self.motor_decoder.decode(left_output, right_output, elapsed)
        if odor_input >= self.odor_threshold:
            self.mode = "NEURAL FOLLOWING"
            self.search_until = 0.0
            self.turn_rate = neural_turn
            return self.turn_rate

        self.mode = "SEARCHING"
        if now >= self.search_until:
            # Alternate random curvature with straight stretches, never x/y vectors.
            self.search_target = (
                0.0 if self.rng.random() < 0.5 else
                self.rng.uniform(-SEARCH_MAX_TURN_RATE, SEARCH_MAX_TURN_RATE)
            )
            self.search_until = now + self.rng.uniform(SEARCH_MIN_SECONDS, SEARCH_MAX_SECONDS)
        blend = 1.0 - math.exp(-elapsed / SEARCH_SMOOTHING_SECONDS)
        self.turn_rate += blend * (self.search_target - self.turn_rate)
        return self.turn_rate
