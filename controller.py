import random

from brain.motor_decoder import MotorDecoder

ODOR_THRESHOLD = 0.03
SEARCH_MIN_SECONDS = 0.5
SEARCH_MAX_SECONDS = 1.5
SEARCH_DIRECTIONS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
]


class Controller:
    def __init__(self):
        self.mode = "SEARCHING"
        self.search_direction = (0, 0)
        self.search_until = 0.0
        self.motor_decoder = MotorDecoder()
        self.previous_time = None

    def choose_movement(self, odor_input, left_output, right_output, now):
        """Select search or neural steering without receiving fruit direction."""
        elapsed = 1.0 / 60 if self.previous_time is None else now - self.previous_time
        self.previous_time = now
        if odor_input > ODOR_THRESHOLD:
            self.mode = "NEURAL FOLLOWING"
            # Start a fresh search if the scent is lost again.
            self.search_until = 0.0
            return self.motor_decoder.decode(left_output, right_output, elapsed)

        self.mode = "SEARCHING"
        if now >= self.search_until:
            self.search_direction = random.choice(SEARCH_DIRECTIONS)
            self.search_until = now + random.uniform(
                SEARCH_MIN_SECONDS, SEARCH_MAX_SECONDS
            )

        self.motor_decoder.set_search_direction(self.search_direction)
        return self.search_direction
