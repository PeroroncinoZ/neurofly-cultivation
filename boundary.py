"""Deterministic wall avoidance; uses geometry and scalar sensory state, never fruit position."""
import math
import logging

logger = logging.getLogger(__name__)
BOUNDARY_ODOR_THRESHOLD = 0.03
BOUNDARY_SLOW_DISTANCE = 30.0

BOUNDARY_MARGIN = 100.0
BOUNDARY_TURN_GAIN = 3.0
MAX_TURN_RATE = 3.0
TURN_SMOOTHING_SECONDS = 0.12
HIGH_ODOR_START = 0.75
HIGH_ODOR_FULL = 0.95
SLOW_SPEED_THRESHOLD = 120.0
NEAR_SOURCE_MIN_STRENGTH = 0.1
INWARD_HEADING_CLEARANCE = 0.25  # Finish turning slightly inward past wall-parallel.


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
        self.releasing = False
        self.speed_scale = 1.0
        self.turn_modifications = 0
        self.turn_sign_changes = 0

    def apply(self, fly, width, height, requested_turn, elapsed, total_odor=0.0, forward_speed=None):
        self.speed_scale = 1.0
        speed = fly.applied_speed if forward_speed is None else forward_speed
        if total_odor >= BOUNDARY_ODOR_THRESHOLD:
            # Rotation in place is always safe for the circular body. Preserve
            # neural sign (including zero); brake translation instead of steering.
            heading = fly.heading + requested_turn * max(0.0, elapsed)
            direction_x, direction_y = math.cos(heading), math.sin(heading)
            clearances = []
            for position, direction, limit in ((fly.x, direction_x, width),
                                                (fly.y, direction_y, height)):
                if abs(direction) > 1e-12:
                    clearance = (limit - fly.radius - position if direction > 0
                                 else position - fly.radius)
                    clearances.append(max(0.0, clearance) / abs(direction))
            distance = min(clearances, default=float('inf'))
            braking = max(0.0, min(1.0, distance / BOUNDARY_SLOW_DISTANCE))
            safe_step = 1.0 if speed * elapsed <= 0 else min(1.0, distance / (speed * elapsed))
            self.speed_scale = min(braking, safe_step)
            self.active = self.speed_scale < 1.0
            self.releasing = False
            self.turn_rate = requested_turn
            return self.turn_rate

        def pressure(distance):
            value = max(0.0, min(1.0, 1 - distance / self.margin))
            return value * value * (3 - 2 * value)

        # Only walls the fly is moving toward need to change its heading.
        forward_x, forward_y = math.cos(fly.heading), math.sin(fly.heading)
        left = pressure(fly.x - fly.radius) * max(0.0, min(1.0, (-forward_x + INWARD_HEADING_CLEARANCE) / INWARD_HEADING_CLEARANCE))
        right = pressure(width - fly.radius - fly.x) * max(0.0, min(1.0, (forward_x + INWARD_HEADING_CLEARANCE) / INWARD_HEADING_CLEARANCE))
        top = pressure(fly.y - fly.radius) * max(0.0, min(1.0, (-forward_y + INWARD_HEADING_CLEARANCE) / INWARD_HEADING_CLEARANCE))
        bottom = pressure(height - fly.radius - fly.y) * max(0.0, min(1.0, (forward_y + INWARD_HEADING_CLEARANCE) / INWARD_HEADING_CLEARANCE))
        strength = max(left, right, top, bottom)
        speed = fly.applied_speed if forward_speed is None else forward_speed
        high_odor = max(0.0, min(1.0,
            (total_odor - HIGH_ODOR_START) / (HIGH_ODOR_FULL - HIGH_ODOR_START)))
        slow = max(0.0, min(1.0, 1 - speed / SLOW_SPEED_THRESHOLD))
        strength *= 1 - high_odor * slow * (1 - NEAR_SOURCE_MIN_STRENGTH)
        # Position clamping remains the hard safety constraint, even at rest.
        self.active = strength > 1e-9
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
        if self.active or self.releasing:
            blend = -math.expm1(-max(0.0, elapsed) / self.smoothing_seconds)
            self.turn_rate += blend * (target - self.turn_rate)
        else:
            self.turn_rate = requested_turn
        self.releasing = self.active or abs(self.turn_rate - requested_turn) > 1e-4
        self.turn_rate = max(-self.max_turn_rate, min(self.max_turn_rate, self.turn_rate))
        if not math.isclose(self.turn_rate, requested_turn, abs_tol=1e-12):
            self.turn_modifications += 1
            self.turn_sign_changes += self.turn_rate * requested_turn < 0
            logger.info("Boundary turn modification: requested=%+.6f applied=%+.6f odor=%.4f",
                        requested_turn, self.turn_rate, total_odor)
        return self.turn_rate
