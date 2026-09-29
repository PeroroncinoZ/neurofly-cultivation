import math
import random


SENSING_RANGE = 350
SENSOR_OFFSET = 15
NOISE_AMOUNT = 0.01


def odor_at(x, y, fruit, sensing_range):
    """A simple odor field that fades linearly to zero at the range limit."""
    distance = math.hypot(fruit.x - x, fruit.y - y)
    return fruit.odor_strength * max(0.0, 1.0 - distance / sensing_range)


def sense_fruit(fly, fruit, sensing_range=SENSING_RANGE, noise_amount=NOISE_AMOUNT):
    """Sample nearby odor without exposing the fruit's position."""
    if sensing_range <= 0:
        raise ValueError("sensing_range must be positive")
    if noise_amount < 0:
        raise ValueError("noise_amount must not be negative")

    distance = math.hypot(fruit.x - fly.x, fruit.y - fly.y)
    if distance >= sensing_range or fruit.odor_strength <= 0:
        return {"odor_intensity": 0.0, "horizontal": 0.0, "vertical": 0.0}

    def read_sensor(x, y):
        intensity = odor_at(x, y, fruit, sensing_range)
        noise = random.uniform(-noise_amount, noise_amount)
        return max(0.0, intensity + noise)

    left = read_sensor(fly.x - SENSOR_OFFSET, fly.y)
    right = read_sensor(fly.x + SENSOR_OFFSET, fly.y)
    above = read_sensor(fly.x, fly.y - SENSOR_OFFSET)
    below = read_sensor(fly.x, fly.y + SENSOR_OFFSET)

    return {
        "odor_intensity": (left + right + above + below) / 4,
        "horizontal": right - left,  # Positive means stronger on the right.
        "vertical": below - above,  # Positive means stronger below.
    }
