import math

import pygame

CAPTURE_RADIUS = 35.0
SPAWN_BUFFER = 10.0
SPAWN_MARGIN = CAPTURE_RADIUS + SPAWN_BUFFER


class SpiritualFruit:
    def __init__(self, x, y, odor_strength=1.0, capture_radius=CAPTURE_RADIUS):
        if not math.isfinite(capture_radius) or capture_radius <= 0:
            raise ValueError("capture_radius must be finite and positive")
        self.capture_radius = float(capture_radius)
        self.x = x
        self.y = y
        self.odor_strength = odor_strength
        self.radius = 12
        self.color = (180, 80, 255)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
