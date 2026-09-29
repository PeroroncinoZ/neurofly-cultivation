import math

import pygame


class Fly:
    def __init__(self, x, y, heading=0.0, speed=300.0):
        self.x = float(x)
        self.y = float(y)
        self.heading = float(heading) % math.tau
        self.qi = 0
        self.speed = float(speed)  # Pixels/second (formerly 5 pixels/frame at 60 Hz).
        self.applied_speed = self.speed
        self.radius = 10
        self.color = (255, 255, 255)

    def move(self, turn_rate, elapsed_seconds, speed_scale=1.0):
        """Integrate angular velocity, then move forward along the body heading."""
        elapsed_seconds = max(0.0, elapsed_seconds)
        self.heading = (self.heading + turn_rate * elapsed_seconds) % math.tau
        self.applied_speed = self.speed * speed_scale
        self.x += math.cos(self.heading) * self.applied_speed * elapsed_seconds
        self.y += math.sin(self.heading) * self.applied_speed * elapsed_seconds

    def keep_inside(self, width, height):
        hit_x = self.x < self.radius or self.x > width - self.radius
        hit_y = self.y < self.radius or self.y > height - self.radius
        self.x = float(max(self.radius, min(self.x, width - self.radius)))
        self.y = float(max(self.radius, min(self.y, height - self.radius)))
        # Position constraint only: heading is controlled by smooth wall avoidance.
        return hit_x, hit_y

    def draw(self, screen):
        center = (round(self.x), round(self.y))
        pygame.draw.circle(screen, self.color, center, self.radius)
        nose = (round(self.x + self.radius * math.cos(self.heading)),
                round(self.y + self.radius * math.sin(self.heading)))
        pygame.draw.line(screen, (50, 180, 255), center, nose, 3)
