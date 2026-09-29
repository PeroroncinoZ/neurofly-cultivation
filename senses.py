import math


def sense_fruit(fly, fruit):
    """Return the fruit's relative position and distance in pixels."""
    dx = fruit.x - fly.x
    dy = fruit.y - fly.y
    distance = math.hypot(dx, dy)

    # Positive dx means right; positive dy means down in Pygame.
    return {"dx": dx, "dy": dy, "distance": distance}
