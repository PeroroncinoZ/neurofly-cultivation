"""Simplified motor decoder reading connectome-derived neural activity.

This is a game movement mapping, not a biologically complete motor circuit.
LH activity sets a horizontal bias; vertical motion retains the last search
direction (initially upward). No fruit position or sensory gradient is used.
"""

import math


STEERING_GAIN = 8.0
SMOOTHING_SECONDS = 0.25


class MotorDecoder:
    def __init__(self):
        self.direction_x = 0.0
        self.direction_y = -1.0
        self.steering_difference = 0.0

    def set_search_direction(self, direction):
        """Carry the most recent search movement into neural following."""
        self.direction_x, self.direction_y = direction

    def decode(self, left_activity, right_activity, elapsed_seconds):
        self.steering_difference = right_activity - left_activity
        target_x = max(-1.0, min(1.0, STEERING_GAIN * self.steering_difference))
        # Smooth velocity instead of choosing a new left/right sign each frame.
        blend = 1.0 - math.exp(-max(0.0, elapsed_seconds) / SMOOTHING_SECONDS)
        self.direction_x += blend * (target_x - self.direction_x)
        return self.direction_x, self.direction_y
