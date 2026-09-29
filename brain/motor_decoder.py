"""Map DNa02 activity asymmetry to angular velocity, in radians/second."""

import math

# A difference of 0.003–0.01 requests 0.9–3.0 rad/s.
STEERING_GAIN = 300.0
MAX_TURN_RATE = 3.0
SMOOTHING_SECONDS = 0.15


class MotorDecoder:
    def __init__(self, steering_gain=STEERING_GAIN, max_turn_rate=MAX_TURN_RATE,
                 smoothing_seconds=SMOOTHING_SECONDS):
        if steering_gain < 0 or max_turn_rate <= 0:
            raise ValueError("gain must be nonnegative and maximum turn rate positive")
        if not math.isfinite(smoothing_seconds) or smoothing_seconds <= 0:
            raise ValueError("smoothing_seconds must be finite and positive")
        self.smoothing_seconds = smoothing_seconds
        self.turn_rate = 0.0
        self.steering_gain = steering_gain
        self.max_turn_rate = max_turn_rate
        self.steering_difference = 0.0

    def decode(self, left_activity, right_activity, elapsed_seconds=1 / 60):
        # Screen y increases downward: positive rotation turns right/clockwise.
        self.steering_difference = right_activity - left_activity
        target = max(-self.max_turn_rate, min(
            self.max_turn_rate, self.steering_gain * self.steering_difference
        ))
        # Exponential smoothing is independent of frame rate. It filters only
        # angular velocity; raw neural activity and its difference are untouched.
        blend = -math.expm1(-max(0.0, elapsed_seconds) / self.smoothing_seconds)
        self.turn_rate += blend * (target - self.turn_rate)
        self.turn_rate = max(-self.max_turn_rate, min(self.max_turn_rate, self.turn_rate))
        return self.turn_rate
