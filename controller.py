import random


SIGNAL_THRESHOLD = 0.01
ODOR_THRESHOLD = 0.03
SEARCH_MIN_SECONDS = 0.5
SEARCH_MAX_SECONDS = 1.5
SEARCH_DIRECTIONS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
]


def follow_odor(senses):
    """Follow stronger odor, ignoring very small sensory differences."""
    direction_x = 0
    direction_y = 0

    if senses["horizontal"] > SIGNAL_THRESHOLD:
        direction_x = 1
    elif senses["horizontal"] < -SIGNAL_THRESHOLD:
        direction_x = -1

    if senses["vertical"] > SIGNAL_THRESHOLD:
        direction_y = 1
    elif senses["vertical"] < -SIGNAL_THRESHOLD:
        direction_y = -1

    return direction_x, direction_y


class Controller:
    def __init__(self):
        self.mode = "SEARCHING"
        self.search_direction = (0, 0)
        self.search_until = 0.0

    def choose_movement(self, senses, now):
        """Choose movement using sensory readings and time in seconds."""
        if senses["odor_intensity"] > ODOR_THRESHOLD:
            self.mode = "FOLLOWING ODOR"
            # Start a fresh search if the scent is lost again.
            self.search_until = 0.0
            return follow_odor(senses)

        self.mode = "SEARCHING"
        if now >= self.search_until:
            self.search_direction = random.choice(SEARCH_DIRECTIONS)
            self.search_until = now + random.uniform(
                SEARCH_MIN_SECONDS, SEARCH_MAX_SECONDS
            )

        return self.search_direction
