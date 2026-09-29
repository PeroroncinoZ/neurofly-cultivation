"""Deterministic wall avoidance; receives body geometry, never odor or fruit."""
import math

BOUNDARY_MARGIN = 100.0
BOUNDARY_TURN_GAIN = 3.0
MAX_TURN_RATE = 3.0
TURN_SMOOTHING_SECONDS = 0.12


class BoundaryAvoidance:
    def __init__(self, margin=BOUNDARY_MARGIN, turn_gain=BOUNDARY_TURN_GAIN,
                 max_turn_rate=MAX_TURN_RATE, smoothing_seconds=TURN_SMOOTHING_SECONDS):
        if min(margin, turn_gain, max_turn_rate, smoothing_seconds) <= 0:
            raise ValueError("boundary parameters must be positive")
        self.margin = margin
        self.turn_gain = turn_gain
        self.max_turn_rate = max_turn_rate
        self.smoothing_seconds = smoothing_seconds
        self.turn_rate = 0.0
        self.active = False

    def apply(self, fly, width, height, requested_turn, elapsed):
        def pressure(distance):
            value = max(0.0, min(1.0, 1 - distance / self.margin))
            return value * value * (3 - 2 * value)

        left = pressure(fly.x - fly.radius)
        right = pressure(width - fly.radius - fly.x)
        top = pressure(fly.y - fly.radius)
        bottom = pressure(height - fly.radius - fly.y)
        strength = max(left, right, top, bottom)
        self.active = strength > 0
        inward_x, inward_y = left - right, top - bottom
        target = requested_turn
        if inward_x or inward_y:
            desired = math.atan2(inward_y, inward_x)
            error = (desired - fly.heading + math.pi) % math.tau - math.pi
            # Exact head-on encounters always choose the same rotation.
            if abs(abs(error) - math.pi) < 1e-9:
                error = math.pi
            wall_turn = max(-self.max_turn_rate, min(self.max_turn_rate,
                                                    self.turn_gain * error))
            target = (1 - strength) * requested_turn + strength * wall_turn
        if self.active:
            blend = -math.expm1(-max(0.0, elapsed) / self.smoothing_seconds)
            self.turn_rate += blend * (target - self.turn_rate)
        else:
            self.turn_rate = requested_turn
        self.turn_rate = max(-self.max_turn_rate, min(self.max_turn_rate, self.turn_rate))
        return self.turn_rate
