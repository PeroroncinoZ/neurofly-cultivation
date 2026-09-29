SIGNAL_THRESHOLD = 0.01


def choose_movement(senses):
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
