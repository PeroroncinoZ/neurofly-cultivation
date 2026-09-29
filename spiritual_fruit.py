import pygame


class SpiritualFruit:
    def __init__(self, x, y, odor_strength=1.0):
        self.x = x
        self.y = y
        self.odor_strength = odor_strength
        self.radius = 12
        self.color = (180, 80, 255)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
