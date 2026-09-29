"""Map DNa02 activity asymmetry to angular velocity, in radians/second."""

STEERING_GAIN = 8.0
MAX_TURN_RATE = 3.0


class MotorDecoder:
    def __init__(self, steering_gain=STEERING_GAIN, max_turn_rate=MAX_TURN_RATE):
        if steering_gain < 0 or max_turn_rate <= 0:
            raise ValueError("gain must be nonnegative and maximum turn rate positive")
        self.steering_gain = steering_gain
        self.max_turn_rate = max_turn_rate
        self.steering_difference = 0.0

    def decode(self, left_activity, right_activity):
        # Screen y increases downward: positive rotation turns right/clockwise.
        self.steering_difference = right_activity - left_activity
        return max(-self.max_turn_rate, min(
            self.max_turn_rate, self.steering_gain * self.steering_difference
        ))
