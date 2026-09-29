import math
import random

import pygame

from controller import Controller
from fly import Fly
from senses import SENSING_RANGE, sense_fruit
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
    controller = Controller()
    fruit = SpiritualFruit(600, 200)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not running:
            break

        senses = sense_fruit(fly, fruit)
        now = pygame.time.get_ticks() / 1000.0
        direction_x, direction_y = controller.choose_movement(senses, now)
        fly.move(direction_x, direction_y)
        fly.keep_inside(screen.get_width(), screen.get_height())

        if circles_touch(fly, fruit):
            fly.qi += 1
            # Replacing the old fruit removes it from the world.
            fruit = spawn_fruit(screen.get_width(), screen.get_height())

        # Clear the previous frame before drawing the fruit and fly again.
        screen.fill((30, 30, 30))
        fruit.draw(screen)
        fly.draw(screen)
        # Show the same noisy readings the controller used this frame.
        debug_lines = [
            f"Qi: {fly.qi}",
            f"Mode: {controller.mode}",
            f"Odor intensity: {senses['odor_intensity']:.3f}",
            f"Right - left: {senses['horizontal']:+.3f}",
            f"Below - above: {senses['vertical']:+.3f}",
            f"Sensing range: {SENSING_RANGE} px",
        ]
        for index, line in enumerate(debug_lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, 10 + index * 30))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
