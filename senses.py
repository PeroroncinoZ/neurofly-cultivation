"""Sample an odor field at two antennae in the fly's body frame."""

import math
import random

SENSING_RANGE = 350
SENSOR_OFFSET = 15
SENSOR_FORWARD_OFFSET = 10
NOISE_AMOUNT = 0.01


def odor_at(x, y, fruit, sensing_range):
    """A simple odor field that fades linearly to zero at the range limit."""
    distance = math.hypot(fruit.x - x, fruit.y - y)
    return fruit.odor_strength * max(0.0, 1.0 - distance / sensing_range)


def antenna_positions(fly):
    forward_x, forward_y = math.cos(fly.heading), math.sin(fly.heading)
    head_x = fly.x + SENSOR_FORWARD_OFFSET * forward_x
    head_y = fly.y + SENSOR_FORWARD_OFFSET * forward_y
    # Anatomical left is above a fly facing screen-right.
    left_offset_x = SENSOR_OFFSET * forward_y
    left_offset_y = -SENSOR_OFFSET * forward_x
    return ((head_x + left_offset_x, head_y + left_offset_y),
            (head_x - left_offset_x, head_y - left_offset_y))


def sense_fruit(fly, fruit, sensing_range=SENSING_RANGE, noise_amount=NOISE_AMOUNT):
    """Return bilateral samples only; fruit geometry stays in the sensory system."""
    if sensing_range <= 0:
        raise ValueError("sensing_range must be positive")
    if noise_amount < 0:
        raise ValueError("noise_amount must not be negative")

    def read_sensor(position):
        intensity = odor_at(*position, fruit, sensing_range)
        if intensity <= 0:
            return 0.0
        return max(0.0, intensity + random.uniform(-noise_amount, noise_amount))

    left_position, right_position = antenna_positions(fly)
    left, right = read_sensor(left_position), read_sensor(right_position)
    return {"left_odor": left, "right_odor": right,
            "odor_intensity": (left + right) / 2}
