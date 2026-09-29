import pygame


class Fly:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.qi = 0
        self.speed = 5
        self.radius = 10
        self.color = (255, 255, 255)

    def move(self, direction_x, direction_y):
        # The controller chooses directions; the body applies its speed.
        self.x += direction_x * self.speed
        self.y += direction_y * self.speed

    def keep_inside(self, width, height):
        # Leave enough room for the entire circle at each edge.
        self.x = max(self.radius, min(self.x, width - self.radius))
        self.y = max(self.radius, min(self.y, height - self.radius))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
