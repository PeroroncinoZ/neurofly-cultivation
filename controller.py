def choose_movement(senses):
    """Return horizontal and vertical directions: -1, 0, or 1."""
    direction_x = 0
    direction_y = 0

    if senses["dx"] > 0:
        direction_x = 1
    elif senses["dx"] < 0:
        direction_x = -1

    if senses["dy"] > 0:
        direction_y = 1
    elif senses["dy"] < 0:
        direction_y = -1

    return direction_x, direction_y
