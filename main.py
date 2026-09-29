import math
import random

import pygame

from fly import Fly
from senses import sense_fruit
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

        # Sense after collection so the values describe the current fruit.
        senses = sense_fruit(fly, fruit)

        # Clear the previous frame before drawing the fruit and fly again.
        screen.fill((30, 30, 30))
        fruit.draw(screen)
        fly.draw(screen)
        debug_lines = [
            f"Qi: {fly.qi}",
            f"Fruit dx: {senses['dx']:.1f} px",
            f"Fruit dy: {senses['dy']:.1f} px",
            f"Fruit distance: {senses['distance']:.1f} px",
        ]
        for index, line in enumerate(debug_lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, 10 + index * 30))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
