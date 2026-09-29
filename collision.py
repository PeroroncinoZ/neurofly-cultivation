"""Geometric capture checks, independent of sensing and steering."""


def movement_touches_fruit(start, end, fly_radius, fruit):
    """Swept-circle collision with the fixed fruit, including tangent contact."""
    segment_x, segment_y = end[0] - start[0], end[1] - start[1]
    length_squared = segment_x ** 2 + segment_y ** 2
    fraction = 0.0 if length_squared == 0 else max(0.0, min(1.0,
        ((fruit.x - start[0]) * segment_x + (fruit.y - start[1]) * segment_y)
        / length_squared))
    closest_x = start[0] + fraction * segment_x
    closest_y = start[1] + fraction * segment_y
    return ((fruit.x - closest_x) ** 2 + (fruit.y - closest_y) ** 2
            <= (fly_radius + fruit.radius) ** 2)
