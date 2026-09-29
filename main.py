import math
import random

import pygame

from fly import Fly
from spiritual_fruit import SpiritualFruit


def circles_touch(first, second):
    distance = math.hypot(first.x - second.x, first.y - second.y)
    return distance <= first.radius + second.radius


def spawn_fruit(width, height):
    fruit = SpiritualFruit(0, 0)
    # Keep the whole fruit inside the window.
    fruit.x = random.randint(fruit.radius, width - fruit.radius)
    fruit.y = random.randint(fruit.radius, height - fruit.radius)
    return fruit


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("NeuroFly: Cultivation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    fly = Fly(400, 300)
    fruit = SpiritualFruit(600, 200)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not running:
            break

        keys = pygame.key.get_pressed()
        fly.move(keys)

        if circles_touch(fly, fruit):
            fly.qi += 1
            # Replacing the old fruit removes it from the world.
            fruit = spawn_fruit(screen.get_width(), screen.get_height())

        # Clear the previous frame before drawing the fruit and fly again.
        screen.fill((30, 30, 30))
        fruit.draw(screen)
        fly.draw(screen)
        qi_text = font.render(f"Qi: {fly.qi}", True, (255, 255, 255))
        screen.blit(qi_text, (10, 10))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
