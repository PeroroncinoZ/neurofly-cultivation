"""Choose angular velocity using odor detection and neural motor activity."""

import math
import random

from brain.motor_decoder import MotorDecoder

ODOR_THRESHOLD = 0.03
SEARCH_MIN_SECONDS = 0.5
SEARCH_MAX_SECONDS = 1.5
SEARCH_MAX_TURN_RATE = 1.5
SEARCH_SMOOTHING_SECONDS = 0.35
ODOR_TREND_SECONDS = 0.3
ODOR_TREND_FULL_SCALE = 0.3  # Odor units/second for full modulation.
INCREASING_TURN_SCALE = 0.4
DECREASING_TURN_SCALE = 2.0
SLOW_ODOR_START = 0.65
SLOW_ODOR_FULL = 0.95
APPROACH_SPEED_SCALE = 0.6
MIN_SPEED_SCALE = 0.1
FEEDING_ODOR_THRESHOLD = 0.90
FEEDING_EXIT_THRESHOLD = 0.85
FEEDING_STABLE_CHANGE = 0.05  # Odor units/second.
FEEDING_CONFIRM_SECONDS = 0.4
FEEDING_DURATION_SECONDS = 1.0
FEEDING_COOLDOWN_SECONDS = 1.0
FEEDING_SPEED_SCALE = 0.0
FEEDING_TURN_SCALE = 0.15


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
        self.high_stable_since = None
        self.feeding_until = None
        self.feeding_cooldown_until = 0.0
        self.previous_odor = None
        self.total_odor = 0.0
        self.smoothed_odor_change = 0.0
        self.speed_scale = 1.0

    def choose_turn_rate(self, odor_input, left_output, right_output, now):
        """Return radians/second; no position or odor gradient enters steering."""
        elapsed = 0.0 if self.previous_time is None else max(0.0, now - self.previous_time)
        self.previous_time = now
        self.total_odor = odor_input
        if self.previous_odor is not None and elapsed > 0:
            change = (odor_input - self.previous_odor) / elapsed
            blend = -math.expm1(-elapsed / ODOR_TREND_SECONDS)
            self.smoothed_odor_change += blend * (change - self.smoothed_odor_change)
        self.previous_odor = odor_input
        stable_high = (odor_input >= FEEDING_ODOR_THRESHOLD
                       and abs(self.smoothed_odor_change) <= FEEDING_STABLE_CHANGE)
        if self.feeding_until is not None:
            if odor_input < FEEDING_EXIT_THRESHOLD or now >= self.feeding_until:
                self.feeding_until = None
                self.high_stable_since = None
                self.feeding_cooldown_until = now + FEEDING_COOLDOWN_SECONDS
        if self.feeding_until is None:
            if stable_high and now >= self.feeding_cooldown_until:
                if self.high_stable_since is None:
                    self.high_stable_since = now
                if now - self.high_stable_since >= FEEDING_CONFIRM_SECONDS:
                    self.feeding_until = now + FEEDING_DURATION_SECONDS
            else:
                self.high_stable_since = None
        turn_scale = 1.0
        self.speed_scale = 1.0
        if odor_input >= self.odor_threshold:
            trend = max(-1.0, min(1.0,
                self.smoothed_odor_change / ODOR_TREND_FULL_SCALE))
            if trend >= 0:
                turn_scale = 1.0 + trend * (INCREASING_TURN_SCALE - 1.0)
            else:
                turn_scale = 1.0 - trend * (DECREASING_TURN_SCALE - 1.0)
            strength = max(0.0, min(1.0,
                (odor_input - SLOW_ODOR_START) / (SLOW_ODOR_FULL - SLOW_ODOR_START)))
            strength = strength * strength * (3.0 - 2.0 * strength)
            self.speed_scale = APPROACH_SPEED_SCALE - strength * (APPROACH_SPEED_SCALE - MIN_SPEED_SCALE)
        else:
            # Do not carry an old trend through a scent-free search interval.
            self.smoothed_odor_change = 0.0
        if self.feeding_until is not None:
            self.speed_scale = FEEDING_SPEED_SCALE
            turn_scale *= FEEDING_TURN_SCALE
        neural_turn = self.motor_decoder.decode(
            left_output, right_output, elapsed, odor_intensity=odor_input, gain_scale=turn_scale
        )
        if odor_input >= self.odor_threshold:
            self.mode = "FEEDING" if self.feeding_until is not None else "NEURAL FOLLOWING"
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
