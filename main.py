import math
import random

import pygame

from brain.brain_interface import BrainInterface
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
    brain = BrainInterface()
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
        brain.update(senses["odor_intensity"])
        brain_debug = brain.get_debug_values()
        now = pygame.time.get_ticks() / 1000.0
        direction_x, direction_y = controller.choose_movement(
            brain_debug["odor_input"], brain_debug["left_output"],
            brain_debug["right_output"], now,
        )
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
        # Sensory gradients are displayed only; movement uses neural outputs.
        debug_lines = [
            f"Qi: {fly.qi}",
            f"Mode: {controller.mode}",
            f"Odor intensity: {senses['odor_intensity']:.3f}",
            f"Right - left: {senses['horizontal']:+.3f}",
            f"Below - above: {senses['vertical']:+.3f}",
            f"Sensing range: {SENSING_RANGE} px",
            "Simplified neural steering:",
            f"Odor input: {brain_debug['odor_input']:.3f}",
            f"ORN_DM1 mean: {brain_debug['orn_dm1_average']:.3f}",
            f"DM1_lPN left: {brain_debug['dm1_lpn_left']:.3f}",
            f"DM1_lPN right: {brain_debug['dm1_lpn_right']:.3f}",
            f"Lateral horn mean: {brain_debug['lateral_horn_average']:.3f}",
            f"Left output: {brain_debug['left_output']:.3f}",
            f"Right output: {brain_debug['right_output']:.3f}",
            f"Steering (R - L): {brain_debug['right_output'] - brain_debug['left_output']:+.4f}",
            f"Movement (x, y): ({direction_x:+.3f}, {direction_y:+.3f})",
        ]
        for index, line in enumerate(debug_lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, 10 + index * 30))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
