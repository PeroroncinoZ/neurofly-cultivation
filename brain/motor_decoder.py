"""Map DNa02 activity asymmetry to angular velocity, in radians/second."""

import math

# Base gain before deadband and optional temporal/state modulation.
STEERING_GAIN = 100.0
MAX_TURN_RATE = 3.0
SMOOTHING_SECONDS = 0.15
STEERING_DEADBAND = 0.0005



class MotorDecoder:
    def __init__(self, steering_gain=STEERING_GAIN, max_turn_rate=MAX_TURN_RATE,
                 smoothing_seconds=SMOOTHING_SECONDS,
                 deadband=STEERING_DEADBAND):
        if steering_gain < 0 or max_turn_rate <= 0:
            raise ValueError("gain must be nonnegative and maximum turn rate positive")
        if not math.isfinite(smoothing_seconds) or smoothing_seconds <= 0:
            raise ValueError("smoothing_seconds must be finite and positive")
        if not math.isfinite(deadband) or deadband < 0:
            raise ValueError("deadband must be finite and nonnegative")
        self.deadband = deadband
        self.smoothed_difference = 0.0
        self.applied_gain = steering_gain
        self.smoothing_seconds = smoothing_seconds
        self.turn_rate = 0.0
        self.steering_gain = steering_gain
        self.max_turn_rate = max_turn_rate
        self.steering_difference = 0.0

    def decode(self, left_activity, right_activity, elapsed_seconds=1 / 60,
               odor_intensity=0.0, gain_scale=1.0):
        """Filter L-R, apply a symmetric soft deadband, scale and clamp.

        Odor intensity is accepted for compatibility but does not attenuate gain. All filtering state belongs to the motor mapping.
        """
        if not math.isfinite(gain_scale) or gain_scale < 0:
            raise ValueError("gain_scale must be finite and nonnegative")
        # Exported pathways cross: right DM1 drives left DNa02 and vice versa.
        # Interpret stronger left DNa02 as a positive (rightward) body turn.
        self.steering_difference = left_activity - right_activity
        blend = -math.expm1(-max(0.0, elapsed_seconds) / self.smoothing_seconds)
        self.smoothed_difference += blend * (
            self.steering_difference - self.smoothed_difference
        )
        # Subtract the deadband width outside it for a continuous response.
        effective_difference = math.copysign(
            max(0.0, abs(self.smoothed_difference) - self.deadband),
            self.smoothed_difference,
        )
        self.applied_gain = self.steering_gain * gain_scale
        # Screen y increases downward: positive rotation turns right/clockwise.
        self.turn_rate = max(-self.max_turn_rate, min(
            self.max_turn_rate, self.applied_gain * effective_difference
        ))
        return self.turn_rate
